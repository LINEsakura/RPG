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

# --- 2. 属性克制 ---
# 攻击者属性 -> {被攻击者属性: 伤害倍率}
ATTR_MATRIX = {
    "fire":  {"fire": 1.0, "water": 0.5, "earth": 1.5, "wind": 1.0, "light": 1.0, "none": 1.0},
    "water": {"fire": 1.5, "water": 1.0, "earth": 0.5, "wind": 1.0, "light": 1.0, "none": 1.0},
    "earth": {"fire": 0.5, "water": 1.5, "earth": 1.0, "wind": 1.0, "light": 1.0, "none": 1.0},
    "wind":  {"fire": 1.0, "water": 1.0, "earth": 1.0, "wind": 1.0, "light": 1.0, "none": 1.0},
    "light": {"fire": 1.0, "water": 1.0, "earth": 1.0, "wind": 1.0, "light": 1.0, "none": 1.0},
    "none":  {"fire": 1.0, "water": 1.0, "earth": 1.0, "wind": 1.0, "light": 1.0, "none": 1.0},
}

# --- 3. 武器升级 ---
# {等级: {所需材料: 数量}}
UPGRADE_COSTS = {
    1: {"common_stone": 10}, 
    2: {"attribute_stone": 5}, 
    3: {"attribute_stone": 10},
    4: {"attribute_stone": 20},
    5: {"attribute_stone": 50},
}

# --- 4. 武器升级伤害 ---
# {等级: 额外伤害}
UPGRADE_DAMAGE = {
    0: 0,  # 0 级 (没武器)
    1: 5,  # 1 级
    2: 10, # 2 级
    3: 15,
    4: 30,
    5: 50, # 5 级
}