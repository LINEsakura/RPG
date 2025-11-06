"""
Boss 配置文件
只定义 Boss 的属性和掉落。
"""
# 导入全局常量，我们需要它来定义掉落
from .config_globals import ATTRIBUTES, STONE_NAMES

# --- 1. Boss 数据 ---
# (名字, 初始血量, 属性, 报复伤害)
BOSS_DATA = {
    "fire_boss": (10, "fire", 0),
    "water_boss": (10, "water", 0),
    "earth_boss": (10, "earth", 0),
    "wind_boss": (10, "wind", 0),
    "light_boss": (10, "light", 0),
    "final_boss": (100, "none", 10), 
}

# --- 2. 掉落表 ---
# 掉落表: Boss名字 -> [ (物品, 概率, 数量), ... ]
LOOT_TABLES = {
    "fire_boss":  [("common_stone", 1.0, 5), ("fire_stone", 1.0, 2)],
    "water_boss": [("common_stone", 1.0, 5), ("water_stone", 1.0, 2)],
    "earth_boss": [("common_stone", 1.0, 5), ("earth_stone", 1.0, 2)],
    "wind_boss":  [("common_stone", 1.0, 5), ("wind_stone", 1.0, 2)],
    "light_boss": [("common_stone", 1.0, 5), ("light_stone", 1.0, 2)],
    "final_boss": [("common_stone", 1.0, 50)],
}