import { createClient } from '@supabase/supabase-js';
import { chromium } from 'playwright';

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY;
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// 三角洲行动改枪码格式：至少三段，由短横线连接，最后一段较长
const CODE_REGEX = /([A-Z0-9]+(?:-[A-Z0-9]+){2,})/gi;

async function crawlGamersky() {
  console.log('🕷️ 开始爬取游民星空三角洲行动版块...');
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  // 设置更真实的 User-Agent
  await page.setExtraHTTPHeaders({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  });
  
  let totalCodes = 0;
  
  try {
    // 爬取前 3 页
    for (let pageNum = 1; pageNum <= 3; pageNum++) {
      const url = pageNum === 1 
        ? 'https://club.gamersky.com/forum/1736' 
        : `https://club.gamersky.com/forum/1736-${pageNum}`;
      
      console.log(`📄 正在爬取第 ${pageNum} 页: ${url}`);
      
      try {
        await page.goto(url, { timeout: 30000, waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(3000);
        
        // 获取整个页面的文本内容
        const pageText = await page.evaluate(() => document.body.innerText);
        
        // 用正则提取所有匹配的改枪码
        const matches = pageText.match(CODE_REGEX) || [];
        const uniqueCodes = [...new Set(matches)]; // 去重
        
        console.log(`   📌 第 ${pageNum} 页提取到 ${uniqueCodes.length} 个改枪码`);
        
        // 插入数据库
        for (const code of uniqueCodes) {
          // 过滤掉太短的或明显不是改枪码的
          if (code.length < 15) continue;
          
          const { error } = await supabase
            .from('gunsmith_codes')
            .upsert({
              code: code,
              source_site: '游民星空',
              source_url: url,
              fetched_at: new Date().toISOString()
            }, { onConflict: 'code' });
            
          if (!error) {
            totalCodes++;
            console.log(`      ✅ 插入: ${code}`);
          }
        }
      } catch (e) {
        console.error(`   ❌ 第 ${pageNum} 页爬取失败:`, e.message);
      }
    }
    
    console.log(`🎉 本次共爬取 ${totalCodes} 个新改枪码`);
  } catch (e) {
    console.error('❌ 爬虫运行失败:', e.message);
  } finally {
    await browser.close();
  }
}

async function main() {
  console.log('🚀 开始执行爬虫...');
  await crawlGamersky();
  console.log('🏁 爬虫任务结束');
}

main();
