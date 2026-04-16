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
# 根据萌娘百科和游戏内数据整理的枪械→兵种映射
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

# 枪械名称别名（处理不同写法）
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
    { "name": "M4A1 高稳突击", "weapon": "M4A1", "class": "突击", 
      "attachments": "垂直握把 + 消音器 + 红点", 
      "code": "M4A1突击步枪-烽火地带-6IUKUN40FGIGGAT87VQQ3" },
    { "name": "AKM 暴力输出", "weapon": "AKM", "class": "突击", 
      "attachments": "补偿器 + 轻机枪托 + 全息", 
      "code": "AKM突击步枪-烽火地带-7JVLKP50GHKPH2BT98WR4" },
    { "name": "Vector 近战速射", "weapon": "Vector", "class": "侦察", 
      "attachments": "激光 + 扩容弹匣 + 消音", 
      "code": "VECTOR-烽火地带-3LJSND72KSL92JD7G3H4" },
    { "name": "PTR-32 满改激光枪", "weapon": "PTR-32", "class": "突击",
      "attachments": "钛金制退器 + 密令斜角握把 + 影袭枪托",
      "code": "PTR-32突击步枪-全面战场-6EIAKTC02U9HU6AC38CQJ" },
    { "name": "K416 均衡配置", "weapon": "K416", "class": "突击",
      "attachments": "堡垒水平 + 红激光 + 稳固枪托",
      "code": "K416突击步枪-全面战场-6EIALPC02U9HU6AC38CQJ" },
    { "name": "M14 射手步枪", "weapon": "M14", "class": "支援",
      "attachments": "70W战备满改",
      "code": "M14射手步枪-烽火地带-6HC9EHC0ECHLI3RNV6CKS" },
]

# ==================== 4. 正则表达式 ====================
# 匹配格式: 枪械名-模式-代码
# 例如: "PTR-32突击步枪-全面战场-6EIAKTC02U9HU6AC38CQJ"
FULL_CODE_PATTERN = re.compile(
    r"([A-Za-z0-9\u4e00-\u9fff\-\.\s]+?)"  # 枪械名 (允许中文、字母、数字、横杠、空格)
    r"[-—]"                                 # 分隔符
    r"([全面战场|烽火地带]+)"                # 模式
    r"[-—]"                                 # 分隔符
    r"([A-Z0-9]{12,})",                     # 代码 (至少12位大写字母+数字)
    re.IGNORECASE
)

# 备用: 单独匹配代码 (当上面的格式匹配不到时使用)
CODE_ONLY_PATTERN = re.compile(r"[A-Z0-9]{12,}")


# ==================== 5. 根据枪械名判断兵种 ====================
def get_weapon_class(weapon_name):
    """根据枪械名称判断兵种"""
    if not weapon_name:
        return "全能"
    
    weapon_upper = weapon_name.upper()
    
    # 先检查别名
    for alias, full_name in WEAPON_ALIASES.items():
        if alias.upper() in weapon_upper:
            weapon_name = full_name
            break
    
    # 检查映射表
    for key, cls in WEAPON_CLASS_MAP.items():
        if key.upper() in weapon_upper:
            return cls
    
    # 根据名称特征推断
    if any(x in weapon_name for x in ["冲锋", "MP", "UZI", "Vector", "P90", "SMG"]):
        return "侦察"
    elif any(x in weapon_name for x in ["狙击", "射手", "SR", "M14", "AWM", "PKM", "M249"]):
        return "支援"
    elif any(x in weapon_name for x in ["霰弹", "S12K", "M1014"]):
        return "工程"
    elif any(x in weapon_name for x in ["突击", "步枪", "AR", "AK", "M4", "K416", "SCAR"]):
        return "突击"
    
    return "全能"


# ==================== 6. 提取配装名称 ====================
def extract_loadout_name(text_before_code, weapon_name):
    """根据上下文生成配装名称"""
    text = text_before_code.lower()
    
    if "满改" in text or "满配" in text:
        return f"{weapon_name} 满改方案"
    elif "半改" in text:
        return f"{weapon_name} 半改方案"
    elif "低改" in text or "省钱" in text:
        return f"{weapon_name} 省钱低改"
    elif "腰射" in text:
        return f"{weapon_name} 腰射流"
    elif "稳" in text or "压枪" in text:
        return f"{weapon_name} 高稳压枪"
    elif "主播" in text or "自用" in text:
        return f"{weapon_name} 主播自用"
    else:
        return f"{weapon_name} 推荐配装"


