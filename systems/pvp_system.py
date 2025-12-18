from config.config_shop import PVP_REWARD_GOLD

class PvpSystem:
    def __init__(self, agent_data_ref):
        self.agent_data = agent_data_ref
        self.queue = []

    def reset(self):
        self.queue = []

    def join_queue(self, agent):
        if agent not in self.queue:
            self.queue.append(agent)

    def resolve_matches(self, rewards):
        while len(self.queue) >= 2:
            p1 = self.queue.pop(0)
            p2 = self.queue.pop(0)
            
            # 简单战力对比：总武器 Tier
            s1 = sum(self.agent_data[p1]["weapons"].values())
            s2 = sum(self.agent_data[p2]["weapons"].values())
            
            winner = p1 if s1 >= s2 else p2
            
            self.agent_data[winner]["gold"] += PVP_REWARD_GOLD
            rewards[winner] += 100
            print(f"[PvP] {winner} 击败了对手 (战力 {s1} vs {s2})")