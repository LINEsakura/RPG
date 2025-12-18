# config_shop.py
from .config_globals import BASIC_STONES, EVO_STONES

# 1. 商店直接售卖物品 (金币回收机制)
# 设定：商店只卖基础材料，高级材料(Evo)卖得极贵，逼迫玩家去打Boss
SHOP_PRICES = {
    "common_stone": 50,
    "fire_stone": 200,
    "water_stone": 200,
    "earth_stone": 200,
    "wind_stone": 200,
    "light_stone": 200,
    "evolution_stone": 5000, # 天价，鼓励社交/打Boss
}

# 2. 拍卖行允许交易的物品及建议起拍价
TRADEABLE_ITEMS = BASIC_STONES + EVO_STONES
BASE_MARKET_PRICES = SHOP_PRICES.copy()

# 补充高级材料的建议基准价
for item in EVO_STONES:
    if item not in BASE_MARKET_PRICES:
        BASE_MARKET_PRICES[item] = 1000

# 3. PvP 奖励
PVP_REWARD_GOLD = 300