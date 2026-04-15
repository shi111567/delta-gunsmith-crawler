import { chromium } from 'playwright';
import * as fs from 'fs/promises';

// 目标网站，汇集了三角洲行动大量的改枪码
const TARGET_URL = 'https://g.aitags.cn/';

async function crawlAitags() {
  console.log('🕷️ 开始爬取 aitags.cn ...');
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  try {
    await page.goto(TARGET_URL, { timeout: 30000, waitUntil: 'domcontentloaded' });
    // 等待页面上的表格加载完成
    await page.waitForSelector('table tbody tr', { timeout: 10000 });

    // 在页面上下文中执行脚本，提取表格数据
    const codes = await page.$$eval('table tbody tr', (rows) => {
      return rows.map(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length >= 3) {
          // 假设表格结构为：枪械名称 | 配件信息 | 改枪码
          const weapon = cells[0]?.innerText?.trim() || '未知武器';
          const attachments = cells[1]?.innerText?.trim() || '';
          const code = cells[2]?.innerText?.trim();
          
          // 简单的验证，确保提取到的是有效改枪码
          if (code && code.length > 10) {
            return {
              name: weapon,
              weapon: weapon.split(' ')[0], // 简化武器名，比如“M4A1 突击步枪” -> “M4A1”
              attachments: attachments,
              code: code,
              class: '全能' // 默认分类，你可以根据需要调整
            };
          }
          return null;
        }).filter(item => item !== null);
    });

    console.log(`✅ 成功提取 ${codes.length} 条改枪码`);

    // 如果网站改版，上面的选择器失效，可以回退到之前提取整个页面文本的方案。
    if (codes.length === 0) {
        console.warn("⚠️ 表格提取失败，尝试从整个页面提取...");
        // ... (这里可以放入你之前用的正则提取方案作为备用)
    }

    // 将提取到的数据写入 codes.json 文件
    if (codes.length > 0) {
      await fs.writeFile('codes.json', JSON.stringify(codes, null, 2));
      console.log('💾 数据已保存到 codes.json');
    } else {
      console.log('❌ 未提取到任何改枪码，不更新文件。');
    }

  } catch (e) {
    console.error('❌ 爬虫运行失败:', e.message);
  } finally {
    await browser.close();
  }
}

async function main() {
  console.log('🚀 开始执行爬虫...');
  await crawlAitags();
  console.log('🏁 爬虫任务结束');
}

main();
