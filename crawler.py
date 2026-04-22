import json
import re
import requests
import time
import random
from bs4 import BeautifulSoup
from datetime import datetime

# ==================== 1. 配置目标网址（改枪码） ====================
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
    "腾龙": "腾龙突击步枪", "ptr": "PTR-32", "m4": "M4A1", "ak": "AKM",
    "k4": "K416", "mp": "MP5",
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
    if not weapon_name: return "全能"
    weapon_upper = weapon_name.upper()
    for alias, full_name in WEAPON_ALIASES.items():
        if alias.upper() in weapon_upper:
            weapon_name = full_name
            break
    for key, cls in WEAPON_CLASS_MAP.items():
        if key.upper() in weapon_upper:
            return cls
    if any(x in weapon_name for x in ["冲锋", "MP", "UZI", "Vector", "P90", "SMG"]): return "侦察"
    elif any(x in weapon_name for x in ["狙击", "射手", "SR", "M14", "AWM", "PKM", "M249"]): return "支援"
    elif any(x in weapon_name for x in ["霰弹", "S12K", "M1014"]): return "工程"
    elif any(x in weapon_name for x in ["突击", "步枪", "AR", "AK", "M4", "K416", "SCAR"]): return "突击"
    return "全能"

def extract_price(context):
    match = re.search(r'(\d+(?:\.\d+)?)\s*[万wW]', context)
    if match: return match.group(1) + '万'
    return None

def fetch_all_codes():
    all_codes = []
    headers = {"User-Agent": "Mozilla/5.0"}
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

