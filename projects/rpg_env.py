# --- 1. 导入库 ---
import gymnasium
from gymnasium.spaces import Discrete, Dict, Box
from pettingzoo import AECEnv
from pettingzoo.utils.agent_selector import agent_selector
import numpy as np
import random

# --- 2. 导入我们所有的配置文件! ---
from config.config_globals import *
from config.config_bosses import *
from config.config_weapons import *

class RpgEnv(AECEnv):
    metadata = {"render_modes": ["human"], "name": "rpg_env_v0"}

    def __init__(self, render_mode=None):
        # (代码 100% 不变, 因为所有变量名都一样)
        self.boss_names = list(BOSS_DATA.keys())
        self.weapon_names = list(WEAPON_DATA.keys())
        self.possible_agents = ["player_0", "player_1"]
        
        num_actions = 1 + len(self.boss_names) + len(self.weapon_names)
        self.action_spaces = {agent: Discrete(num_actions) for agent in self.possible_agents}
        
        self.observation_spaces = {
            agent: Dict({
                "my_health": Discrete(AGENT_MAX_HEALTH + 1),
                "my_inventory": Dict({stone: Discrete(100) for stone in STONE_NAMES}),
                "my_weapons": Dict({weapon: Discrete(MAX_WEAPON_LEVEL + 1) for weapon in self.weapon_names}),
                "boss_healths": Dict({boss: Discrete(BOSS_DATA[boss][0] + 1) for boss in self.boss_names})
            })
            for agent in self.possible_agents
        }
        self.render_mode = render_mode

    # 
    # (这部分代码也 100% 不变)
    #
    def observe(self, agent):
        obs = {
            "my_health": self.agent_healths[agent],
            "my_inventory": self.agent_inventories[agent],
            "my_weapons": self.agent_weapons[agent],
            "boss_healths": self.boss_healths
        }
        return obs

    def reset(self, seed=None, options=None):
        self.boss_healths = {boss: BOSS_DATA[boss][0] for boss in self.boss_names}
        self.agents = self.possible_agents[:]
        self.agent_healths = {agent: AGENT_MAX_HEALTH for agent in self.agents}
        self.agent_inventories = {agent: {stone: 0 for stone in STONE_NAMES} for agent in self.agents}
        self.agent_weapons = {agent: {weapon: 0 for weapon in self.weapon_names} for agent in self.agents}
        
        self.rewards = {agent: 0 for agent in self.agents}
        self._cumulative_rewards = {agent: 0 for agent in self.agents}
        self.terminations = {agent: False for agent in self.agents}
        self.truncations = {agent: False for agent in self.agents}
        self.infos = {agent: {} for agent in self.agents}
        
        self.agent_selector = agent_selector(self.agents)
        self.agent_selection = self.agent_selector.reset()
        
        return self.observe(self.agent_selection), {}

    # 
    # (这部分代码也 100% 不变, 
    # 因为它只是在调用 config 文件中定义的函数和数据)
    #
    def _roll_loot(self, boss_name):
        loot = {stone: 0 for stone in STONE_NAMES}
        for item, prob, amount in LOOT_TABLES[boss_name]:
            if random.random() < prob: 
                loot[item] += amount
        print(f"  > Boss {boss_name} 掉落了: {loot}")
        return loot

    def _calculate_damage(self, agent, boss_name):
        agent_weapon_levels = self.agent_weapons[agent]
        total_damage = 1 
        active_weapons = []
        for weapon_name, level in agent_weapon_levels.items():
            if level > 0:
                active_weapons.append((weapon_name, level))
        if not active_weapons:
            return total_damage
        weapon_name, level = active_weapons[0]
        base_dmg = WEAPON_DATA[weapon_name][0]
        upgrade_dmg = level * 5 
        weapon_attr = WEAPON_DATA[weapon_name][1]
        boss_attr = BOSS_DATA[boss_name][1]
        attr_multiplier = ATTR_MATRIX[weapon_attr][boss_attr]
        total_damage = (base_dmg + upgrade_dmg) * attr_multiplier
        return total_damage

    def _handle_craft_or_upgrade(self, agent, weapon_name):
        current_level = self.agent_weapons[agent][weapon_name]
        if current_level == MAX_WEAPON_LEVEL:
            return 0 
        next_level = current_level + 1
        costs = UPGRADE_COSTS[next_level]
        can_afford = True
        inventory = self.agent_inventories[agent]
        weapon_attr = WEAPON_DATA[weapon_name][1]
        for material, amount in costs.items():
            if material == "attribute_stone":
                attr_stone_name = f"{weapon_attr}_stone"
                if inventory[attr_stone_name] < amount:
                    can_afford = False
                    break
            elif inventory[material] < amount:
                can_afford = False
                break
        if can_afford:
            for material, amount in costs.items():
                if material == "attribute_stone":
                    attr_stone_name = f"{weapon_attr}_stone"
                    inventory[attr_stone_name] -= amount
                else:
                    inventory[material] -= amount
            self.agent_weapons[agent][weapon_name] = next_level
            print(f"  > {agent} 成功将 {weapon_name} 升级到 Lv.{next_level}!")
            return 50 
        else:
            print(f"  > {agent} 尝试升级 {weapon_name}, 但材料不足.")
            return 0 

    # 
    # (Step, Render, Close 函数也 100% 不变)
    #
    def step(self, action):
        agent = self.agent_selection
        self._cumulative_rewards[agent] = self.rewards[agent]
        
        if self.terminations[agent] or self.truncations[agent]:
            self.agent_selection = self.agent_selector.next()
            return

        step_reward = 0
        
        if action == 0:
            print(f"  > {agent} 闲置...")
            step_reward = 0
            
        elif 1 <= action <= len(self.boss_names):
            boss_name = self.boss_names[action - 1]
            if self.boss_healths[boss_name] > 0:
                damage = self._calculate_damage(agent, boss_name)
                self.boss_healths[boss_name] -= damage
                print(f"  > {agent} 攻击 {boss_name}, 造成 {damage:.0f} 伤害. 剩余 HP: {self.boss_healths[boss_name]:.0f}")
                
                if self.boss_healths[boss_name] <= 0:
                    print(f"*** {boss_name} 被 {agent} 击败! ***")
                    loot = self._roll_loot(boss_name)
                    for item, amount in loot.items():
                        self.agent_inventories[agent][item] += amount
                    step_reward += 100
                    self.boss_healths[boss_name] = BOSS_DATA[boss_name][0]
                
                boss_retaliation_dmg = BOSS_DATA[boss_name][2]
                if boss_retaliation_dmg > 0:
                    self.agent_healths[agent] -= boss_retaliation_dmg
                    print(f"  > {boss_name} 反击 {agent}, 造成 {boss_retaliation_dmg} 伤害. 剩余 HP: {self.agent_healths[agent]}")
            
        elif (len(self.boss_names) + 1) <= action < (1 + len(self.boss_names) + len(self.weapon_names)):
            weapon_name = self.weapon_names[action - (len(self.boss_names) + 1)]
            step_reward = self._handle_craft_or_upgrade(agent, weapon_name)

        if self.agent_healths[agent] <= 0:
            print(f"--- {agent} 已经死亡! ---")
            self.terminations[agent] = True
            step_reward = -500 
            
        if all(self.terminations.values()):
            self.truncations = {a: True for a in self.agents}

        self.rewards[agent] += step_reward
        self.agent_selection = self.agent_selector.next()

        if self.render_mode == "human":
            self.render()

    def render(self):
        if self.render_mode == "human":
            print("--- 状态更新 ---")
            print(f"  轮到: {self.agent_selection}")
            print("  Bosses:")
            for boss, hp in self.boss_healths.items():
                print(f"    {boss}: {hp:.0f} HP")
            print("  Agents:")
            for agent in self.agents:
                print(f"    {agent}: {self.agent_healths[agent]} HP")
                inv = {k:v for k,v in self.agent_inventories[agent].items() if v > 0}
                wep = {k:v for k,v in self.agent_weapons[agent].items() if v > 0}
                print(f"      Inv: {inv}")
                print(f"      Wep: {wep}")

    def close(self):
        pass