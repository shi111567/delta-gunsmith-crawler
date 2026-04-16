import json
import re
import requests
import time
import random
from bs4 import BeautifulSoup
from datetime import datetime

# ==================== 1. 配置目标网址 ====================
TARGET_URLS = [
    "https://app.ali213.net/gl/1761633.html",
    "https://yuba.douyu.com/discussion/4845959/anchor",
    "https://www.vgover.com/news/209982",
    "https://news.17173.com/content/08262025/132412345.shtml"
]

# ==================== 2. 枪械分类映射表 ====================
WEAPON_CLASS_MAP = {
    "M4A1": "突击", "AKM": "突击", "AK-12": "突击", "SCAR-H": "突击",
    "K416": "突击", "K437": "突击", "AR57": "突击", "AUG": "突击",
    "MCX": "突击", "MCX LT": "突击", "PTR-32": "突击", "腾龙突击步枪": "突击",
    "CAR-15": "突击", "191式": "突击", "QBZ95-1": "突击", "SG552": "突击",
    "AS Val": "突击", "M7": "突击", "MK47": "突击", "G3": "突击",
    "MP5": "侦察", "MP7": "侦察", "Vector": "侦察", "UZI": "侦察",
    "P90": "侦察", "SR-3M": "侦察", "SMG-45": "侦察", "勇士冲锋枪": "侦察",
    "QCQ171": "侦察",
    "AWM": "支援", "M82A1": "支援", "R93": "支援", "SR-25": "支援",
    "M14": "支援", "VSS": "支援", "PKM": "支援", "M249": "支援",
    "M250": "支援", "QJB201": "支援",
    "S12K": "工程", "M1014": "工程", "FS-12": "工程", "M870": "工程",
    "ASh-12": "突击", "KC17": "突击",
}

WEAPON_ALIASES = {
    "腾龙": "腾龙突击步枪",
    "ptr": "PTR-32",
    "m4": "M4A1",
    "ak": "AKM",
    "k4": "K416",
    "mp": "MP5",
}

# ==================== 3. 本地兜底数据 ====================
DEFAULT_CODES = [
    {"name": "腾龙24万稳导低改", "weapon": "腾龙突击步枪", "class": "突击", "attachments": "影袭托芯枪托 + 新式蛟龙战术长枪管 + 高速导气", "code": "6IMVF7O0B0GKDDOTE9T6Q", "price": "24万"},
    {"name": "G3战斗步枪", "weapon": "G3战斗步枪", "class": "突击", "attachments": "长枪管 + 垂直握把 + 红点瞄具", "code": "G3战斗步枪-烽火地带-6JO0TDK0AQGR1G4DCP72P", "price": "18万"},
    {"name": "三倍AUG突击步枪", "weapon": "AUG突击步枪", "class": "突击", "attachments": "三倍镜 + 556四级弹 + 垂直握把", "code": "三倍AUG突击步枪-烽火地带-6JO0VHO0AQGR1G4DCP72P", "price": "32万"},
    {"name": "AR57 31万腰射双修", "weapon": "AR57突击步枪", "class": "突击", "attachments": "核心配件半改 + 腰射拉满 + 高稳定倍镜", "code": "AR57突击步枪-烽火地带-6JO197C095AEL8D57LH45", "price": "31万"},
    {"name": "勇士冲锋枪-制式券均衡", "weapon": "勇士冲锋枪", "class": "侦察", "attachments": "制式券标准配置 + 均衡改装", "code": "6J2Q7Q40FP8PKANEBHTBM", "price": "15万"},
    {"name": "SG552紫弹高稳", "weapon": "SG552突击步枪", "class": "突击", "attachments": "紫弹配置 + 快稳兼顾", "code": "6J2PFG40FP8PKANEBHTBM", "price": "28万"},
    {"name": "MK47腰射高甲穿", "weapon": "MK47突击步枪", "class": "突击", "attachments": "钛金竞赛制退器 + 垂直握把 + 40发扩容", "code": "MK47突击步枪-烽火地带-6JI0PUO0BNSV43TFRAQ1K", "price": "45万"},
    {"name": "Vector近战蒸发器", "weapon": "Vector冲锋枪", "class": "侦察", "attachments": "超高射速 + 近战王者", "code": "Vector冲锋枪-全面战场-6HB6D28064DU5TFLJ691H", "price": "22万"},
    {"name": "MP7冲锋枪-S9任务推荐", "weapon": "MP7冲锋枪", "class": "侦察", "attachments": "疾风配置 + 中距离稳定", "code": "MP7冲锋枪-烽火地带-6JO105G0AQGR1G4DCP72P", "price": "19万"},
    {"name": "PTR-32零后坐力激光枪", "weapon": "PTR-32突击步枪", "class": "突击", "attachments": "G3镂空握把 + G3加强长枪管 + FFC双流制退器", "code": "6IRJFES09FR1N24J7HKOH", "price": "38万"},
]

