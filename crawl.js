import { createClient } from '@supabase/supabase-js';
import { chromium } from 'playwright';

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY;
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// 三角洲行动改枪码常见格式
const CODE_REGEX = /([A-Z0-9]{6,}-[A-Z0-9]{6,}-[A-Z0-9]{15,})/gi;

async function crawlYoumin() {
  console.log('🕷️ 开始爬取游民星空改枪码合集页...');
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  try {
    // 游民星空改枪码合集页面（多页，这里爬取前3页）
    const baseUrl = 'https://club.gamersky.com/forum/1736';
    let totalCodes = 0;
    
    for (let pageNum = 1; pageNum <= 3; pageNum++) {
      const url = pageNum === 1 ? baseUrl : `${baseUrl}-${pageNum}`;
      console.log(`📄 正在爬取第 ${pageNum} 页: ${url}`);
      
      await page.goto(url, { timeout: 30000 });
      await page.waitForTimeout(3000);
      
      // 获取帖子列表链接
      const postLinks = await page.$$eval('a.xst', links => links.map(a => a.href));
      console.log(`📌 第 ${pageNum} 页找到 ${postLinks.length} 个帖子`);
      
      for (const link of postLinks.slice(0, 5)) { // 每页只爬前5个帖子，加快速度
        console.log(`🔗 进入帖子: ${link}`);
        await page.goto(link, { timeout: 20000 });
        await page.waitForTimeout(2000);
        
        const pageText = await page.evaluate(() => document.body.innerText);
        const matches = pageText.match(CODE_REGEX) || [];
        
        for (const code of matches) {
          const { error } = await supabase
            .from('gunsmith_codes')
            .upsert({
              code: code,
              source_site: '游民星空',
              source_url: link,
              fetched_at: new Date().toISOString()
            }, { onConflict: 'code' });
            
          if (!error) {
            totalCodes++;
            console.log(`✅ 插入改枪码: ${code}`);
          }
        }
      }
    }
    console.log(`🎉 本次共爬取 ${totalCodes} 个改枪码`);
  } catch (e) {
    console.error('❌ 爬取失败:', e.message);
  } finally {
    await browser.close();
  }
}

async function main() {
  console.log('🚀 开始执行爬虫...');
  await crawlYoumin();
  console.log('🏁 爬虫任务结束');
}

main();
