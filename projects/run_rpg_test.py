import os
from .rpg_env import RpgEnv # (新) 我们导入的是新的 ParallelEnv
import random

# (新) 请求 1：日志功能已被移除, 我们先专注于让环境跑起来
# LOG_DIRECTORY = "simulation_logs" 

def run_simulation():
    """
    (新) 运行一个包含 5 个并行 Agent 的模拟
    """
    
    print(f"--- [并行模拟] 开始 ---")
    
    # 1. 创建一个环境 (它自动包含了 5 个 agent)
    env = RpgEnv(render_mode="human")
    
    # 2. 重置环境 (Gymnasium 循环)
    observations, infos = env.reset()
    
    # (新) 只要环境中还有 agent, 循环就继续
    while env.agents:
        
        # --- 在这里写你的“AI” ---
        #
        # (新) 关键: 我们必须为 *所有* 存活的 agent 创建一个动作字典
        actions = {}
        for agent in env.agents:
            # 我们的“AI”：随机做一件事
            actions[agent] = env.action_spaces[agent].sample()
            
            # (一个更好的 AI 示例：让 player_0 刷 "fire_boss")
            # if agent == "player_0":
            #     actions[agent] = 1 # 1 = 攻击 fire_boss
            # else:
            #     actions[agent] = env.action_spaces[agent].sample()

        # 5. 执行 *所有* agent 的动作
        observations, rewards, terminations, truncations, infos = env.step(actions)

    print(f"--- [并行模拟] 结束 (所有 Agent 已 Terminated 或 Truncated) ---")
    env.close()

if __name__ == "__main__":
    
    print("--- 运行并行模拟 ---")
    run_simulation()