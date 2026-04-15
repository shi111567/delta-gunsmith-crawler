import json
import re
import requests
import time
import random
from bs4 import BeautifulSoup

# --- 1. 配置目标网址 (一次性配置，之后无需改动) ---
TARGET_URLS = [
    "https://app.ali213.net/gl/1761633.html",  # 游侠网: 腾龙S9方案
    "https://yuba.douyu.com/discussion/4845959/anchor", # 斗鱼鱼吧: 主播自用码
    "https://www.vgover.com/news/209982",      # 电玩帮: S9制式券推荐
    "https://news.17173.com/content/08262025/132412345.shtml" # 17173: 最新改装码
]

# --- 2. 本地兜底数据 (网络异常时保证网站有内容可看) ---
DEFAULT_CODES = [
    { "name": "M4A1 高稳突击", "weapon": "M4A1", "class": "突击", "attachments": "垂直握把 + 消音器 + 红点", "code": "M4A1-烽火地带-6IUKUN40FGIGGAT87VQQ3" },
    { "name": "AKM 暴力输出", "weapon": "AKM", "class": "突击", "attachments": "补偿器 + 轻机枪托 + 全息", "code": "AKM-烽火地带-7JVLKP50GHKPH2BT98WR4" },
    { "name": "Vector 近战速射", "weapon": "Vector", "class": "侦察", "attachments": "激光 + 扩容弹匣 + 消音", "code": "VECTOR-烽火地带-3LJSND72KSL92JD7G3H4" }
]

# 更精确的改枪码格式 (至少12位，包含数字和大写字母)
CODE_PATTERN = re.compile(r"[A-Z0-9]{12,}")

# --- 3. 核心抓取函数 ---
def fetch_all_codes():
    all_codes = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for url in TARGET_URLS:
        try:
            print(f"🌐 正在抓取: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取页面中所有符合格式的文本
            page_text = soup.get_text()
            raw_codes = CODE_PATTERN.findall(page_text)
            
            # 去重并简单封装
            for code in set(raw_codes):
                all_codes.append({
                    "name": "网络热门配装",
                    "weapon": "自动识别",
                    "class": "全能",
                    "attachments": "全网实时热门改枪码",
                    "code": code
                })
            print(f"✅ 成功解析，获取到 {len(set(raw_codes))} 个候选代码")
            
            # 随机延时，防止请求过快被封
            time.sleep(random.uniform(1, 3))
            
        except Exception as e:
            print(f"❌ 抓取失败 {url}: {e}")

    # 全局去重
    unique_codes = []
    seen = set()
    for item in all_codes:
        if item["code"] not in seen:
            seen.add(item["code"])
            unique_codes.append(item)
            
    return unique_codes

# --- 4. 主执行函数 ---
def main():
    print("🚀 开始执行全自动改枪码更新任务...")
    online_codes = fetch_all_codes()
    
    final_codes = online_codes if online_codes else DEFAULT_CODES
    status_msg = f"✨ 更新完成！共获取 {len(online_codes)} 条在线数据。" if online_codes else "⚠️ 网络获取失败，本次使用兜底数据。"
    
    with open("codes.json", "w", encoding="utf-8") as f:
        json.dump(final_codes, f, ensure_ascii=False, indent=2)
    
    print(status_msg)
    print(f"🎉 数据已成功写入 codes.json")

if __name__ == "__main__":
    main()
