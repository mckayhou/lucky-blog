#!/usr/bin/env node
/**
 * 中东战争专用搜索脚本
 * 调用 Tavily API + 定向抓取核心网站
 */

const { execSync } = require('child_process');
const path = require('path');

// 解析参数
const args = process.argv.slice(2);
let params = {};

try {
  params = JSON.parse(args[0] || '{}');
} catch (e) {
  console.error('用法：node war-search.mjs \'{"query": "...", "hours": 2, "depth": "advanced"}\'');
  process.exit(1);
}

const {
  query = 'Middle East war latest',
  hours = 2,
  depth = 'advanced',
  sources = ['tavily', 'isw', 'liveuamap']
} = params;

console.log(`🔍 开始中东战争搜索 - ${new Date().toISOString()}`);
console.log(`   关键词：${query}`);
console.log(`   时间范围：过去${hours}小时`);
console.log(`   搜索深度：${depth}`);
console.log(`   来源：${sources.join(', ')}`);
console.log('');

const results = [];

// 1. Tavily 搜索
if (sources.includes('tavily')) {
  console.log('📡 Tavily 搜索中...');
  try {
    const tavilyScript = path.join(__dirname, '../tavily-search/scripts/search.mjs');
    const topicFlag = '--topic news';
    const deepFlag = depth === 'advanced' ? '--deep' : '';
    const daysFlag = `--days ${Math.ceil(hours / 24)}`;
    
    const cmd = `node "${tavilyScript}" "${query}" ${topicFlag} ${deepFlag} ${daysFlag}`;
    const output = execSync(cmd, { encoding: 'utf-8', timeout: 30000 });
    
    // 解析输出（假设是 JSON 或格式化文本）
    try {
      const parsed = JSON.parse(output);
      results.push(...parsed.results || parsed);
    } catch {
      // 非 JSON 输出，按行解析
      const lines = output.split('\n').filter(l => l.trim());
      lines.forEach((line, i) => {
        results.push({
          title: line.split('|')[0]?.trim() || line,
          url: line.match(/https?:\/\/[^\s]+/)?.[0] || '',
          snippet: line,
          source: 'Tavily'
        });
      });
    }
    console.log(`   ✓ 找到 ${results.length} 条结果`);
  } catch (e) {
    console.error(`   ✗ Tavily 搜索失败：${e.message}`);
  }
}

// 2. 定向抓取核心网站
const coreSites = [
  { name: 'ISW', url: 'https://www.understandingwar.org/' },
  { name: 'LiveUAMap', url: 'https://liveuamap.com/' },
  { name: 'Reuters ME', url: 'https://www.reuters.com/world/middle-east/' },
  { name: 'BBC ME', url: 'https://www.bbc.com/news/world/middle_east' },
  { name: 'Al Jazeera', url: 'https://www.aljazeera.com/where/middleeast/' },
];

if (sources.includes('isw') || sources.includes('liveuamap')) {
  coreSites.forEach(site => {
    if (sources.some(s => site.name.toLowerCase().includes(s))) {
      console.log(`📄 抓取 ${site.name}...`);
      try {
        const extractScript = path.join(__dirname, '../tavily-search/scripts/extract.mjs');
        const cmd = `node "${extractScript}" "${site.url}"`;
        const output = execSync(cmd, { encoding: 'utf-8', timeout: 15000 });
        
        results.push({
          title: `${site.name} 最新报道`,
          url: site.url,
          snippet: output.slice(0, 500),
          source: site.name
        });
        console.log(`   ✓ 成功`);
      } catch (e) {
        console.error(`   ✗ 抓取失败：${e.message}`);
      }
    }
  });
}

// 输出去重结果
console.log('');
console.log(`📊 搜索结果汇总：${results.length} 条`);
console.log(JSON.stringify({ results, count: results.length, timestamp: new Date().toISOString() }, null, 2));