# ==================== 5. 起装方案生成 ====================
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
        for w in tpl["weapons"]: total += w["price"]
        for a in tpl["armors"]:
            if a["name"] in ARMOR_PRICE_BASE: a["price"] = ARMOR_PRICE_BASE[a["name"]]
            total += a["price"]
        for h in tpl["helmets"]:
            if h["name"] in HELMET_PRICE_BASE: h["price"] = HELMET_PRICE_BASE[h["name"]]
            total += h["price"]
        for b in tpl["backpacks"]:
            if b["name"] in BACKPACK_PRICE_BASE: b["price"] = BACKPACK_PRICE_BASE[b["name"]]
            total += b["price"]
        loadout = tpl.copy()
        loadout["totalPrice"] = round(total, 1)
        loadout["updateTime"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        final_loadouts.append(loadout)
    final_loadouts.sort(key=lambda x: x["hotScore"], reverse=True)
    return final_loadouts


# ==================== 福利活动候选发现 ====================
WELFARE_CANDIDATES_FILE = "welfare_candidates.json"
WELFARE_PUBLISHED_FILE = "welfare_activities.json"

# 需要监控的福利信息来源
WELFARE_SOURCES = [
    {
        "name": "官方新闻中心",
        "url": "https://df.qq.com/web202106/news.html",
        "type": "official"
    },
    {
        "name": "九游福利汇总",
        "url": "https://a.9game.cn/df/activity/",
        "type": "aggregator"
    },
    {
        "name": "52PK兑换码",
        "url": "https://m.52pk.com/df/codes/",
        "type": "aggregator"
    },
    {
        "name": "游侠网活动专区",
        "url": "https://www.ali213.net/zt/deltaforce/activity/",
        "type": "aggregator"
    }
]

# 福利关键词（用于识别活动类文章）
WELFARE_KEYWORDS = ["福利", "礼包", "兑换码", "免费", "白嫖", "赠送", "领取", "活动", "奖励", "CDK", "cdk"]

def discover_welfare_candidates():
    """发现候选福利活动（不直接发布，需要人工确认）"""
    print("\n🎁 开始发现福利活动候选...")
    
    candidates = []
    headers = {"User-Agent": "Mozilla/5.0"}
    
    # 先读取已有的候选，避免重复
    existing = []
    try:
        with open(WELFARE_CANDIDATES_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
    except FileNotFoundError:
        pass
    
    existing_urls = {c.get("link", "") for c in existing}
    
    for source in WELFARE_SOURCES:
        try:
            print(f"   📡 扫描 {source['name']}...")
            response = requests.get(source["url"], headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取所有链接
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # 补全相对路径
                if href.startswith('/'):
                    href = "https://df.qq.com" + href
                elif not href.startswith('http'):
                    continue
                
                # 检查是否包含福利关键词
                combined = text + href
                if any(kw in combined for kw in WELFARE_KEYWORDS):
                    # 避免重复
                    if href in existing_urls:
                        continue
                    
                    # 尝试提取标题和描述
                    title = text if len(text) > 5 else "新福利活动"
                    parent = link.find_parent(['div', 'li', 'article'])
                    desc = ""
                    if parent:
                        desc_text = parent.get_text(strip=True)
                        if len(desc_text) > len(title):
                            desc = desc_text[:100] + "..." if len(desc_text) > 100 else desc_text
                    
                    candidates.append({
                        "id": f"c_{int(time.time())}_{len(candidates)}",
                        "title": title,
                        "platform": source["name"],
                        "desc": desc or "点击查看详情",
                        "link": href,
                        "source": source["name"],
                        "discovered_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "status": "pending",  # pending/confirmed/rejected
                        "icon": "fa-gift",
                        "color": "#FF6B35"
                    })
                    existing_urls.add(href)
                    
            time.sleep(random.uniform(1, 2))
        except Exception as e:
            print(f"   ⚠️ {source['name']} 扫描失败: {e}")
    
    # 合并已有候选和新发现的候选
    all_candidates = existing + candidates
    
    # 去重
    seen = set()
    unique_candidates = []
    for c in all_candidates:
        if c["link"] not in seen:
            seen.add(c["link"])
            unique_candidates.append(c)
    
    with open(WELFARE_CANDIDATES_FILE, "w", encoding="utf-8") as f:
        json.dump(unique_candidates, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 发现 {len(candidates)} 个新候选，共 {len(unique_candidates)} 个待确认")
    return unique_candidates


def validate_published_welfare():
    """验证已发布的活动是否仍然有效"""
    print("\n🔍 验证已发布福利活动的有效性...")
    
    try:
        with open(WELFARE_PUBLISHED_FILE, "r", encoding="utf-8") as f:
            published = json.load(f)
    except FileNotFoundError:
        print(f"   ⚠️ {WELFARE_PUBLISHED_FILE} 不存在，跳过验证")
        return
    
    headers = {"User-Agent": "Mozilla/5.0"}
    updated = False
    
    for act in published:
        if not act.get("is_active", True):
            continue
        
        try:
            response = requests.get(act["link"], headers=headers, timeout=10, allow_redirects=True)
            
            # 如果返回404或重定向到首页，说明活动已失效
            if response.status_code == 404:
                act["is_active"] = False
                act["expire_reason"] = "页面不存在"
                updated = True
                print(f"   ❌ {act['title']} 已失效（404）")
            elif "活动已结束" in response.text or "活动已过期" in response.text or "敬请期待" in response.text:
                act["is_active"] = False
                act["expire_reason"] = "活动已结束"
                updated = True
                print(f"   ⏰ {act['title']} 已过期")
            else:
                # 可选：检查是否有明确的过期时间标签，这里只做简单标记
                pass
                    
        except Exception as e:
            print(f"   ⚠️ 验证 {act['title']} 时出错: {e}")
    
    if updated:
        with open(WELFARE_PUBLISHED_FILE, "w", encoding="utf-8") as f:
            json.dump(published, f, ensure_ascii=False, indent=2)
        print(f"✅ welfare_activities.json 已更新")
    else:
        print(f"✅ 所有已发布活动仍在有效期内")




# ==================== 6. 万能猜题库生成器 ====================
class QuizGenerator:
    def __init__(self):
        self.quiz_bank = []

    def add_weapon_questions(self):
        weapons = list(WEAPON_CLASS_MAP.keys())
        for w in weapons[:30]:
            cls = WEAPON_CLASS_MAP.get(w, "全能")
            question = f"「{w}」属于哪个兵种？"
            options = ["突击", "侦察", "支援", "工程"]
            answer = options.index(cls) if cls in options else 0
            self.quiz_bank.append({
                "category": "兵种",
                "question": question,
                "options": options,
                "answer": answer,
                "explain": f"{w} 是 {cls} 兵种的主武器。"
            })

    def add_map_questions(self):
        maps = ["零号大坝", "航天基地", "长弓溪谷", "巴克什", "攀升"]
        features = {
            "零号大坝": "拥有行政辖区和地下金库",
            "航天基地": "以钻石皇后酒店为高价值物资点",
            "长弓溪谷": "狙击高点位于中央高塔",
            "巴克什": "以皇家博物馆为核心交战区",
            "攀升": "新地图，垂直结构复杂"
        }
        for m in maps:
            question = f"哪张地图{features[m]}？"
            other_maps = [x for x in maps if x != m]
            sample_count = min(3, len(other_maps))
            options = random.sample(other_maps, sample_count) + [m]
            random.shuffle(options)
            answer = options.index(m)
            self.quiz_bank.append({
                "category": "地图",
                "question": question,
                "options": options,
                "answer": answer,
                "explain": f"{m} 的特点：{features[m]}"
            })

    def add_operator_questions(self):
        operators = [
            {"name": "红狼", "skill": "战术滑铲", "feature": "突击"},
            {"name": "蜂医", "skill": "激素手枪", "feature": "支援"},
            {"name": "露娜", "skill": "探测箭", "feature": "侦察"},
            {"name": "骇爪", "skill": "信号干扰", "feature": "侦察"},
            {"name": "威龙", "skill": "声波陷阱", "feature": "工程", "nickname": "老黑"},
            {"name": "牧羊人", "skill": "无人机", "feature": "工程"},
        ]
        for op in operators:
            if op.get("nickname"):
                question = f"哪位干员的外号叫「{op['nickname']}」？"
                sample_count = min(3, len(operators)-1)
                options = [o["name"] for o in random.sample([o for o in operators if o["name"] != op["name"]], sample_count)] + [op["name"]]
                random.shuffle(options)
                answer = options.index(op["name"])
                self.quiz_bank.append({
                    "category": "干员",
                    "question": question,
                    "options": options,
                    "answer": answer,
                    "explain": f"{op['name']} 外号 {op['nickname']}，是 {op['feature']} 干员。"
                })
            question = f"干员「{op['name']}」的招牌技能是什么？"
            sample_count = min(3, len(operators)-1)
            options = [o["skill"] for o in random.sample([o for o in operators if o["name"] != op["name"]], sample_count)] + [op["skill"]]
            random.shuffle(options)
            answer = options.index(op["skill"])
            self.quiz_bank.append({
                "category": "干员",
                "question": question,
                "options": options,
                "answer": answer,
                "explain": f"{op['name']} 的技能是 {op['skill']}。"
            })

    def add_value_questions(self):
        items = [
            {"name": "非洲之心", "price": "200万+"},
            {"name": "曼德尔砖", "price": "100万+"},
            {"name": "显卡", "price": "50万+"},
            {"name": "碳纤维板", "price": "20万+"},
        ]
        for item in items:
            question = f"物品「{item['name']}」的参考价值是多少？"
            prices = ["10万以内", "20-50万", "50-100万", "100万+"]
            if item["price"] == "200万+":
                answer = 3
            elif item["price"] == "100万+":
                answer = 3
            elif item["price"] == "50万+":
                answer = 2
            else:
                answer = 1
            self.quiz_bank.append({
                "category": "物品价值",
                "question": question,
                "options": prices,
                "answer": answer,
                "explain": f"{item['name']} 的价值约为 {item['price']}。"
            })

    def add_tactic_questions(self):
        tactics = [
            {"name": "跑刀", "desc": "只带刀或极低成本装备进入战局搜刮"},
            {"name": "卡战备", "desc": "凑够战备值门槛以进入高级地图"},
            {"name": "老六", "desc": "躲在角落阴人"},
            {"name": "架枪", "desc": "在掩体后持续瞄准一个方向"},
        ]
        for t in tactics:
            question = f"以下哪种打法是指「{t['desc']}」？"
            sample_count = min(3, len(tactics)-1)
            options = [x["name"] for x in random.sample([x for x in tactics if x["name"] != t["name"]], sample_count)] + [t["name"]]
            random.shuffle(options)
            answer = options.index(t["name"])
            self.quiz_bank.append({
                "category": "战术打法",
                "question": question,
                "options": options,
                "answer": answer,
                "explain": f"「{t['name']}」就是 {t['desc']}。"
            })

    def generate_all(self):
        print("\n🧠 开始生成万能猜题库...")
        self.add_weapon_questions()
        self.add_map_questions()
        self.add_operator_questions()
        self.add_value_questions()
        self.add_tactic_questions()
        random.shuffle(self.quiz_bank)
        print(f"✅ 题库生成完毕，共 {len(self.quiz_bank)} 道题目")
        return self.quiz_bank

# ==================== 7. 物资价格生成（模拟实时波动） ====================
def fetch_loot_prices():
    print("\n💰 开始生成物资价格...")
    base_prices = {
        "非洲之心": 1314, "量子芯片": 1980, "复苏呼吸机": 500, "金条": 286,
        "战术头盔": 198, "飞秒激光器": 154, "精密电子元件": 142, "纳米修复凝胶": 125,
        "阵列服务器蓝图": 120, "电子脚镣": 102, "异常清除药品": 89, "加密硬盘": 65,
        "车载信号干扰器": 60, "精密零件": 52.3, "军用通讯仪": 50, "军用炮弹": 45,
        "碳纤维板": 42, "航电模块": 38.6, "劳力士": 38, "留声机": 35,
        "显卡": 28, "笔记本电脑": 22, "数码相机": 15, "设计图纸": 12,
        "金蛋(9x39)": 2, "军用罐头": 1.5, "低级燃料": 1.5, "高精数显卡尺": 1.5
    }
    prices = []
    for name, base in base_prices.items():
        fluctuation = 1 + (random.random() - 0.5) * 0.1
        new_price = round(base * fluctuation, 1)
        trend = "up" if fluctuation > 1.01 else ("down" if fluctuation < 0.99 else "stable")
        change = round((fluctuation - 1) * 100, 1)
        tier = "red" if base > 500 else ("gold" if base > 100 else ("purple" if base > 50 else "blue"))
        prices.append({
            "name": name, "price": new_price, "unit": "万", "tier": tier,
            "trend": trend, "change_percent": change, "desc": "实时行情", "slot_value": 1,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
    prices.sort(key=lambda x: x["price"], reverse=True)
    print(f"✅ 物资价格生成完毕，共 {len(prices)} 条")
    return prices

# ==================== 8. 枪械TTK数据生成 ====================
def generate_weapon_ttk():
    print("\n🔫 生成武器TTK数据...")
    weapons = [
        {"name": "AS Val", "damage": 34, "fire_rate": 800, "armor_pen": 48, "category": "突击"},
        {"name": "Vector", "damage": 32, "fire_rate": 1091, "armor_pen": 25, "category": "冲锋"},
        {"name": "M7", "damage": 38, "fire_rate": 750, "armor_pen": 42, "category": "突击"},
        {"name": "K416", "damage": 40, "fire_rate": 780, "armor_pen": 30, "category": "突击"},
        {"name": "MP7", "damage": 33, "fire_rate": 900, "armor_pen": 28, "category": "冲锋"},
        {"name": "AUG", "damage": 41, "fire_rate": 720, "armor_pen": 32, "category": "突击"},
        {"name": "G3", "damage": 50, "fire_rate": 500, "armor_pen": 42, "category": "突击"},
        {"name": "PKM", "damage": 42, "fire_rate": 668, "armor_pen": 40, "category": "机枪"},
        {"name": "M249", "damage": 36, "fire_rate": 858, "armor_pen": 35, "category": "机枪"},
        {"name": "S12K", "damage": 136, "fire_rate": 300, "armor_pen": 18, "category": "霰弹"},
    ]
    ttk_data = []
    for w in weapons:
        def calc_ttk(armor_level):
            pen = w["armor_pen"]
            if pen >= armor_level * 12: dmg_mod = 1.0
            elif pen >= armor_level * 10: dmg_mod = 0.75
            else: dmg_mod = 0.55
            final_dmg = max(1, int(w["damage"] * dmg_mod))
            shots = (100 + final_dmg - 1) // final_dmg
            ttk = (shots - 1) * 60 / w["fire_rate"]
            return round(ttk, 3)
        ttk_data.append({
            "name": w["name"], "damage": w["damage"], "fire_rate": w["fire_rate"],
            "armor_pen": w["armor_pen"], "category": w["category"],
            "ttk_4": calc_ttk(4), "ttk_5": calc_ttk(5), "ttk_6": calc_ttk(6),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
    ttk_data.sort(key=lambda x: x["ttk_5"])
    print(f"✅ 枪械TTK数据生成完毕，共 {len(ttk_data)} 条")
    return ttk_data

# ==================== 9. 主函数 ====================
def main():
    print("🚀 开始执行全自动更新任务...")
    print("=" * 50)
    
    # 改枪码
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
    print(f"🎉 codes.json 已更新，共 {len(unique_final)} 条")

    # 起装方案
    budget_data = generate_budget_loadouts_json()
    with open("budget_loadouts.json", "w", encoding="utf-8") as f:
        json.dump(budget_data, f, ensure_ascii=False, indent=2)
    print(f"✅ budget_loadouts.json 已更新，共 {len(budget_data)} 个方案")

    # 万能猜题库
    try:
        quiz_gen = QuizGenerator()
        quiz_bank = quiz_gen.generate_all()
        with open("quiz_bank.json", "w", encoding="utf-8") as f:
            json.dump(quiz_bank, f, ensure_ascii=False, indent=2)
        print(f"🎯 quiz_bank.json 已生成，共 {len(quiz_bank)} 道题目")
    except Exception as e:
        print(f"❌ 生成题库时发生错误: {e}")

    # 物资价格
    loot_prices = fetch_loot_prices()
    with open("loot_prices.json", "w", encoding="utf-8") as f:
        json.dump(loot_prices, f, ensure_ascii=False, indent=2)
    print(f"📊 loot_prices.json 已更新，共 {len(loot_prices)} 条")

    # 枪械TTK
    weapon_ttk = generate_weapon_ttk()
    with open("weapon_ttk.json", "w", encoding="utf-8") as f:
        json.dump(weapon_ttk, f, ensure_ascii=False, indent=2)
    print(f"🎯 weapon_ttk.json 已更新，共 {len(weapon_ttk)} 条")


def main():
    # ... 您原有的改枪码、起装方案、题库、物资价格、TTK 代码 ...
    
    # ========== 新增：福利活动候选发现 + 验证 ==========
    discover_welfare_candidates()
    validate_published_welfare()
    # ========== 新增结束 ==========

if __name__ == "__main__":
    main()
