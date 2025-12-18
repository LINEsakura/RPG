import random
from config.config_bosses import BOSS_DATA, BOSS_NAMES, get_loot_table
from config.config_weapons import BASE_DAMAGE, ATTR_MATRIX
from config.config_globals import AGENT_MAX_HEALTH

class CombatSystem:
    def __init__(self, agent_data_ref):
        # 引用 PlayerSystem 中的数据字典，以便直接扣血/发奖励
        self.agent_data = agent_data_ref
        self.multi_boss_states = {}
        self.solo_boss_states = {}

    def reset(self, agents):
        self.multi_boss_states = {}
        self.solo_boss_states = {a: {} for a in agents}
        
        for name in BOSS_NAMES:
            data = BOSS_DATA[name]
            if data["type"] == "multi":
                self.multi_boss_states[name] = data["hp"]
            else:
                for a in agents:
                    self.solo_boss_states[a][name] = data["hp"]

    def process_solo_combat(self, agent, boss_name, rewards):
        """处理单人副本"""
        hp = self.solo_boss_states[agent][boss_name]
        if hp <= 0: hp = BOSS_DATA[boss_name]["hp"] # 自动复活
        
        dmg = self._calc_damage(agent, boss_name)
        hp -= dmg
        rewards[agent] += dmg * 0.02
        
        # 反击
        self._apply_boss_damage(agent, BOSS_DATA[boss_name]["dmg"])
        
        # 击杀
        if hp <= 0:
            self._distribute_loot([agent], boss_name)
            hp = BOSS_DATA[boss_name]["hp"]
            rewards[agent] += 20 * BOSS_DATA[boss_name]["tier"]
            
        self.solo_boss_states[agent][boss_name] = hp

    def resolve_multi_combat_round(self, attack_requests, rewards):
        """统一结算多人战斗队列"""
        # attack_requests 格式: {boss_name: [agent_list]}
        for boss_name, attackers in attack_requests.items():
            if not attackers: continue
            
            # 1. 计算共鸣
            resonance = self._calc_resonance(attackers)
            if resonance > 1.0:
                print(f"*** [Resonance] {boss_name} 受到 x{resonance} 倍伤害! ***")

            # 2. 结算伤害
            total_dmg = 0
            for ag in attackers:
                dmg = self._calc_damage(ag, boss_name) * resonance
                total_dmg += dmg
                rewards[ag] += dmg * 0.05
            
            self.multi_boss_states[boss_name] -= total_dmg
            
            # 3. 反击
            boss_dmg = BOSS_DATA[boss_name]["dmg"]
            for ag in attackers:
                self._apply_boss_damage(ag, boss_dmg, rewards)

            # 4. 击杀判定
            if self.multi_boss_states[boss_name] <= 0:
                print(f"=== [Kill] 团队击败 {boss_name}! ===")
                self._distribute_loot(attackers, boss_name)
                self.multi_boss_states[boss_name] = BOSS_DATA[boss_name]["hp"]
                for ag in attackers: 
                    rewards[ag] += 100 * BOSS_DATA[boss_name]["tier"]

    def _calc_damage(self, agent, boss_name):
        """核心伤害公式：包含阶级压制"""
        b_info = BOSS_DATA[boss_name]
        b_tier, b_attr = b_info["tier"], b_info["attr"]
        best_dmg = 0
        
        # 自动选择最优武器
        player_weapons = self.agent_data[agent]["weapons"]
        for w_name, w_tier in player_weapons.items():
            w_attr = w_name.split("_")[0]
            
            base = BASE_DAMAGE * w_tier
            attr_mod = ATTR_MATRIX[w_attr][b_attr]
            
            # 阶级压制
            tier_diff = w_tier - b_tier
            tier_mod = 1.0
            if tier_diff < 0: tier_mod = 0.5 ** abs(tier_diff)
            elif tier_diff > 0: tier_mod = 1.2 ** tier_diff
                
            final = base * attr_mod * tier_mod
            if final > best_dmg: best_dmg = final
            
        return max(1, int(best_dmg))

    def _calc_resonance(self, attackers):
        """计算队伍属性多样性"""
        elements = set()
        for ag in attackers:
            # 简单取最强武器属性
            weps = self.agent_data[ag]["weapons"]
            best_w = max(weps, key=weps.get)
            elements.add(best_w.split("_")[0])
        
        if len(elements) >= 5: return 1.5
        if len(elements) >= 3: return 1.2
        return 1.0

    def _apply_boss_damage(self, agent, dmg, rewards=None):
        self.agent_data[agent]["hp"] -= dmg
        if self.agent_data[agent]["hp"] <= 0:
            self.agent_data[agent]["hp"] = AGENT_MAX_HEALTH
            if rewards: rewards[agent] -= 50 # 死亡惩罚

    def _distribute_loot(self, agents, boss_name):
        table = get_loot_table(boss_name)
        for ag in agents:
            for item, prob, amt in table:
                if random.random() < prob:
                    self.agent_data[ag]["inventory"][item] += amt