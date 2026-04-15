import { createClient } from '@supabase/supabase-js';
import { chromium } from 'playwright';

const SUPABASE_URL = 'https://opseuwrzcnsdrsizhyel.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_Pz0ndHiDt50G0nSU_ZHjxA_wcYzu1ez';
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// 三角洲行动改枪码常见格式：类似 "M4A1-烽火地带-6IUKUN40FGIGGAT87VQQ3"
const CODE_REGEX = /([A-Z0-9]{6,}-[A-Z0-9]{6,}-[A-Z0-9]{15,})/gi;

async function crawlYoumin() {
  console.log('🕷️ 开始爬取游民星空改枪码...');
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  try {
    // 游民星空三角洲行动圈子
    await page.goto('https://club.gamersky.com/forum/1736', { timeout: 30000 });
    await page.waitForTimeout(5000);
    
    // 获取页面全部文本
    const pageText = await page.evaluate(() => document.body.innerText);
    const matches = pageText.match(CODE_REGEX) || [];
    const uniqueCodes = [...new Set(matches)];
    console.log(`✅ 发现 ${uniqueCodes.length} 个改枪码`);
    
    for (const code of uniqueCodes) {
      await supabase.from('gunsmith_codes').upsert({
        code: code,
        source_site: '游民星空',
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
  console.log('🚀 开始执行爬虫...');
  await crawlYoumin();
  console.log('🎉 完成！');
}

main();
