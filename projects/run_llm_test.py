import os
from .rpg_env import RpgEnv
from .llm_agent import LLMAgent # (新) 导入我们的 LLM 大脑

def run_llm_simulation():
    """
    (新) 运行一个由 LLM Agent 驱动的并行模拟
    """
    
    print(f"--- [LLM Agent 模拟] 开始 ---")
    
    # 1. 创建环境 (它自动包含了 5 个 agent)
    env = RpgEnv(render_mode="human")
    
    # 2. (新) 为每个 agent 创建一个“大脑”
    #    (我们这里创建一个字典, key 是 agent_id, value 是大脑)
    brains = {agent_id: LLMAgent() for agent_id in env.possible_agents}
    
    # 3. 重置环境
    observations, infos = env.reset()
    
    # 只要环境中还有 agent, 循环就继续
    while env.agents:
        
        # (新!) 我们为 *所有* 存活的 agent 创建一个动作字典
        actions = {}
        
        # (新!) 循环遍历所有 *当前存活* 的 agent
        for agent_id in env.agents:
            
            # 1. 获取这个 agent 的大脑
            agent_brain = brains[agent_id]
            
            # 2. 获取这个 agent 的当前观察
            current_obs = observations[agent_id]
            
            # 3. 让“大脑”根据“观察”选择一个“动作”
            action_id = agent_brain.choose_action(current_obs, env.current_step)
            
            actions[agent_id] = action_id

        # 5. 执行 *所有* agent 的动作
        observations, rewards, terminations, truncations, infos = env.step(actions)

    print(f"--- [LLM Agent 模拟] 结束 (所有 Agent 已 Terminated 或 Truncated) ---")
    env.close()

if __name__ == "__main__":
    # (新) 检查 API Key 是否已设置
    if not os.environ.get("OPENAI_API_KEY"):
        print("错误: OPENAI_API_KEY 环境变量未设置。")
        print("请运行: export OPENAI_API_KEY='sk-...'")
    else:
        print("--- 运行 LLM 驱动的并行模拟 ---")
        run_llm_simulation()