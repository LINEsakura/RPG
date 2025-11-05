"""
全局常量 (Globals Config)
定义被 Bosses 和 Weapons 共享的基础数据。
"""

# --- 1. 基础属性 ---
ATTRIBUTES = ["fire", "water", "earth", "wind", "light"]
AGENT_MAX_HEALTH = 100
MAX_WEAPON_LEVEL = 5

# --- 2. 材料 ---
# (从 ATTRIBUTES 动态生成)
STONE_NAMES = [f"{attr}_stone" for attr in ATTRIBUTES] + ["common_stone"]