# ==================== 4. 正则表达式 ====================
FULL_CODE_PATTERN = re.compile(
    r"([A-Za-z0-9\u4e00-\u9fff\-\.\s]+?)[-—]([全面战场|烽火地带]+)[-—]([A-Z0-9]{12,})",
    re.IGNORECASE
)
CODE_ONLY_PATTERN = re.compile(r"[A-Z0-9]{12,}")

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

def extract_price(context):
    match = re.search(r'(\d+(?:\.\d+)?)\s*[万wW]', context)
    if match:
        return match.group(1) + '万'
    return None

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
            matches = FULL_CODE_PATTERN.findall(page_text)
            if matches:
                print(f"   ✅ 匹配到 {len(matches)} 个完整格式的改枪码")
                for weapon_part, mode, code in matches:
                    weapon_name = weapon_part.strip()
                    weapon_name = re.sub(r"\s+", " ", weapon_name)
                    weapon_class = get_weapon_class(weapon_name)
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
    unique_codes = []
    seen = set()
    for item in all_codes:
        if item["code"] not in seen:
            seen.add(item["code"])
            unique_codes.append(item)
    print(f"\n📊 共获取 {len(unique_codes)} 个有效改枪码")
    return unique_codes

# ==================== 5. 起装方案生成（新增） ====================
ARMOR_PRICE_BASE = {
    "蝰蛇轻型": 12.0, "蝰蛇系列": 7.8, "2级轻便甲": 2.0, "3级防弹背心": 3.0,
    "3级甲": 4.0, "射手战术背心": 5.0, "DT-AVS防弹衣": 15.0, "四级甲": 18.0,
}
HELMET_PRICE_BASE = {
    "4级听力头戴": 5.0, "户外棒球帽": 3.4, "破损五级头": 6.0, "MC201战术头盔": 5.0,
    "D6头盔": 7.0, "MHS战术头盔": 10.0, "四级头": 10.0, "GT1战术头盔": 8.0, "三级头": 4.0,
}
BACKPACK_PRICE_BASE = {
    "MAP侦察背包": 4.4, "强袭战术背心": 3.0, "战术快拆背包": 4.0,
    "GIR野战胸挂": 5.0, "野战背包": 3.0,
}

BUDGET_LOADOUT_TEMPLATES = [
    {"name": "丐版野牛·极限跑刀", "scenario": "跑刀", "map": ["大坝", "长弓溪谷"],
     "weapons": [{"name": "野牛冲锋枪", "price": 3.3, "desc": "丐中丐版，近战糊脸", "code": "野牛冲锋枪-烽火地带-6IDNJTC0FCDV4UPACJK76"}],
     "armors": [{"name": "蝰蛇轻型", "price": 12.0, "desc": "四级防护，不减移速"}],
     "helmets": [{"name": "蝰蛇系列", "price": 7.8, "desc": "配套四级头"}],
     "backpacks": [{"name": "MAP侦察背包", "price": 4.4, "desc": "24格大容量"}],
     "features": "极致性价比，专为跑刀设计，投入极低，捡到就是赚到。", "hotScore": 95},
    {"name": "CAR-15·步枪跑刀", "scenario": "跑刀", "map": ["巴克什", "大坝"],
     "weapons": [{"name": "CAR-15突击步枪", "price": 3.1, "desc": "50米内压枪稳定", "code": "CAR-15突击步枪-烽火地带-6IDNQUC0FCDV4UPACJK76"}],
     "armors": [{"name": "2级轻便甲", "price": 2.0, "desc": "不拖累移速"}],
     "helmets": [{"name": "4级听力头戴", "price": 5.0, "desc": "听脚步防偷袭"}],
     "backpacks": [{"name": "强袭战术背心", "price": 3.0, "desc": "14格容量"}],
     "features": "步枪跑刀，中距离作战能力更强，不虚一般AI。", "hotScore": 88},
    {"name": "M870·卡战备神器", "scenario": "卡战备", "map": ["航天基地", "长弓溪谷"],
     "weapons": [{"name": "M870霰弹枪", "price": 4.0, "desc": "近战秒人，清AI效率极高", "code": "M870-烽火地带-6H6B1K808BFD9V58JNQMS"}],
     "armors": [{"name": "3级防弹背心", "price": 3.0, "desc": "基础防护"}],
     "helmets": [{"name": "破损五级头", "price": 6.0, "desc": "高战备值，性价比极高"}],
     "backpacks": [{"name": "GIR野战胸挂", "price": 5.0, "desc": "超大容量"}],
     "features": "凑战备门槛的神器，总价低，战备值高。", "hotScore": 91},
    {"name": "MP5·经典平民猛攻", "scenario": "猛攻", "map": ["大坝", "航天基地", "巴克什"],
     "weapons": [{"name": "MP5冲锋枪", "price": 11.5, "desc": "20米内腰射精准", "code": "MP5冲锋枪-烽火地带-6ICCO940FCDV4UPACJK76"},
                {"name": "G18C手枪", "price": 10.6, "desc": "近战补枪神器", "code": ""}],
     "armors": [{"name": "DT-AVS防弹衣", "price": 15.0, "desc": "四级甲，绝密模式可用"}],
     "helmets": [{"name": "MHS战术头盔", "price": 10.0, "desc": "四级头，拾音+30%"}],
     "backpacks": [{"name": "GIR野战胸挂", "price": 5.0, "desc": "经典胸挂"}],
     "features": "经典平民猛攻组合，主副武器搭配，适应多种交战距离。", "hotScore": 93},
    {"name": "MCX LT·零后坐力激光枪", "scenario": "绝密", "map": ["航天基地", "巴克什"],
     "weapons": [{"name": "MCX LT突击步枪", "price": 30.0, "desc": "零后坐力激光枪", "code": "MCX LT突击步枪-烽火地带-6J0DPQ0092SAL51E9I4V4"}],
     "armors": [{"name": "四级甲", "price": 18.0, "desc": "绝密门槛"}],
     "helmets": [{"name": "四级头", "price": 10.0, "desc": "必备"}],
     "backpacks": [{"name": "GIR野战胸挂", "price": 5.0, "desc": "摸金必备"}],
     "features": "30万打造T0级体验，指哪打哪，平民战神。", "hotScore": 90},
    {"name": "腾龙·18万S级强度", "scenario": "通用", "map": ["大坝", "长弓溪谷", "航天基地", "巴克什"],
     "weapons": [{"name": "腾龙突击步枪", "price": 18.0, "desc": "18万玩到S级中上游", "code": "6IL87QG013CE082VBOHIS"}],
     "armors": [{"name": "三级甲", "price": 5.0, "desc": "过渡使用"}],
     "helmets": [{"name": "三级头", "price": 4.0, "desc": "基础防护"}],
     "backpacks": [{"name": "强袭战术背心", "price": 3.0, "desc": "性价比之选"}],
     "features": "版本答案，极低成本获得S级强度，无后座体验。", "hotScore": 98},
]

