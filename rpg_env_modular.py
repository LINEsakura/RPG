import gymnasium
from gymnasium.spaces import Discrete, Dict
from pettingzoo import ParallelEnv

# 导入配置和子系统
from config.config_globals import *
from config.config_bosses import BOSS_NAMES, BOSS_DATA
from config.config_weapons import WEAPON_NAMES
from config.config_shop import SHOP_PRICES, BASE_MARKET_PRICES, TRADEABLE_ITEMS

from systems.player_system import PlayerSystem
from systems.combat_system import CombatSystem
from systems.economy_system import EconomySystem
from systems.pvp_system import PvpSystem

class RpgEnvModular(ParallelEnv):
    metadata = {"render_modes": ["human"], "name": "rpg_modular_v1"}

    def __init__(self, render_mode=None):
        self.possible_agents = [f"player_{i}" for i in range(5)]
        self.agents = self.possible_agents[:]
        self.render_mode = render_mode
        
        # --- 初始化子系统 ---
        # PlayerSystem 持有数据源 (Source of Truth)
        self.player_sys = PlayerSystem(self.agents)
        # 其他系统共享同一个数据源引用
        self.combat_sys = CombatSystem(self.player_sys.agent_data)
        self.economy_sys = EconomySystem(self.player_sys.agent_data)
        self.pvp_sys = PvpSystem(self.player_sys.agent_data)
        
        # --- 构建动作空间索引 ---
        self._build_action_space()
        
        self.observation_spaces = {a: Dict({"val": Discrete(1)}) for a in self.agents}

    def _build_action_space(self):
        """动态生成动作索引映射"""
        self.act_idx = {}
        curr = 1 # 0 is IDLE
        
        self.act_idx["attack_start"] = curr
        curr += len(BOSS_NAMES)
        
        self.act_idx["upgrade_start"] = curr
        curr += len(WEAPON_NAMES)
        
        self.shop_items = list(SHOP_PRICES.keys())
        self.act_idx["shop_start"] = curr
        curr += len(self.shop_items)
        
        self.act_idx["sell_start"] = curr
        curr += len(TRADEABLE_ITEMS)
        
        self.act_idx["buy_start"] = curr
        curr += len(TRADEABLE_ITEMS)
        
        self.act_idx["pvp"] = curr
        curr += 1
        
        self.action_spaces = {a: Discrete(curr) for a in self.agents}

    def reset(self, seed=None, options=None):
        self.agents = self.possible_agents[:]
        self.current_step = 0
        
        # 重置所有子系统
        self.player_sys.reset()
        self.combat_sys.reset(self.agents)
        self.economy_sys.reset()
        self.pvp_sys.reset()
            
        return {a: {} for a in self.agents}, {a: {} for a in self.agents}

    def step(self, actions):
        self.current_step += 1
        rewards = {a: 0 for a in self.agents}
        infos = {a: {} for a in self.agents}
        
        # 收集多Boss战斗请求
        multi_attacks = {name: [] for name in BOSS_NAMES}
        
        # --- 分发 Agent 动作 ---
        for agent in self.agents:
            if agent not in actions: continue
            action = actions[agent]
            
            # 1. 战斗
            if self.act_idx["attack_start"] <= action < self.act_idx["upgrade_start"]:
                idx = action - self.act_idx["attack_start"]
                boss_name = BOSS_NAMES[idx]
                
                if BOSS_DATA[boss_name]["type"] == "solo":
                    self.combat_sys.process_solo_combat(agent, boss_name, rewards)
                else:
                    if self.combat_sys.multi_boss_states[boss_name] > 0:
                        multi_attacks[boss_name].append(agent)

            # 2. 升级
            elif self.act_idx["upgrade_start"] <= action < self.act_idx["shop_start"]:
                idx = action - self.act_idx["upgrade_start"]
                self.player_sys.handle_upgrade(agent, WEAPON_NAMES[idx])

            # 3. 商店
            elif self.act_idx["shop_start"] <= action < self.act_idx["sell_start"]:
                idx = action - self.act_idx["shop_start"]
                self.economy_sys.buy_from_shop(agent, self.shop_items[idx])

            # 4. 拍卖行卖
            elif self.act_idx["sell_start"] <= action < self.act_idx["buy_start"]:
                idx = action - self.act_idx["sell_start"]
                self.economy_sys.post_auction(agent, TRADEABLE_ITEMS[idx])

            # 5. 拍卖行买
            elif self.act_idx["buy_start"] <= action < self.act_idx["pvp"]:
                idx = action - self.act_idx["buy_start"]
                self.economy_sys.buy_auction(agent, TRADEABLE_ITEMS[idx])

            # 6. PvP
            elif action == self.act_idx["pvp"]:
                self.pvp_sys.join_queue(agent)

        # --- 系统级结算 ---
        
        # 结算多人战斗 (处理共鸣)
        self.combat_sys.resolve_multi_combat_round(multi_attacks, rewards)
        
        # 结算 PvP
        self.pvp_sys.resolve_matches(rewards)

        # 结束判定
        truncated = self.current_step >= MAX_STEPS
        
        return {a:{} for a in self.agents}, rewards, {a:False for a in self.agents}, {a:truncated for a in self.agents}, infos