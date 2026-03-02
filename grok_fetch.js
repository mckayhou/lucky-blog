const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  });
  
  const page = await browser.newPage();
  await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
  
  try {
    await page.goto('https://grok.com/share/bGVnYWN5LWNvcHk_4786b929-c68b-40b4-b4fc-fbb4e9e8dcc7?rid=d303ffb1-763a-4172-a175-af6ae2ab392d', {
      waitUntil: 'networkidle2',
      timeout: 30000
    });
    
    // 等待内容加载
    await page.waitForSelector('body', { timeout: 10000 });
    
    // 获取页面内容
    const content = await page.content();
    const text = await page.evaluate(() => document.body.innerText);
    
    console.log('=== 页面标题 ===');
    const title = await page.title();
    console.log(title);
    
    console.log('\n=== 页面文本内容 ===');
    console.log(text.substring(0, 10000));
    
  } catch (error) {
    console.error('访问失败:', error.message);
    
    // 截图调试
    await page.screenshot({ path: '/root/.openclaw/workspace/grok_error.png', fullPage: true });
    console.log('错误截图已保存：/root/.openclaw/workspace/grok_error.png');
  }
  
  await browser.close();
})();
