# run_benchmark.py
from rpg_env_final import RpgEnvFinal
import random
import time

def main():
    env = RpgEnvFinal()
    observations, infos = env.reset()
    
    print("=== RPG Benchmark 启动 ===")
    print(f"Agents: {env.agents}")
    print(f"Action Space Size: {env.action_spaces['player_0'].n}")
    
    # 运行 100 步测试
    for step in range(100):
        actions = {}
        for agent in env.agents:
            # 这里是随机动作，实际Benchmark中应接入LLM
            actions[agent] = env.action_spaces[agent].sample()
            
        obs, rewards, terminations, truncations, infos = env.step(actions)
        
        # 简单的日志抽样
        if step % 20 == 0:
            p0_data = env.agent_data['player_0']
            print(f"\n[Step {step}] Player_0 Status:")
            print(f"  HP: {p0_data['hp']}")
            print(f"  Gold: {p0_data['gold']}")
            print(f"  Inventory: { {k:v for k,v in p0_data['inventory'].items() if v>0} }")
            print(f"  Weapons: {p0_data['weapons']}")
            
        if all(truncations.values()):
            break
            
    print("=== 测试结束 ===")

if __name__ == "__main__":
    main()