import gymnasium
from gymnasium.spaces import Discrete, Dict
from pettingzoo import ParallelEnv
from pettingzoo.utils import wrappers
import numpy as np
import random
import os

from config.config_globals import *
from config.config_bosses import *
from config.config_weapons import *

class RpgEnv(ParallelEnv): # ParallelEnv
    metadata = {"render_modes": ["human"], "name": "rpg_env_v0"}

    def __init__(self, render_mode=None):
        
        self.possible_agents = [f"player_{i}" for i in range(5)] # (新) 5 个 Agent
        self.agents = self.possible_agents[:]
        
        self.boss_names = list(BOSS_DATA.keys())
        self.weapon_names = list(WEAPON_DATA.keys())

        # PettingZoo Parallel API
        self.observation_spaces = {
            agent: Dict({
                "my_health": Discrete(AGENT_MAX_HEALTH + 1),
                "my_state": Discrete(2), # 0 = 在世界, 1 = 在战斗
                "my_inventory": Dict({stone: Discrete(100) for stone in STONE_NAMES}),
                "my_weapons": Dict({weapon: Discrete(MAX_WEAPON_LEVEL + 1) for weapon in self.weapon_names}),
                # (简化) agent 不再能看到所有 Boss 血量, 只能看到自己战斗中的 Boss
                "battle_boss_health": Discrete(BOSS_DATA["final_boss"][0] + 1) # (取一个最大值)
            })
            for agent in self.possible_agents
        }
        
        num_actions = 1 + len(self.boss_names) + len(self.weapon_names)
        self.action_spaces = {agent: Discrete(num_actions) for agent in self.possible_agents}
        
        self.render_mode = render_mode
        self.current_step = 0
        
        # --- 核心逻辑：状态机 ---
        self.agent_healths = {}
        self.agent_inventories = {}
        self.agent_weapons = {}
        # 追踪 Agent 在干什么: "WORLD" 或 "BATTLE"
        self.agent_states = {agent: "WORLD" for agent in self.possible_agents}
        # 追踪 Agent 的独立战斗 "副本"
        self.battle_instances = {} # e.g. {"player_0": {"type": "fire_boss", "health": 1000}}

    def _get_obs(self, agent):
        """ParallelEnv 的观察函数"""
        battle_hp = 0
        if self.agent_states[agent] == "BATTLE":
            battle_hp = self.battle_instances[agent]["health"]

        return {
            "my_health": self.agent_healths[agent],
            "my_state": 1 if self.agent_states[agent] == "BATTLE" else 0,
            "my_inventory": self.agent_inventories[agent],
            "my_weapons": self.agent_weapons[agent],
            "battle_boss_health": battle_hp
        }

    def reset(self, seed=None, options=None):
        # 重置所有 Agent
        self.agents = self.possible_agents[:]
        self.agent_healths = {agent: AGENT_MAX_HEALTH for agent in self.agents}
        self.agent_inventories = {agent: {stone: 0 for stone in STONE_NAMES} for agent in self.agents}
        self.agent_weapons = {agent: {weapon: 0 for weapon in self.weapon_names} for agent in self.agents}
        self.agent_states = {agent: "WORLD" for agent in self.agents}
        self.battle_instances = {}
        self.current_step = 0

        # ParallelEnv reset 返回一个 obs 字典
        observations = {agent: self._get_obs(agent) for agent in self.agents}
        infos = {agent: {} for agent in self.agents}
        return observations, infos

    # --- Boss 战斗的核心逻辑 ---
    def _create_battle_instance(self, agent, boss_name):
        """创建一个崭新的 '副本' Boss"""
        if self.agent_states[agent] == "WORLD":
            print(f"  > {agent} 开始挑战 {boss_name}!")
            self.agent_states[agent] = "BATTLE"
            self.battle_instances[agent] = {
                "type": boss_name,
                "health": BOSS_DATA[boss_name][0]
            }
    
    def _resolve_battle_loss(self, agent):
        """Agent 死亡，满血复活，Boss 副本被删除"""
        print(f"--- {agent} 死亡! 满血复活. ---")
        self.agent_healths[agent] = AGENT_MAX_HEALTH
        self.agent_states[agent] = "WORLD"
        del self.battle_instances[agent]
        return 0 # 死亡没有奖励
        
    def _resolve_battle_win(self, agent, battle):
        """Boss 死亡，掉落，Boss 副本被删除"""
        boss_name = battle["type"]
        print(f"*** {boss_name} 被 {agent} 击败! ***")
        
        # 1. 获得战利品
        loot = self._roll_loot(boss_name)
        for item, amount in loot.items():
            self.agent_inventories[agent][item] += amount
        
        # 2. 离开战斗
        self.agent_states[agent] = "WORLD"
        del self.battle_instances[agent]
        
        # 3. 检查是否是最终胜利
        if boss_name == "final_boss":
            return 10000 # 巨大胜利奖励
        else:
            return 100 # 普通击杀奖励

    # --- 战斗计算 ---
    def _roll_loot(self, boss_name):
        loot = {stone: 0 for stone in STONE_NAMES}
        for item, prob, amount in LOOT_TABLES[boss_name]:
            if random.random() < prob: loot[item] += amount
        print(f"  > Boss {boss_name} 掉落了: {loot}")
        return loot

    def _calculate_damage(self, agent, boss_name):
        agent_weapon_levels = self.agent_weapons[agent]
        total_damage = 1 
        if boss_name == "final_boss":
            has_max_weapon = any(level == MAX_WEAPON_LEVEL for level in agent_weapon_levels.values())
            if not has_max_weapon: return 0 
        
        active_weapons = [(name, lvl) for name, lvl in agent_weapon_levels.items() if lvl > 0]
        if not active_weapons: return total_damage
        
        weapon_name, level = active_weapons[0]
        base_dmg = WEAPON_DATA[weapon_name][0]
        upgrade_dmg = UPGRADE_DAMAGE[level]

        weapon_attr = WEAPON_DATA[weapon_name][1]
        boss_attr = BOSS_DATA[boss_name][1]
        attr_multiplier = ATTR_MATRIX[weapon_attr][boss_attr]
        total_damage = (base_dmg + upgrade_dmg) * attr_multiplier
        return total_damage

    def _handle_craft_or_upgrade(self, agent, weapon_name):
        current_level = self.agent_weapons[agent][weapon_name]
        if current_level == MAX_WEAPON_LEVEL: return 0 
        next_level = current_level + 1
        costs = UPGRADE_COSTS[next_level]
        can_afford = True
        inventory = self.agent_inventories[agent]
        weapon_attr = WEAPON_DATA[weapon_name][1]
        for material, amount in costs.items():
            if material == "attribute_stone":
                attr_stone_name = f"{weapon_attr}_stone"
                if inventory[attr_stone_name] < amount: can_afford = False; break
            elif inventory[material] < amount: can_afford = False; break
        if can_afford:
            for material, amount in costs.items():
                if material == "attribute_stone":
                    attr_stone_name = f"{weapon_attr}_stone"
                    inventory[attr_stone_name] -= amount
                else: inventory[material] -= amount
            self.agent_weapons[agent][weapon_name] = next_level
            print(f"  > {agent} 成功将 {weapon_name} 升级到 Lv.{next_level}!")
            return 50 
        else:
            print(f"  > {agent} 尝试升级 {weapon_name}, 但材料不足.")
            return 0 

    # --- 并行 Step 函数 ---
    def step(self, actions):
        
        # ParallelEnv 接收一个动作字典, 返回四个字典
        observations = {}
        rewards = {}
        terminations = {}
        truncations = {}
        infos = {}

        self.current_step += 1

        # 1. 循环处理每个 agent 的动作
        for agent in self.agents:
            action = actions.get(agent) # 获取这个 agent 的动作
            if action is None:
                continue # Agent 已经结束, 跳过

            step_reward = 0
            
            # 在循环开始时，我们假设 agent 这一步不会结束
            terminations[agent] = False 
            
            # --- 2. 状态机：根据 Agent 在“世界”还是“战斗”中，执行不同逻辑 ---
            
            if self.agent_states[agent] == "WORLD":
                # --- Agent 在“世界”中 ---
                if action == 0: # 闲置
                    print(f"  > {agent} [World] 闲置...")
                    
                elif 1 <= action <= len(self.boss_names): # 尝试开始战斗
                    boss_name = self.boss_names[action - 1]
                    self._create_battle_instance(agent, boss_name)
                    
                elif (len(self.boss_names) + 1) <= action < (1 + len(self.boss_names) + len(self.weapon_names)):
                    weapon_name = self.weapon_names[action - (len(self.boss_names) + 1)]
                    step_reward = self._handle_craft_or_upgrade(agent, weapon_name)
            
            elif self.agent_states[agent] == "BATTLE":
                # --- Agent 在“战斗”中 ---
                battle = self.battle_instances[agent]
                boss_name = battle["type"]
                
                if action > 0: # 简化：任何非闲置动作都是“攻击”
                    # 1. Agent 攻击 Boss
                    damage = self._calculate_damage(agent, boss_name)
                    battle["health"] -= damage
                    print(f"  > {agent} [Battle] 攻击 {boss_name}, 造成 {damage:.0f} 伤害. 剩余 HP: {battle['health']:.0f}")
                    
                    if battle["health"] <= 0:
                        # --- 胜利逻辑在这里！ ---
                        step_reward = self._resolve_battle_win(agent, battle)
                        
                        # 检查这是否是最终的胜利
                        if boss_name == "final_boss":
                            print(f"*** {agent} 击败了最终Boss! ***")
                            terminations[agent] = True # 在这里设置
                    else:
                        # 2. Boss 反击 (如果会反击)
                        boss_retaliation_dmg = BOSS_DATA[boss_name][2]
                        if boss_retaliation_dmg > 0:
                            self.agent_healths[agent] -= boss_retaliation_dmg
                            print(f"  > {boss_name} 反击 {agent}, 造成 {boss_retaliation_dmg} 伤害.")
                            if self.agent_healths[agent] <= 0:
                                # 失败
                                step_reward = self._resolve_battle_loss(agent)
                else: # Action == 0 (闲置/逃跑)
                    print(f"  > {agent} [Battle] 闲置...")
            
            # --- 3. 奖励和胜利检查 ---
            rewards[agent] = step_reward
            
        # --- 4. 检查超时 ---
        truncated = self.current_step >= AGENT_MAX_STEPS
        if truncated:
            print(f"--- 达到最大步数 {AGENT_MAX_STEPS}, 游戏超时 ---")
            self.agents = [] # 超时后, 移除所有 agents
        
        # 5. ParallelEnv: 移除 "dead" (terminated) agents
        for agent in list(self.agents): # (迭代一个副本)
            if terminations.get(agent, False):
                self.agents.remove(agent)

        # 6. 为所有 *仍然存活* 的 agent 准备返回值
        for agent in self.agents:
            observations[agent] = self._get_obs(agent)
            truncations[agent] = truncated # (新) 广播 truncated 状态
            infos[agent] = {}
        
        if self.render_mode == "human":
            self.render()

        # ParallelEnv 返回 5 个字典
        return observations, rewards, terminations, truncations, infos

    def render(self):
        if self.render_mode == "human":
            print(f"--- 步骤: {self.current_step} ---")
            for agent in self.possible_agents:
                if agent not in self.agents: 
                    print(f"  Agent: {agent} (已结束)")
                    continue
                
                # 打印 Agent 状态
                print(f"  Agent: {agent} (HP: {self.agent_healths[agent]}) (State: {self.agent_states[agent]})")
                
                # 打印战斗信息
                if self.agent_states[agent] == "BATTLE":
                    battle = self.battle_instances[agent]
                    print(f"    IN BATTLE vs {battle['type']} (HP: {battle['health']:.0f})")
                
                # 打印背包
                inv = {k:v for k,v in self.agent_inventories[agent].items() if v > 0}
                if inv: 
                    print(f"    Inv: {inv}")
                
                # --- 详细打印武器信息 ---
                agent_weps = self.agent_weapons[agent]
                # 检查 agent 是否至少有一把武器
                has_weps = any(level > 0 for level in agent_weps.values())
                
                if has_weps:
                    print("    Wep:")
                    # 循环 agent 拥有的所有武器
                    for weapon_name, level in agent_weps.items():
                        if level > 0:
                            # 从导入的 WEAPON_DATA 中查询属性
                            # WEAPON_DATA[weapon_name] -> (基础伤害, 属性)
                            attribute = WEAPON_DATA[weapon_name][1]
                            
                            # 打印详细信息
                            print(f"      - {weapon_name}: (Level {level}, Attr: {attribute})")
                # --- 详细打印结束 ---

    def close(self):
        pass # 日志记录功能已被移除