def generate_budget_loadouts_json():
    final_loadouts = []
    for tpl in BUDGET_LOADOUT_TEMPLATES:
        total = 0
        for w in tpl["weapons"]:
            total += w["price"]
        for a in tpl["armors"]:
            if a["name"] in ARMOR_PRICE_BASE:
                a["price"] = ARMOR_PRICE_BASE[a["name"]]
            total += a["price"]
        for h in tpl["helmets"]:
            if h["name"] in HELMET_PRICE_BASE:
                h["price"] = HELMET_PRICE_BASE[h["name"]]
            total += h["price"]
        for b in tpl["backpacks"]:
            if b["name"] in BACKPACK_PRICE_BASE:
                b["price"] = BACKPACK_PRICE_BASE[b["name"]]
            total += b["price"]
        loadout = tpl.copy()
        loadout["totalPrice"] = round(total, 1)
        loadout["updateTime"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        final_loadouts.append(loadout)
    final_loadouts.sort(key=lambda x: x["hotScore"], reverse=True)
    return final_loadouts

# ==================== 6. 主函数 ====================
def main():
    print("🚀 开始执行全自动改枪码更新任务...")
    print("=" * 50)
    online_codes = fetch_all_codes()
    if len(online_codes) < 5:
        final_codes = online_codes + DEFAULT_CODES
    elif not online_codes:
        final_codes = DEFAULT_CODES
    else:
        final_codes = online_codes + DEFAULT_CODES[:5]
    seen = set()
    unique_final = []
    for item in final_codes:
        if item["code"] not in seen:
            seen.add(item["code"])
            if "price" not in item or item["price"] is None:
                price_from_name = extract_price(item.get("name", ""))
                item["price"] = price_from_name if price_from_name else "暂无报价"
            unique_final.append(item)
    with open("codes.json", "w", encoding="utf-8") as f:
        json.dump(unique_final, f, ensure_ascii=False, indent=2)
    print("=" * 50)
    print(f"🎉 数据已成功写入 codes.json，共 {len(unique_final)} 条")
    class_count = {}
    price_count = 0
    for item in unique_final:
        cls = item.get("class", "全能")
        class_count[cls] = class_count.get(cls, 0) + 1
        if item.get("price") and item["price"] != "暂无报价":
            price_count += 1
    print(f"📈 兵种分布: {class_count}")
    print(f"💰 含价格数据: {price_count}/{len(unique_final)} 条")

    # 生成起装方案 JSON
    print("\n📦 开始生成起装方案 JSON...")
    budget_data = generate_budget_loadouts_json()
    with open("budget_loadouts.json", "w", encoding="utf-8") as f:
        json.dump(budget_data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已生成 budget_loadouts.json，共 {len(budget_data)} 个方案")

if __name__ == "__main__":
    main()
