import os
import json
import google.generativeai as genai # (新) 导入 Google 库

# (旧) 我们不再需要 OpenAI 库了
# from openai import OpenAI 

# (不变) 导入我们的“蓝图”
from config.config_globals import *
from config.config_bosses import *
from config.config_weapons import *

class LLMAgent:
    def __init__(self):
        # --- (新!) 1. 配置 Google 客户端 ---
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            # (新) 检查新的环境变量
            raise ValueError("GOOGLE_API_KEY 环境变量未设置！")
            
        genai.configure(api_key=api_key)
        
        # --- (新!) 2. 设置模型 ---
        # (我们使用 gemini-1.5-flash，它又快又强)
        
        # (新) 强制 Gemini 输出 JSON
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json" 
        )
        
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config=generation_config
        )

        # 3. (不变) 构建动作列表
        self.action_list_text = self._build_action_list()

    # --- (不变) 你的所有“翻译官”函数都不需要修改 ---
    
    def _build_action_list(self):
        """(不变) - 将我们的 config 文件“翻译”成 LLM 能看懂的动作列表"""
        action_list = ["0: 闲置 (Idle)"]
        boss_names = list(BOSS_DATA.keys())
        for i, boss_name in enumerate(boss_names):
            boss_attr = BOSS_DATA[boss_name][1]
            loot_list = [item[0] for item in LOOT_TABLES[boss_name]]
            action_list.append(f"{i+1}: 攻击 {boss_name} (属性: {boss_attr}, 掉落: {', '.join(loot_list)})")
            
        weapon_names = list(WEAPON_DATA.keys())
        for i, weapon_name in enumerate(weapon_names):
            weapon_attr = WEAPON_DATA[weapon_name][1]
            cost_str = ", ".join(f"{v} {k}" for k,v in UPGRADE_COSTS[1].items())
            action_list.append(f"{i+len(boss_names)+1}: 制作/升级 {weapon_name} (属性: {weapon_attr}, 1级成本: {cost_str})")
            
        return "\n".join(action_list)

    def _build_system_prompt(self):
        """(不变) - LLM 的“角色设定”"""
        return f"""
        你是一个 RPG 游戏的高玩。你的最终目标是击败 'final_boss'。
        为了击败 'final_boss'，你必须先制作一把 5 级武器 (MAX_WEAPON_LEVEL=5)。
        
        [规则]
        1. 你必须通过攻击其他 Boss 来收集材料。
        2. 你会因为 Boss 反击而受伤，但死亡会自动满血复活。
        3. 你的背包和武器等级是共享的。
        4. 你的“制作/升级”动作会自动使用你背包里的材料来提升你武器的等级。
        
        [动作列表 (你必须选择其中之一)]
        {self.action_list_text}
        
        [输出格式]
        你必须严格按照 JSON 格式回复，包含你的“思考”和你选择的“动作ID”。
        例如:
        {{"thought": "我的背包是空的, 我需要 common_stone, 我应该去打 fire_boss。", "action_id": 1}}
        """

    def _build_user_prompt(self, obs):
        """(不变) - 将环境的“字典”观察“翻译”成 LLM 能看懂的文本"""
        inventory_text = ", ".join(f"{item}: {count}" for item, count in obs["my_inventory"].items() if count > 0)
        if not inventory_text: inventory_text = "空的"
        
        weapon_text = ", ".join(f"{wep}: Lv.{lvl}" for wep, lvl in obs["my_weapons"].items() if lvl > 0)
        if not weapon_text: weapon_text = "无 (只有拳头, 1点伤害)"
        
        state_text = "在世界中 (可以自由行动)" if obs["my_state"] == 0 else f"战斗中 (vs Boss, 剩余 HP: {obs['battle_boss_health']})"
        
        return f"""
        [你当前的状态]
        当前步数: {obs['current_step']}
        血量: {obs['my_health']} / {AGENT_MAX_HEALTH}
        状态: {state_text}
        背包: {inventory_text}
        武器: {weapon_text}
        
        [你的决定]
        根据你的目标和当前状态，做出你的下一步决定。请使用 JSON 格式回复。
        """

    def _parse_llm_response(self, response_text):
        """(不变) - 将 LLM 的“文本”回复“翻译”回环境能懂的“数字”"""
        try:
            data = json.loads(response_text)
            action_id = int(data.get("action_id", 0))
            max_action = len(self.action_list_text.split('\n')) - 1
            if 0 <= action_id <= max_action:
                return action_id
            else:
                print(f"  > [LLM 错误]: LLM 选择了无效的动作ID {action_id}。已强制改为 0。")
                return 0
        except json.JSONDecodeError:
            print(f"  > [LLM 错误]: LLM 返回了无效的 JSON。已强制改为 0。")
            return 0

    def choose_action(self, obs, current_step):
        """
        (新!) 这是“大脑”的主函数 (Gemini 版本)
        """
        # 1. (不变) 准备 Prompt
        obs['current_step'] = current_step
        user_prompt = self._build_user_prompt(obs)
        system_prompt = self._build_system_prompt()
        
        # (新) Gemini 的 API 格式是 [system, user]
        full_prompt = [system_prompt, user_prompt]

        print(f"  > [Gemini]: Geminig 正在思考...")
        
        try:
            # 2. (新) 调用 Google Gemini API
            response = self.model.generate_content(full_prompt)
            
            # 3. (新) 从 Gemini 获取回复文本
            response_text = response.text
            
            # 4. (不变) 解析 JSON
            action_id = self._parse_llm_response(response_text)
            
            # (新) Gemini 强制 JSON，所以我们可以更安全地加载它
            print(f"  > [Gemini 思考]: {json.loads(response_text).get('thought', '...')}")
            
            return action_id

        except Exception as e:
            print(f"  > [Gemini API 错误]: {e}. 已强制改为 0。")
            return 0