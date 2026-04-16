import json
import re
import requests
import time
import random
from bs4 import BeautifulSoup

# ==================== 1. 配置目标网址 ====================
TARGET_URLS = [
    "https://app.ali213.net/gl/1761633.html",       # 游侠网: 腾龙S9方案
    "https://yuba.douyu.com/discussion/4845959/anchor",  # 斗鱼鱼吧: 主播自用码
    "https://www.vgover.com/news/209982",            # 电玩帮: S9制式券推荐
    "https://news.17173.com/content/08262025/132412345.shtml"  # 17173: 最新改装码
]

# ==================== 2. 枪械分类映射表 ====================
WEAPON_CLASS_MAP = {
    # 突击步枪 → 突击
    "M4A1": "突击", "AKM": "突击", "AK-12": "突击", "SCAR-H": "突击",
    "K416": "突击", "K437": "突击", "AR57": "突击", "AUG": "突击",
    "MCX": "突击", "MCX LT": "突击", "PTR-32": "突击", "腾龙突击步枪": "突击",
    "CAR-15": "突击", "191式": "突击", "QBZ95-1": "突击", "SG552": "突击",
    "AS Val": "突击", "M7": "突击", "MK47": "突击", "G3": "突击",
    # 冲锋枪 → 侦察
    "MP5": "侦察", "MP7": "侦察", "Vector": "侦察", "UZI": "侦察",
    "P90": "侦察", "SR-3M": "侦察", "SMG-45": "侦察", "勇士冲锋枪": "侦察",
    "QCQ171": "侦察",
    # 狙击步枪 / 射手步枪 → 支援
    "AWM": "支援", "M82A1": "支援", "R93": "支援", "SR-25": "支援",
    "M14": "支援", "VSS": "支援", "PKM": "支援", "M249": "支援",
    "M250": "支援", "QJB201": "支援",
    # 霰弹枪 → 工程
    "S12K": "工程", "M1014": "工程", "FS-12": "工程", "M870": "工程",
    # 战斗步枪 / 其他
    "ASh-12": "突击", "KC17": "突击",
}

# 枪械名称别名
WEAPON_ALIASES = {
    "腾龙": "腾龙突击步枪",
    "ptr": "PTR-32",
    "m4": "M4A1",
    "ak": "AKM",
    "k4": "K416",
    "mp": "MP5",
}

