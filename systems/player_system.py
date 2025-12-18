import random
from config.config_globals import ALL_ITEMS, AGENT_MAX_HEALTH, INITIAL_GOLD
from config.config_weapons import WEAPON_NAMES, TIER_UP_COSTS

class PlayerSystem:
    def __init__(self, agents):
        self.agents = agents
        self.agent_data = {}

    def reset(self):
        self.agent_data = {}
        for agent in self.agents:
            self.agent_data[agent] = {
                "hp": AGENT_MAX_HEALTH,
                "gold": INITIAL_GOLD,
                "inventory": {i: 0 for i in ALL_ITEMS},
                "weapons": {w: 1 for w in WEAPON_NAMES}, # 默认 Tier 1
            }
            # 初始给点资源
            self.agent_data[agent]["inventory"]["common_stone"] = 5

    def get_data(self, agent):
        return self.agent_data[agent]

    def handle_upgrade(self, agent, weapon_name):
        """处理武器升阶逻辑"""
        data = self.agent_data[agent]
        curr_tier = data["weapons"][weapon_name]
        
        if curr_tier >= 5: return False # 已满级

        next_tier = curr_tier + 1
        costs = TIER_UP_COSTS.get(next_tier, {})
        
        # 1. 检查金币
        if data["gold"] < costs.get("gold", 0): return False

        # 2. 检查材料 (处理 specific_stone 动态命名)
        wep_attr = weapon_name.split("_")[0]
        real_costs = {}
        
        for mat, amt in costs.items():
            if mat == "gold": continue
            
            real_mat_name = mat
            if mat == "specific_stone": real_mat_name = f"{wep_attr}_stone"
            if mat == "specific_essence": real_mat_name = f"{wep_attr}_essence"
            
            real_costs[real_mat_name] = amt
            if data["inventory"].get(real_mat_name, 0) < amt:
                return False

        # 3. 扣除消耗并升级
        data["gold"] -= costs.get("gold", 0)
        for mat, amt in real_costs.items():
            data["inventory"][mat] -= amt
            
        data["weapons"][weapon_name] = next_tier
        print(f"[Upgrade] {agent} 将 {weapon_name} 提升至 Tier {next_tier}")
        return True