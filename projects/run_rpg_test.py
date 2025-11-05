from .rpg_env import RpgEnv
import random

def run_game():
    """运行一个完整的游戏回合"""
    
    # 1. 创建环境
    env = RpgEnv(render_mode="human")
    
    print("--- 游戏开始 ---")
    
    # 2. 重置环境
    observation, info = env.reset()
    
    # 3. 循环直到游戏结束 (这里我们只跑 100 步)
    for _ in range(100):
        
        # 轮询所有 agent
        for agent in env.agent_iter():
            
            # 检查游戏是否已结束
            if env.terminations[agent] or env.truncations[agent]:
                action = None # 游戏结束，啥也不干
            else:
                # --- 在这里写你的“AI” ---
                #
                # 我们的“AI”：
                # 随机做一件事
                action = env.action_spaces[agent].sample()
                
                # (一个更好的 AI 示例：两个 agent 都去刷 "fire_boss")
                # action = 1 # 1 = 攻击 fire_boss
            
            # 4. 执行动作
            # (我们不需要 step 的返回值, 因为 env.agent_iterator() 会处理)
            env.step(action)

    print("--- 游戏结束 (100 步) ---")
    env.close()

if __name__ == "__main__":
    
    print("--- [已跳过] PettingZoo API 测试 (环境太复杂) ---")
    
    # 运行我们自己写的游戏
    print("--- 直接运行我们自己的游戏 (100 步) ---")
    run_game()