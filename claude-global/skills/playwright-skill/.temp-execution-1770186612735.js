
const { launchWithUserProfile } = require("./lib/helpers");

(async () => {
  const { browser, page, close } = await launchWithUserProfile();
  
  try {
    await page.goto("https://creator.xiaohongshu.com/new/note-manager", { 
      waitUntil: "domcontentloaded",
      timeout: 60000 
    });
    await page.waitForTimeout(2000);
    
    // 滚动获取更多内容
    for (let i = 0; i < 10; i++) {
      await page.evaluate(() => window.scrollBy(0, 1000));
      await page.waitForTimeout(800);
    }
    
    // 获取完整的页面内容
    const pageText = await page.evaluate(() => {
      return document.body.innerText;
    });
    
    console.log(pageText);
    
  } catch (e) {
    console.error("错误:", e.message);
  }
  
  await close();
})();
