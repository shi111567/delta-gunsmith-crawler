import { createClient } from '@supabase/supabase-js';
import { chromium } from 'playwright';

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY;
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// 改枪码正则（三角洲行动常见格式）
const CODE_REGEX = /([A-Z0-9]{6,}-[A-Z0-9]{6,}-[A-Z0-9]{15,})/gi;

async function crawlNGA() {
  console.log('🕷️ 开始爬取 NGA 三角洲行动板块...');
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  try {
    // NGA 三角洲行动板块，按发帖时间排序
    await page.goto('https://nga.178.com/thread.php?fid=803&order_by=postdatedesc', { 
      timeout: 30000,
      waitUntil: 'domcontentloaded' 
    });
    await page.waitForTimeout(3000);
    
    // 获取前5个帖子的链接
    const postLinks = await page.evaluate(() => {
      const links = [];
      document.querySelectorAll('tbody .topic a').forEach(a => {
        if (a.href && a.href.includes('read.php')) links.push(a.href);
      });
      return links.slice(0, 5);
    });
    
    console.log(`📌 找到 ${postLinks.length} 个帖子，开始逐个提取...`);
    const allCodes = [];
    
    for (const link of postLinks) {
      try {
        await page.goto(link, { timeout: 15000, waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);
        
        // 获取帖子标题和正文
        const content = await page.evaluate(() => {
          const title = document.querySelector('#postsubject0')?.innerText || '';
          const body = document.querySelector('#postcontent0')?.innerText || '';
          return { title, body };
        });
        
        // 合并文本提取改枪码
        const text = content.title + ' ' + content.body;
        const matches = text.match(CODE_REGEX) || [];
        matches.forEach(code => allCodes.push({ 
          code, 
          weapon_name: content.title.substring(0, 30) || '热门配装',
          source_site: 'NGA',
          source_url: link
        }));
        
        console.log(`   └─ ${link} 提取到 ${matches.length} 个码`);
      } catch (e) {
        console.warn(`   └─ 帖子 ${link} 访问失败: ${e.message}`);
      }
    }
    
    // 去重后存入数据库
    const uniqueCodes = Array.from(new Map(allCodes.map(c => [c.code, c])).values());
    console.log(`✅ 共提取 ${uniqueCodes.length} 个改枪码`);
    
    for (const item of uniqueCodes) {
      await supabase.from('gunsmith_codes').upsert({
        code: item.code,
        weapon_name: item.weapon_name,
        attachments: '热门推荐',
        source_site: item.source_site,
        fetched_at: new Date().toISOString()
      }, { onConflict: 'code' });
    }
  } catch (e) {
    console.error('爬取失败:', e.message);
  } finally {
    await browser.close();
  }
}

async function main() {
  console.log('🚀 开始执行 NGA 改枪码爬虫...');
  await crawlNGA();
  console.log('🎉 任务完成！');
}

main();
