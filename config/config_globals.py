# --- 2. 材料 ---
# (从 ATTRIBUTES 动态生成)
STONE_NAMES = [f"{attr}_stone" for attr in ATTRIBUTES] + ["common_stone"]

# --- 3. 模拟设置 ---
AGENT_MAX_STEPS = 3000



"""
config_globals.py
定义全局共享的基础常量。
"""

# --- 1. 基础属性 ---
ATTRIBUTES = ["fire", "water", "earth", "wind", "light"]
TIERS = [1, 2, 3, 4, 5]  # 5个阶级
AGENT_MAX_HEALTH = 100

# --- 2. 物品定义 ---
# 基础材料 (Solo Boss 掉落)
BASIC_STONES = [f"{attr}_stone" for attr in ATTRIBUTES] + ["common_stone"]

# 进阶材料 (Multi Boss 掉落，用于突破阶级)
EVO_STONES = [f"{attr}_essence" for attr in ATTRIBUTES] + ["evolution_stone"]

# 汇总所有物品
ALL_ITEMS = BASIC_STONES + EVO_STONES + ["gold"]

# --- 3. 初始状态 ---
INITIAL_GOLD = 100

# --- 4. 模拟设置 ---
MAX_STEPS = 500