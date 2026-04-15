import { chromium } from 'playwright';
import * as fs from 'fs/promises';

const TARGET_URL = 'https://g.aitags.cn/';

async function crawlAitags() {
  console.log('🕷️ 开始爬取 aitags.cn ...');
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  try {
    await page.goto(TARGET_URL, { timeout: 30000, waitUntil: 'domcontentloaded' });
    await page.waitForSelector('table tbody tr', { timeout: 10000 });

    const codes = await page.$$eval('table tbody tr', (rows) => {
      return rows.map(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length >= 3) {
          const weapon = cells[0]?.innerText?.trim() || '未知武器';
          const attachments = cells[1]?.innerText?.trim() || '';
          const code = cells[2]?.innerText?.trim();
          
          if (code && code.length > 10) {
            return {
              name: weapon,
              weapon: weapon.split(' ')[0],
              attachments: attachments,
              code: code,
              class: '全能'
            };
          }
        }
        return null;
      }).filter(item => item !== null);  // 这一行之前少了闭合括号，现已修正
    });

    console.log(`✅ 成功提取 ${codes.length} 条改枪码`);

    if (codes.length === 0) {
      console.warn("⚠️ 表格提取失败，尝试从整个页面提取...");
      const pageText = await page.evaluate(() => document.body.innerText);
      const regex = /([A-Z0-9]+(?:-[A-Z0-9]+){2,})/gi;
      const matches = pageText.match(regex) || [];
      const uniqueCodes = [...new Set(matches)];
      const fallbackCodes = uniqueCodes.map(code => ({
        name: code.split('-')[0] || '未知武器',
        weapon: code.split('-')[0] || '',
        attachments: '',
        code: code,
        class: '全能'
      }));
      if (fallbackCodes.length > 0) {
        await fs.writeFile('codes.json', JSON.stringify(fallbackCodes, null, 2));
        console.log(`💾 备用方案提取 ${fallbackCodes.length} 条改枪码并保存`);
        return;
      }
    }

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