# ==================== 7. 核心抓取函数 ====================
def fetch_all_codes():
    all_codes = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for url in TARGET_URLS:
        try:
            print(f"🌐 正在抓取: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 获取整个页面的文本
            page_text = soup.get_text()
            
            # 方法1: 匹配完整格式 "枪名-模式-代码"
            matches = FULL_CODE_PATTERN.findall(page_text)
            
            if matches:
                print(f"   ✅ 匹配到 {len(matches)} 个完整格式的改枪码")
                for weapon_part, mode, code in matches:
                    # 清理枪械名
                    weapon_name = weapon_part.strip()
                    # 去掉可能多余的空格和横杠
                    weapon_name = re.sub(r"\s+", " ", weapon_name)
                    
                    # 判断兵种
                    weapon_class = get_weapon_class(weapon_name)
                    
                    # 尝试提取配件信息（从码附近的文本中）
                    attachments = "热门配件"
                    code_pos = page_text.find(code)
                    if code_pos > 0:
                        context = page_text[max(0, code_pos-200):code_pos]
                        if "配件" in context or "搭配" in context:
                            attachments = "详见原文"
                    
                    all_codes.append({
                        "name": f"{weapon_name} 配装方案",
                        "weapon": weapon_name,
                        "class": weapon_class,
                        "attachments": attachments,
                        "code": code
                    })
            else:
                # 方法2: 只匹配代码，然后尝试从上下文推断枪名
                raw_codes = CODE_ONLY_PATTERN.findall(page_text)
                print(f"   ⚠️ 未匹配到完整格式，找到 {len(set(raw_codes))} 个代码")
                
                for code in set(raw_codes):
                    # 尝试从代码附近的文本推断枪名
                    code_pos = page_text.find(code)
                    context = page_text[max(0, code_pos-150):code_pos]
                    
                    weapon_name = "未知枪械"
                    # 尝试从上下文中找枪名
                    for key in WEAPON_CLASS_MAP.keys():
                        if key.upper() in context.upper():
                            weapon_name = key
                            break
                    
                    weapon_class = get_weapon_class(weapon_name)
                    
                    all_codes.append({
                        "name": f"{weapon_name} 热门配装" if weapon_name != "未知枪械" else "网络热门方案",
                        "weapon": weapon_name,
                        "class": weapon_class,
                        "attachments": "全网实时热门改枪码",
                        "code": code
                    })
            
            # 随机延时
            time.sleep(random.uniform(1, 3))
            
        except Exception as e:
            print(f"   ❌ 抓取失败 {url}: {e}")

    # 去重 (基于code)
    unique_codes = []
    seen = set()
    for item in all_codes:
        if item["code"] not in seen:
            seen.add(item["code"])
            unique_codes.append(item)
    
    print(f"\n📊 共获取 {len(unique_codes)} 个有效改枪码")
    return unique_codes


# ==================== 8. 主函数 ====================
def main():
    print("🚀 开始执行全自动改枪码更新任务...")
    print("=" * 50)
    
    online_codes = fetch_all_codes()
    
    # 如果在线获取的数据太少，补充默认数据
    if len(online_codes) < 3:
        print("⚠️ 在线数据较少，补充默认数据")
        final_codes = online_codes + DEFAULT_CODES
    elif not online_codes:
        print("⚠️ 网络获取失败，使用兜底数据")
        final_codes = DEFAULT_CODES
    else:
        final_codes = online_codes
    
    # 再次去重
    seen = set()
    unique_final = []
    for item in final_codes:
        if item["code"] not in seen:
            seen.add(item["code"])
            unique_final.append(item)
    
    # 写入文件
    with open("codes.json", "w", encoding="utf-8") as f:
        json.dump(unique_final, f, ensure_ascii=False, indent=2)
    
    print("=" * 50)
    print(f"🎉 数据已成功写入 codes.json，共 {len(unique_final)} 条")
    
    # 打印统计
    class_count = {}
    for item in unique_final:
        cls = item.get("class", "全能")
        class_count[cls] = class_count.get(cls, 0) + 1
    print(f"📈 兵种分布: {class_count}")


if __name__ == "__main__":
    main()
