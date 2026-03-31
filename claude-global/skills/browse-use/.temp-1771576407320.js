
module.exports = async function({ browser, context, page, helpers }) {
  // Step 2: 连接到 feedly session，导入 OPML
// 运行: node ~/.claude/skills/browse-use/browse.js run /tmp/feedly-step2-import.js --session=feedly

const OPML_PATH = '/Users/liuyishou/tmp/karpathy-rss.opml';

// 重新导航到 organize 页面（named session 重连后需要重新导航）
await page.goto('https://feedly.com/i/organize');
await page.waitForLoadState('networkidle', { timeout: 15000 });

const url = page.url();
console.log('当前 URL:', url);

if (!url.includes('/i/organize')) {
  console.log('❌ 还没登录或不在 organize 页面');
  console.log('   当前 URL:', url);
  await page.screenshot({ path: '/Users/liuyishou/tmp/feedly-step2-state.png' });
  console.log('截图: /Users/liuyishou/tmp/feedly-step2-state.png');
  process.exit(1);
}

console.log('✅ 已在 organize 页面，开始找 Import 按钮...');
await page.screenshot({ path: '/Users/liuyishou/tmp/feedly-organize-ready.png' });

// 找 Import OPML 按钮/链接
const importSelectors = [
  'text=Import OPML',
  'text=Import',
  '[data-id="importOpml"]',
  'button:has-text("Import")',
  'a:has-text("Import")',
  '[class*="import"]',
];

let importButton = null;
for (const sel of importSelectors) {
  try {
    const el = page.locator(sel).first();
    if (await el.isVisible({ timeout: 2000 })) {
      importButton = el;
      console.log('找到 Import 按钮:', sel);
      break;
    }
  } catch (e) {}
}

if (!importButton) {
  console.log('未找到 Import 按钮，截图看实际内容...');
  await page.screenshot({ path: '/Users/liuyishou/tmp/feedly-no-import.png', fullPage: true });
  const text = await page.locator('body').innerText();
  console.log('页面内容摘要:', text.substring(0, 800));
} else {
  // 设置文件上传拦截
  const [fileChooser] = await Promise.all([
    page.waitForEvent('filechooser', { timeout: 10000 }),
    importButton.click(),
  ]);

  await fileChooser.setFiles(OPML_PATH);
  console.log('✅ OPML 文件已选择！等待上传确认...');

  await page.waitForTimeout(3000);
  await page.screenshot({ path: '/Users/liuyishou/tmp/feedly-after-import.png' });
  console.log('截图: /Users/liuyishou/tmp/feedly-after-import.png');
  console.log('🎉 导入完成！');
}

};
