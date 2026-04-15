import { createClient } from '@supabase/supabase-js';
import { chromium } from 'playwright';

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY;
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// 三角洲行动改枪码常见格式
const CODE_REGEX = /([A-Z0-9]{6,}-[A-Z0-9]{6,}-[A-Z0-9]{15,})/gi;

async function crawlNGA() {
  console.log('🕷️ 开始爬取 NGA 三角洲行动板块...');
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  try {
    // NGA 三角洲行动版块
    await page.goto('https://bbs.nga.cn/thread.php?fid=-5761309', { timeout: 30000 });
    await page.waitForTimeout(5000);
    
    // 获取前 10 个帖子链接
    const postLinks = await page.$$eval('a.topic', links => links.map(a => a.href));
    console.log(`📌 找到 ${postLinks.length} 个帖子，开始爬取前 10 个...`);
    
    let totalCodes = 0;
    for (const link of postLinks.slice(0, 10)) {
      console.log(`🔗 进入帖子: ${link}`);
      await page.goto(link, { timeout: 20000 });
      await page.waitForTimeout(3000);
      
      const pageText = await page.evaluate(() => document.body.innerText);
      const matches = pageText.match(CODE_REGEX) || [];
      
      for (const code of matches) {
        const { error } = await supabase
          .from('gunsmith_codes')
          .upsert({
            code: code,
            source_site: 'NGA',
            source_url: link,
            fetched_at: new Date().toISOString()
          }, { onConflict: 'code' });
          
        if (!error) {
          totalCodes++;
          console.log(`✅ 插入改枪码: ${code}`);
        }
      }
    }
    console.log(`🎉 本次共爬取 ${totalCodes} 个改枪码`);
  } catch (e) {
    console.error('❌ NGA爬取失败:', e.message);
  } finally {
    await browser.close();
  }
}

async function main() {
  console.log('🚀 开始执行爬虫...');
  await crawlNGA();
  console.log('🏁 爬虫任务结束');
}

main();
