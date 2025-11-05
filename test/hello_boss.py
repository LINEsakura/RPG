import gymnasium
from gymnasium.spaces import Discrete
from pettingzoo import AECEnv
from pettingzoo.utils.agent_selector import agent_selector
import numpy as np

"""
这是你的“最小可行”RPG环境。
它实现了 PettingZoo 的 AECEnv (Agent-Environment-Cycle) 接口。
"""

class HelloBossEnv(AECEnv):
    # PettingZoo 需要的元数据
    metadata = {"render_modes": ["human"], "name": "hello_boss_v0"}

    def __init__(self, render_mode=None):
        # --- 我们的游戏逻辑 ---
        self.boss_start_health = 10
        self.agent_damage = 2
        
        # --- PettingZoo API 要求 ---
        self.possible_agents = ["player_0", "player_1"]
        self.agent_name_mapping = dict(zip(self.possible_agents, list(range(len(self.possible_agents)))))
        
        # 动作空间：0=闲置, 1=攻击
        self.action_spaces = {agent: Discrete(2) for agent in self.possible_agents}
        
        # 观察空间：我们简化到极点
        # Agent 只能观察到 Boss 的剩余血量
        # 我们用 Discrete(11) 表示 (0-10点血)
        self.observation_spaces = {agent: Discrete(self.boss_start_health + 1) for agent in self.possible_agents}
        
        self.render_mode = render_mode

    def observe(self, agent):
        # (PettingZoo API) 返回单个 agent 的观察
        # 必须返回一个 numpy 对象, 而不是一个 python int
        # 我们的空间是 Discrete, 所以我们返回一个 int 类型的 numpy 标量
        return np.array(self.boss_health, dtype=np.int64)

    def reset(self, seed=None, options=None):
        # (PettingZoo API) 重置环境
        
        # --- 我们的游戏逻辑 ---
        self.boss_health = self.boss_start_health
        
        # --- PettingZoo API 要求 ---
        self.agents = self.possible_agents[:]
        self.rewards = {agent: 0 for agent in self.agents}
        self._cumulative_rewards = {agent: 0 for agent in self.agents}
        self.terminations = {agent: False for agent in self.agents}
        self.truncations = {agent: False for agent in self.agents}
        self.infos = {agent: {} for agent in self.agents}
        
        # 决定谁是第一个行动的
        self.agent_selector = agent_selector(self.agents)
        self.agent_selection = self.agent_selector.reset()
        
        # 返回 (观察, info)
        return self.observe(self.agent_selection), {}

    def step(self, action):
        # (PettingZoo API) 环境的核心

        agent = self.agent_selection

        # 1. 关键：为 env.last() 存储“上一步”的累积奖励
        # env.last() 会用 (self.rewards[agent] - self._cumulative_rewards[agent]) 来计算单步奖励
        self._cumulative_rewards[agent] = self.rewards[agent]

        # 2. 如果 agent 已经结束了，切换到下一个
        if self.terminations[agent] or self.truncations[agent]:
            # 当 agent 结束后, env.last() 必须返回 0 奖励
            # (我们不需要在这里设置 self.rewards[agent] = 0, 
            # 因为 _cumulative_rewards 已经等于 rewards, 相减已经是 0)
            self.agent_selection = self.agent_selector.next()
            return


        # 先把这一步的奖励算作 0
        step_reward = 0

        # 1. 解析动作
        if action == 1: # 攻击
            self.boss_health -= self.agent_damage
            print(f"  > {agent} 攻击! Boss 血量: {self.boss_health}")
            # 给予攻击奖励
            step_reward = 1
        else: # 0=闲置
            print(f"  > {agent} 闲置...")
            step_reward = 0 # 闲置没有奖励

        # 2. 检查游戏是否结束 (Boss 被击败)
        if self.boss_health <= 0 and not self.terminations[agent]: # 确保只触发一次
            print(f"*** Boss 被 {agent} 击败! ***")
            # 所有 agent 的游戏都结束了
            self.terminations = {a: True for a in self.agents}
            # 给予击杀者额外奖励
            step_reward += 10

        # --- 4. 关键：把“单步奖励”加到“累积奖励”上 ---
        self.rewards[agent] += step_reward

        # --- 5. 切换到下一个 agent ---
        self.agent_selection = self.agent_selector.next()

        # --- 6. 渲染 (如果需要) ---
        if self.render_mode == "human":
            self.render()

    def render(self):
        # (PettingZoo API) 可视化 (我们先用文本)
        if self.render_mode == "human":
            print(f"  [ 状态: Boss HP: {self.boss_health} ]")

    def close(self):
        pass # 清理（如果需要）