import { createClient } from '@supabase/supabase-js';
import { chromium } from 'playwright';

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY;
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// 改枪码格式: 武器名-模式-一大串字符
const CODE_REGEX = /([A-Z0-9]+(?:突击步枪|冲锋枪|射手步枪|战斗步枪|机枪|霰弹枪)?-[烽火地带|全面战场]+-[A-Z0-9]{15,})/gi;

// 通过百度搜索指定关键词来获取包含改枪码的页面
async function crawlViaSearch(keyword, sourceSite) {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  let totalCodes = 0;

  try {
    const searchUrl = `https://www.baidu.com/s?wd=${encodeURIComponent(keyword)}`;
    await page.goto(searchUrl, { timeout: 30000, waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);

    // 获取搜索结果中的前 5 个链接
    const links = await page.$$eval('.result.c-container a', elements => 
      elements.map(el => el.href).filter(href => href && !href.includes('baidu.com'))
    );
    
    console.log(`📌 找到 ${links.length} 个相关页面，开始提取...`);

    for (const link of links.slice(0, 5)) {
      console.log(`🔗 进入页面: ${link}`);
      try {
        await page.goto(link, { timeout: 20000, waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(3000);
        
        // 提取页面全部文本
        const pageText = await page.evaluate(() => document.body.innerText);
        const matches = pageText.match(CODE_REGEX) || [];
        
        // 去重并插入数据库
        const uniqueCodes = [...new Set(matches)];
        for (const code of uniqueCodes) {
          const weaponName = code.split('-')[0] || '';
          
          const { error } = await supabase
            .from('gunsmith_codes')
            .upsert({
              code: code,
              weapon_name: weaponName,
              source_site: sourceSite,
              source_url: link,
              fetched_at: new Date().toISOString()
            }, { onConflict: 'code' });
            
          if (!error) {
            totalCodes++;
            console.log(`✅ [${sourceSite}] 插入: ${code}`);
          }
        }
      } catch (e) {
        console.error(`❌ 页面爬取失败: ${e.message}`);
      }
    }
  } catch (e) {
    console.error('❌ 搜索页爬取失败:', e.message);
  } finally {
    await browser.close();
  }
  return totalCodes;
}

async function main() {
  console.log('🚀 开始执行多源爬虫...');
  
  // 搜索关键词列表
  const keywords = [
    { kw: '三角洲行动 改枪码 site:bbs.nga.cn', site: 'NGA' },
    { kw: '三角洲行动 改枪码 site:club.gamersky.com', site: '游民星空' },
    { kw: '三角洲行动 改枪码 site:yuba.douyu.com', site: '斗鱼鱼吧' },
    { kw: '三角洲行动 改枪码 site:douyin.com', site: '抖音' }
  ];

  let grandTotal = 0;
  for (const item of keywords) {
    console.log(`🔍 搜索关键词: ${item.kw}`);
    const count = await crawlViaSearch(item.kw, item.site);
    grandTotal += count;
    console.log(`🎉 ${item.site} 本次共爬取 ${count} 个新改枪码`);
  }

  console.log(`🏁 爬虫任务结束。总计爬取: ${grandTotal} 个。`);
}

main();