# ==================== 3. 本地兜底数据（含价格） ====================
DEFAULT_CODES = [
    {
        "name": "腾龙24万稳导低改",
        "weapon": "腾龙突击步枪",
        "class": "突击",
        "attachments": "影袭托芯枪托 + 新式蛟龙战术长枪管 + 高速导气",
        "code": "6IMVF7O0B0GKDDOTE9T6Q",
        "price": "24万"
    },
    {
        "name": "G3战斗步枪",
        "weapon": "G3战斗步枪",
        "class": "突击",
        "attachments": "长枪管 + 垂直握把 + 红点瞄具",
        "code": "G3战斗步枪-烽火地带-6JO0TDK0AQGR1G4DCP72P",
        "price": "18万"
    },
    {
        "name": "三倍AUG突击步枪",
        "weapon": "AUG突击步枪",
        "class": "突击",
        "attachments": "三倍镜 + 556四级弹 + 垂直握把",
        "code": "三倍AUG突击步枪-烽火地带-6JO0VHO0AQGR1G4DCP72P",
        "price": "32万"
    },
    {
        "name": "AR57 31万腰射双修",
        "weapon": "AR57突击步枪",
        "class": "突击",
        "attachments": "核心配件半改 + 腰射拉满 + 高稳定倍镜",
        "code": "AR57突击步枪-烽火地带-6JO197C095AEL8D57LH45",
        "price": "31万"
    },
    {
        "name": "勇士冲锋枪-制式券均衡",
        "weapon": "勇士冲锋枪",
        "class": "侦察",
        "attachments": "制式券标准配置 + 均衡改装",
        "code": "6J2Q7Q40FP8PKANEBHTBM",
        "price": "15万"
    },
    {
        "name": "SG552紫弹高稳",
        "weapon": "SG552突击步枪",
        "class": "突击",
        "attachments": "紫弹配置 + 快稳兼顾",
        "code": "6J2PFG40FP8PKANEBHTBM",
        "price": "28万"
    },
    {
        "name": "MK47腰射高甲穿",
        "weapon": "MK47突击步枪",
        "class": "突击",
        "attachments": "钛金竞赛制退器 + 垂直握把 + 40发扩容",
        "code": "MK47突击步枪-烽火地带-6JI0PUO0BNSV43TFRAQ1K",
        "price": "45万"
    },
    {
        "name": "Vector近战蒸发器",
        "weapon": "Vector冲锋枪",
        "class": "侦察",
        "attachments": "超高射速 + 近战王者",
        "code": "Vector冲锋枪-全面战场-6HB6D28064DU5TFLJ691H",
        "price": "22万"
    },
    {
        "name": "MP7冲锋枪-S9任务推荐",
        "weapon": "MP7冲锋枪",
        "class": "侦察",
        "attachments": "疾风配置 + 中距离稳定",
        "code": "MP7冲锋枪-烽火地带-6JO105G0AQGR1G4DCP72P",
        "price": "19万"
    },
    {
        "name": "PTR-32零后坐力激光枪",
        "weapon": "PTR-32突击步枪",
        "class": "突击",
        "attachments": "G3镂空握把 + G3加强长枪管 + FFC双流制退器",
        "code": "6IRJFES09FR1N24J7HKOH",
        "price": "38万"
    },
    # 补充一些 S9 赛季热门方案
    {
        "name": "K416高稳突击",
        "weapon": "K416突击步枪",
        "class": "突击",
        "attachments": "堡垒水平 + 红激光 + 共振一代 + A8长枪管",
        "code": "K416突击步枪-全面战场-6EIALPC02U9HU6AC38CQJ",
        "price": "26万"
    },
    {
        "name": "AS VAL消音突袭",
        "weapon": "AS Val突击步枪",
        "class": "突击",
        "attachments": "长枪管 + 红镭射 + RK-0前握把 + 45发",
        "code": "ASVal突击步枪-全面战场-6EIAKVC02U9HU6AC38CQJ",
        "price": "20万"
    },
    {
        "name": "M14射手步枪-主播同款",
        "weapon": "M14射手步枪",
        "class": "支援",
        "attachments": "消音器 + 8倍镜 + 脚架 + 快速弹匣",
        "code": "M14射手步枪-烽火地带-6G5S6M00DN8Q98HB5S4IC",
        "price": "35万"
    },
    {
        "name": "K437突击步枪-主播自用",
        "weapon": "K437突击步枪",
        "class": "突击",
        "attachments": "垂直握把 + 消音器 + 红点 + 快速弹匣",
        "code": "K437突击步枪-烽火地带-6G0RKVK04DB5TLDRK4HKE",
        "price": "30万"
    },
    {
        "name": "UZI冲锋枪-近战秒杀",
        "weapon": "UZI冲锋枪",
        "class": "侦察",
        "attachments": "钛金制退器 + 导轨护木 + 红激光 + 45发",
        "code": "UZI冲锋枪-全面战场-6EIALBS02U9HU6AC38CQJ",
        "price": "12万"
    }
]

# ==================== 4. 正则表达式 ====================
FULL_CODE_PATTERN = re.compile(
    r"([A-Za-z0-9\u4e00-\u9fff\-\.\s]+?)"  # 枪械名
    r"[-—]"                                 # 分隔符
    r"([全面战场|烽火地带]+)"                # 模式
    r"[-—]"                                 # 分隔符
    r"([A-Z0-9]{12,})",                     # 代码
    re.IGNORECASE
)

CODE_ONLY_PATTERN = re.compile(r"[A-Z0-9]{12,}")


# ==================== 5. 根据枪械名判断兵种 ====================
def get_weapon_class(weapon_name):
    if not weapon_name:
        return "全能"
    weapon_upper = weapon_name.upper()
    for alias, full_name in WEAPON_ALIASES.items():
        if alias.upper() in weapon_upper:
            weapon_name = full_name
            break
    for key, cls in WEAPON_CLASS_MAP.items():
        if key.upper() in weapon_upper:
            return cls
    if any(x in weapon_name for x in ["冲锋", "MP", "UZI", "Vector", "P90", "SMG"]):
        return "侦察"
    elif any(x in weapon_name for x in ["狙击", "射手", "SR", "M14", "AWM", "PKM", "M249"]):
        return "支援"
    elif any(x in weapon_name for x in ["霰弹", "S12K", "M1014"]):
        return "工程"
    elif any(x in weapon_name for x in ["突击", "步枪", "AR", "AK", "M4", "K416", "SCAR"]):
        return "突击"
    return "全能"


# ==================== 6. 提取价格（增强版） ====================
def extract_price(context):
    """从文本中尝试提取价格，返回如 '24万' 或 None"""
    # 匹配 "24万"、"18.5万"、"18.5w"、"32000" 等格式
    match = re.search(r'(\d+(?:\.\d+)?)\s*[万wW]', context)
    if match:
        return match.group(1) + '万'
    # 匹配纯数字价格（如 32000）
    match2 = re.search(r'(\d{4,6})(?:\s*元|\s*哈夫币|\s*金币)?', context)
    if match2:
        num = int(match2.group(1))
        if num >= 10000:
            return f"{num/10000:.1f}万"
        else:
            return str(num)
    return None


