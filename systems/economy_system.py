from config.config_shop import SHOP_PRICES, BASE_MARKET_PRICES

class EconomySystem:
    def __init__(self, agent_data_ref):
        self.agent_data = agent_data_ref
        self.auction_house = [] # [{"seller": id, "item": name, "price": int}]

    def reset(self):
        self.auction_house = []

    def buy_from_shop(self, agent, item_name):
        data = self.agent_data[agent]
        price = SHOP_PRICES.get(item_name, 99999)
        
        if data["gold"] >= price:
            data["gold"] -= price
            data["inventory"][item_name] += 1
            return True
        return False

    def post_auction(self, agent, item_name):
        """以市场价 1.2 倍挂单"""
        data = self.agent_data[agent]
        if data["inventory"].get(item_name, 0) > 0:
            data["inventory"][item_name] -= 1
            price = int(BASE_MARKET_PRICES.get(item_name, 100) * 1.2)
            self.auction_house.append({"seller": agent, "item": item_name, "price": price})
            print(f"[Auction] {agent} 上架 {item_name} 价格 {price}")

    def buy_auction(self, agent, item_name):
        """购买最便宜的单"""
        listings = [l for l in self.auction_house if l["item"] == item_name]
        if not listings: return
        
        best_deal = min(listings, key=lambda x: x["price"])
        buyer = self.agent_data[agent]
        
        if buyer["gold"] >= best_deal["price"]:
            price = best_deal["price"]
            seller_id = best_deal["seller"]
            
            # 交易执行
            buyer["gold"] -= price
            buyer["inventory"][item_name] += 1
            
            if seller_id in self.agent_data:
                self.agent_data[seller_id]["gold"] += price
                
            self.auction_house.remove(best_deal)
            print(f"[Trade] {agent} 购买了 {item_name} (卖家: {seller_id})")