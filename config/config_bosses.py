"""
config_bosses.py
定义 Boss 的阶级、单人/多人变体以及掉落表。
"""
from .config_globals import ATTRIBUTES, TIERS

# --- 1. Boss 模板数据 ---
# 定义每个阶级(Tier)的数值强度
# Solo: 适合单刷，掉基础材料
# Multi: 必须组队，掉进化材料
BOSS_STATS_TEMPLATE = {
    1: {"solo_hp": 50,   "solo_dmg": 5,  "multi_hp": 500,   "multi_dmg": 10},
    2: {"solo_hp": 150,  "solo_dmg": 15, "multi_hp": 1500,  "multi_dmg": 25},
    3: {"solo_hp": 400,  "solo_dmg": 30, "multi_hp": 4000,  "multi_dmg": 50},
    4: {"solo_hp": 1000, "solo_dmg": 60, "multi_hp": 10000, "multi_dmg": 100},
    5: {"multi_hp": 50000, "multi_dmg": 200} # T5 只有多人
}

# --- 2. 动态生成 Boss 数据字典 ---
# 格式: "T1_fire_solo": {hp, attr, type, tier, dmg}
BOSS_DATA = {}

for tier in TIERS:
    stats = BOSS_STATS_TEMPLATE[tier]
    
    # Tier 5 特殊处理 (只有最终 Boss)
    if tier == 5:
        name = "T5_final_multi"
        BOSS_DATA[name] = {
            "hp": stats["multi_hp"], 
            "dmg": stats["multi_dmg"],
            "attr": "none", # 无属性
            "type": "multi",
            "tier": 5
        }
        continue

    # Tier 1-4 生成所有属性的 Solo 和 Multi
    for attr in ATTRIBUTES:
        # Solo Variant
        solo_name = f"T{tier}_{attr}_solo"
        BOSS_DATA[solo_name] = {
            "hp": stats["solo_hp"],
            "dmg": stats["solo_dmg"],
            "attr": attr,
            "type": "solo",
            "tier": tier
        }
        
        # Multi Variant
        multi_name = f"T{tier}_{attr}_multi"
        BOSS_DATA[multi_name] = {
            "hp": stats["multi_hp"],
            "dmg": stats["multi_dmg"],
            "attr": attr,
            "type": "multi",
            "tier": tier
        }

# 为了方便 Gym Space 定义，提取名字列表
BOSS_NAMES = list(BOSS_DATA.keys())

# --- 3. 掉落规则 (LOOT) ---
# 简化配置：Solo 掉 stone, Multi 掉 essence/evolution
def get_loot_table(boss_name):
    """根据 Boss 名字返回掉落配置"""
    data = BOSS_DATA[boss_name]
    tier = data["tier"]
    b_type = data["type"]
    attr = data["attr"]
    
    loot = []
    
    if b_type == "solo":
        # Solo: 必掉 common_stone, 概率掉属性石
        loot.append(("common_stone", 1.0, tier)) # Tier越高给的越多
        if attr != "none":
            loot.append((f"{attr}_stone", 0.5, 1))
            
    elif b_type == "multi":
        # Multi: 必掉 evolution_stone, 概率掉 essence
        loot.append(("evolution_stone", 1.0, 1))
        loot.append(("gold", 1.0, 100 * tier))
        if attr != "none":
            loot.append((f"{attr}_essence", 0.8, 1)) # 高概率
            
    # T5 Final Boss 掉落大量稀有物
    if tier == 5:
        loot = [("evolution_stone", 1.0, 10), ("gold", 1.0, 10000)]
        
    return loot