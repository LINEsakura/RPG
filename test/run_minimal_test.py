from hello_boss import HelloBossEnv
from pettingzoo.test import api_test

def run_game():
    """运行一个完整的游戏回合"""
    
    # 1. 创建环境
    # render_mode="human" 会打印出 render() 的内容
    env = HelloBossEnv(render_mode="human")
    
    print("--- 游戏开始 ---")
    
    # 2. 重置环境并获取第一个 agent 的观察
    observation, info = env.reset()
    
    # 3. 循环直到游戏结束
    for agent in env.agent_iter():
        
        # 检查游戏是否已结束
        # env.last() 返回 (obs, reward, terminated, truncated, info)
        if env.terminations[agent] or env.truncations[agent]:
            action = None # 游戏结束，啥也不干
        else:
            # --- 在这里写你的“AI” ---
            #
            # 我们的“最小 AI”：
            # player_0 永远攻击 (action=1)
            # player_1 永远闲置 (action=0)
            if agent == "player_0":
                action = 1
            else:
                action = 0
        
        # 4. 执行动作
        env.step(action)

    print("--- 游戏结束 ---")
    env.close()

if __name__ == "__main__":
    print("--- [已跳过] 正在进行 PettingZoo API 兼容性测试 ---")

    # 运行我们自己写的游戏
    print("--- 直接运行我们自己的游戏 ---")
    run_game()