# ==================== 7. 核心抓取函数（增强版） ====================
def fetch_all_codes():
    all_codes = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for url in TARGET_URLS:
        try:
            print(f"🌐 正在抓取: {url}")
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.get_text()

            # 方法1: 匹配完整格式 "枪名-模式-代码"
            matches = FULL_CODE_PATTERN.findall(page_text)

            if matches:
                print(f"   ✅ 匹配到 {len(matches)} 个完整格式的改枪码")
                for weapon_part, mode, code in matches:
                    weapon_name = weapon_part.strip()
                    weapon_name = re.sub(r"\s+", " ", weapon_name)
                    weapon_class = get_weapon_class(weapon_name)

                    # 尝试提取价格（扩大搜索范围）
                    code_pos = page_text.find(code)
                    context = page_text[max(0, code_pos-300):code_pos+150] if code_pos > 0 else ""
                    price = extract_price(context)

                    all_codes.append({
                        "name": f"{weapon_name} 配装方案",
                        "weapon": weapon_name,
                        "class": weapon_class,
                        "attachments": "详见原文",
                        "code": code,
                        "price": price
                    })
            else:
                # 方法2: 只匹配代码，尝试推断枪名
                raw_codes = CODE_ONLY_PATTERN.findall(page_text)
                unique_raw = list(set(raw_codes))
                print(f"   ⚠️ 未匹配到完整格式，找到 {len(unique_raw)} 个代码")

                for code in unique_raw:
                    code_pos = page_text.find(code)
                    context = page_text[max(0, code_pos-200):code_pos+100] if code_pos > 0 else ""
                    weapon_name = "未知枪械"
                    for key in WEAPON_CLASS_MAP.keys():
                        if key.upper() in context.upper():
                            weapon_name = key
                            break
                    weapon_class = get_weapon_class(weapon_name)
                    price = extract_price(context)

                    all_codes.append({
                        "name": f"{weapon_name} 热门配装" if weapon_name != "未知枪械" else "网络热门方案",
                        "weapon": weapon_name,
                        "class": weapon_class,
                        "attachments": "全网实时热门改枪码",
                        "code": code,
                        "price": price
                    })

            time.sleep(random.uniform(1, 3))

        except Exception as e:
            print(f"   ❌ 抓取失败 {url}: {e}")

    # 去重
    unique_codes = []
    seen = set()
    for item in all_codes:
        if item["code"] not in seen:
            seen.add(item["code"])
            unique_codes.append(item)

    print(f"\n📊 共获取 {len(unique_codes)} 个有效改枪码")
    return unique_codes


# ==================== 8. 主函数（确保至少输出15条） ====================
def main():
    print("🚀 开始执行全自动改枪码更新任务...")
    print("=" * 50)

    online_codes = fetch_all_codes()

    # 合并在线数据和默认数据
    if len(online_codes) < 5:
        print("⚠️ 在线数据较少，补充默认数据")
        final_codes = online_codes + DEFAULT_CODES
    elif not online_codes:
        print("⚠️ 网络获取失败，使用兜底数据")
        final_codes = DEFAULT_CODES
    else:
        # 在线数据足够，但仍补充一些默认数据确保数量
        final_codes = online_codes + DEFAULT_CODES[:5]

    # 去重（以 code 为准）
    seen = set()
    unique_final = []
    for item in final_codes:
        if item["code"] not in seen:
            seen.add(item["code"])
            # 确保 price 字段存在，如果不存在则尝试从 attachments 或 name 中提取
            if "price" not in item or item["price"] is None:
                # 尝试从 name 中提取价格
                price_from_name = extract_price(item.get("name", ""))
                if price_from_name:
                    item["price"] = price_from_name
                else:
                    # 给一个默认价格范围
                    item["price"] = "暂无报价"
            unique_final.append(item)

    # 确保至少有15条数据
    if len(unique_final) < 15:
        print(f"⚠️ 当前数据只有 {len(unique_final)} 条，补充更多默认数据")
        for extra in DEFAULT_CODES:
            if extra["code"] not in seen:
                seen.add(extra["code"])
                unique_final.append(extra)
                if len(unique_final) >= 20:
                    break

    with open("codes.json", "w", encoding="utf-8") as f:
        json.dump(unique_final, f, ensure_ascii=False, indent=2)

    print("=" * 50)
    print(f"🎉 数据已成功写入 codes.json，共 {len(unique_final)} 条")

    # 统计兵种分布
    class_count = {}
    price_count = 0
    for item in unique_final:
        cls = item.get("class", "全能")
        class_count[cls] = class_count.get(cls, 0) + 1
        if item.get("price") and item["price"] != "暂无报价":
            price_count += 1
    print(f"📈 兵种分布: {class_count}")
    print(f"💰 含价格数据: {price_count}/{len(unique_final)} 条")


if __name__ == "__main__":
    main()
