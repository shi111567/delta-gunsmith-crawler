import { createClient } from '@supabase/supabase-js';
import { chromium } from 'playwright';

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY;
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// 改枪码格式: 枪械名-烽火地带-一大串字符
const CODE_REGEX = /([A-Z0-9]+-[烽火地带|全面战场]+-[A-Z0-9]{15,})/gi;

// 提取代码并存入数据库的通用函数
async function extractAndUpsertCodes(text, sourceSite, sourceUrl) {
  const matches = text.match(CODE_REGEX) || [];
  const uniqueCodes = [...new Set(matches)]; // 去重
  let count = 0;
  
  for (const code of uniqueCodes) {
    // 可选: 提取武器名 (通过第一个 '-' 分割)
    const weaponName = code.split('-')[0] || '';
    
    const { error } = await supabase
      .from('gunsmith_codes')
      .upsert({
        code: code,
        weapon_name: weaponName,
        source_site: sourceSite,
        source_url: sourceUrl,
        fetched_at: new Date().toISOString()
      }, { onConflict: 'code' }); // 代码已存在则更新抓取时间
        
    if (!error) {
      count++;
      console.log(`✅ [${sourceSite}] 插入: ${code}`);
    } else {
      console.warn(`⚠️ [${sourceSite}] 插入失败: ${error.message}`);
    }
  }
  return count;
}

// 1. 爬取 B站 搜索页面
async function crawlBilibili() {
  console.log('🕷️ 开始爬取 B站 改枪码...');
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  let totalCodes = 0;

  try {
    // B站搜索“三角洲行动 改枪码”，按最新排序
    const searchUrl = 'https://search.bilibili.com/all?keyword=三角洲行动 改枪码&order=pubdate';
    await page.goto(searchUrl, { timeout: 30000, waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);

    // 获取搜索结果中的视频卡片链接 (前 5 个)
    const videoLinks = await page.$$eval('.bili-video-card .bili-video-card__wrap', cards => 
      cards.map(card => card.href).filter(href => href)
    );
    console.log(`📌 B站找到 ${videoLinks.length} 个相关视频`);

    // 爬取每个视频的详情页
    for (const link of videoLinks.slice(0, 8)) {
      console.log(`🔗 进入视频: ${link}`);
      try {
        await page.goto(link, { timeout: 20000, waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);
        
        // 提取视频标题和简介
        const pageText = await page.evaluate(() => {
          const title = document.querySelector('h1.video-title')?.innerText || '';
          const desc = document.querySelector('.video-desc-container .desc-info-text')?.innerText || '';
          return title + ' ' + desc;
        });
        
        const count = await extractAndUpsertCodes(pageText, 'B站', link);
        totalCodes += count;
      } catch (e) {
        console.error(`❌ B站视频爬取失败: ${e.message}`);
      }
    }
    console.log(`🎉 B站共爬取 ${totalCodes} 个改枪码`);
  } catch (e) {
    console.error('❌ B站搜索页爬取失败:', e.message);
  } finally {
    await browser.close();
  }
  return totalCodes;
}

// 2. 爬取 斗鱼鱼吧
async function crawlDouyuYuba() {
  console.log('🕷️ 开始爬取 斗鱼鱼吧 改枪码...');
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  let totalCodes = 0;

  // 预设几个已知分享改枪码的鱼吧动态链接
  const feedUrls = [
    'https://yuba.douyu.com/feed/2822393100100471078',
    'https://yuba.douyu.com/feed/2841398423062683087',
    // 你可以在这里手动添加更多链接
  ];

  try {
    for (const link of feedUrls) {
      console.log(`🔗 进入鱼吧动态: ${link}`);
      try {
        await page.goto(link, { timeout: 20000, waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);
        
        // 提取整个页面的文本，改枪码就嵌在里面
        const pageText = await page.evaluate(() => document.body.innerText);
        const count = await extractAndUpsertCodes(pageText, '斗鱼鱼吧', link);
        totalCodes += count;
      } catch (e) {
        console.error(`❌ 鱼吧动态爬取失败: ${e.message}`);
      }
    }
    console.log(`🎉 斗鱼鱼吧共爬取 ${totalCodes} 个改枪码`);
  } catch (e) {
    console.error('❌ 斗鱼鱼吧爬取失败:', e.message);
  } finally {
    await browser.close();
  }
  return totalCodes;
}

// 主函数
async function main() {
  console.log('🚀 开始执行多源爬虫...');
  
  const biliCount = await crawlBilibili();
  const douyuCount = await crawlDouyuYuba();
  
  console.log(`🏁 爬虫任务结束。B站: ${biliCount} 个，斗鱼: ${douyuCount} 个，总计: ${biliCount + douyuCount} 个。`);
}

main();
