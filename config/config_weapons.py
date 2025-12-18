"""
武器配置文件
只定义武器的属性、克制关系和升级配方。
"""
from .config_globals import ATTRIBUTES, MAX_WEAPON_LEVEL

# --- 1. 武器数据 ---
# (名字, 基础伤害, 属性)
WEAPON_DATA = {
    "fire_sword": (10, "fire"),
    "water_sword": (10, "water"),
    "earth_sword": (10, "earth"),
    "wind_sword": (10, "wind"),
    "light_sword": (10, "light"),
}

# --- 2. 属性克制矩阵 ---
# 攻击者属性 -> {被攻击者属性: 伤害倍率}
ATTR_MATRIX = {
    "fire":  {"fire": 1.0, "water": 0.5, "earth": 1.5, "wind": 1.0, "light": 1.0, "none": 1.0},
    "water": {"fire": 1.5, "water": 1.0, "earth": 0.5, "wind": 1.0, "light": 1.0, "none": 1.0},
    "earth": {"fire": 0.5, "water": 1.5, "earth": 1.0, "wind": 1.0, "light": 1.0, "none": 1.0},
    "wind":  {"fire": 1.0, "water": 1.0, "earth": 1.0, "wind": 1.0, "light": 1.0, "none": 1.0},
    "light": {"fire": 1.0, "water": 1.0, "earth": 1.0, "wind": 1.0, "light": 1.0, "none": 1.0},
    "none":  {"fire": 1.0, "water": 1.0, "earth": 1.0, "wind": 1.0, "light": 1.0, "none": 1.0},
}

# --- 3. 升级消耗 (Tier Up Cost) ---
# 这是一个阶梯式消耗，Tier 越高需要的材料越稀有
TIER_UP_COSTS = {
    # 升到 Tier 2 (需要基础石)
    2: {"common_stone": 10, "gold": 100}, 
    # 升到 Tier 3 (需要属性石 - Solo Boss掉落)
    3: {"common_stone": 20, "specific_stone": 5, "gold": 500},
    # 升到 Tier 4 (需要进化石 - Multi Boss掉落)
    4: {"evolution_stone": 2, "specific_essence": 2, "gold": 2000},
    # 升到 Tier 5 (决战兵器)
    5: {"evolution_stone": 10, "specific_essence": 10, "gold": 10000},
}

# --- 4. 武器升级伤害 ---
# {等级: 额外伤害}
UPGRADE_DAMAGE = {
    0: 0,  # 0 级 (没武器)
    1: 2,  # 1 级
    2: 4, # 2 级
    3: 8,
    4: 10,
    5: 15, # 5 级
}