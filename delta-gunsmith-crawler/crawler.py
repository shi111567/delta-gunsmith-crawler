import json
import requests
from bs4 import BeautifulSoup
import re
import time
import random

# ========== 配置区域 ==========
# 您可以在这里添加更多改枪码来源网站
SOURCE_URLS = [
    "https://www.18183.com/delta/",  # 示例网站，需替换为真实改枪码汇总页面
    "https://wiki.biligame.com/delta/",  # B站Wiki
]

# 输出文件名
OUTPUT_FILE = "codes.json"

# ========== 核心抓取函数 ==========
def fetch_codes():
    all_codes = []
    
    for url in SOURCE_URLS:
        try:
            print(f"正在抓取: {url}")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            resp = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # 根据实际网页结构调整选择器
            # 示例：寻找包含改枪码的表格或卡片
            code_blocks = soup.find_all("code") or soup.find_all("pre")
            
            for block in code_blocks:
                text = block.get_text()
                # 正则匹配典型的改枪码格式（可根据实际调整）
                matches = re.findall(r"[A-Z0-9]{4,}-[A-Z0-9]{4,}-[A-Z0-9]{4,}", text)
                for code in matches:
                    all_codes.append({
                        "name": "热门改枪码",
                        "weapon": "自动识别",
                        "class": "全能",
                        "attachments": "网络热门配装",
                        "code": code
                    })
            
            time.sleep(random.uniform(1, 3))  # 礼貌延迟
        except Exception as e:
            print(f"抓取失败 {url}: {e}")
    
    # 去重
    unique_codes = []
    seen = set()
    for item in all_codes:
        if item["code"] not in seen:
            seen.add(item["code"])
            unique_codes.append(item)
    
    return unique_codes

# ========== 默认备用数据（网络失败时使用） ==========
DEFAULT_CODES = [
    {"name": "M4A1 高稳突击", "weapon": "M4A1", "class": "突击", "attachments": "垂直握把 + 消音器 + 红点", "code": "M4A1-烽火地带-6IUKUN40FGIGGAT87VQQ3"},
    {"name": "AKM 暴力输出", "weapon": "AKM", "class": "突击", "attachments": "补偿器 + 轻机枪托 + 全息", "code": "AKM-烽火地带-7JVLKP50GHKPH2BT98WR4"},
    {"name": "Vector 近战速射", "weapon": "Vector", "class": "侦察", "attachments": "激光 + 扩容弹匣 + 消音", "code": "VECTOR-烽火地带-3LJSND72KSL92JD7G3H4"},
    {"name": "AWM 狙击精英", "weapon": "AWM", "class": "侦察", "attachments": "高倍镜 + 消音器 + 托腮板", "code": "AWM-烽火地带-8KTMVQ61HLQN3CU9ZR5"},
    {"name": "P90 冲锋陷阵", "weapon": "P90", "class": "突击", "attachments": "红点 + 扩容弹匣 + 消音器", "code": "P90-烽火地带-2GJQW83FJ4KSL92JD7G3H4"}
]

# ========== 主函数 ==========
def main():
    print("开始抓取改枪码...")
    codes = fetch_codes()
    
    if len(codes) == 0:
        print("未抓取到任何新数据，使用默认数据")
        codes = DEFAULT_CODES
    else:
        print(f"成功抓取 {len(codes)} 条改枪码")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(codes, f, ensure_ascii=False, indent=2)
    
    print(f"数据已保存到 {OUTPUT_FILE}")

if __name__ == "__main__":
    main()