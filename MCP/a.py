import requests
import json
import time
from datetime import datetime, timedelta

class MCP12306Client:
    def __init__(self, base_url: str = "http://127.0.0.1:8888"):
        self.base_url = base_url
        self.mcp_url = f"{base_url}/mcp"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream'
        })
    
    def send_request(self, method: str, params: dict = None):
        """发送请求到 MCP 服务器"""
        payload = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": method,
            "params": params or {}
        }
        
        try:
            response = self.session.post(self.mcp_url, json=payload, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if "error" in result:
                    print(f"请求错误: {result['error']}")
                    return None
                return result.get("result")
            else:
                print(f"HTTP错误: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"请求异常: {e}")
            return None
    
    # 基础工具方法
    def get_current_date(self):
        """获取当前日期（上海时区）"""
        return self.send_request("get-current-date")
    
    def get_stations_in_city(self, city: str):
        """查询城市内所有车站"""
        return self.send_request("get-stations-code-in-city", {"city": city})
    
    def get_city_station_code(self, cities: str):
        """获取城市代表车站ID"""
        return self.send_request("get-station-code-of-citys", {"citys": cities})
    
    def get_station_by_name(self, station_names: str):
        """通过车站名获取车站信息"""
        return self.send_request("get-station-code-by-names", {"stationNames": station_names})
    
    def get_station_detail(self, telecode: str):
        """通过车站ID获取详细信息"""
        return self.send_request("get-station-by-telecode", {"telecode": telecode})
    
    # 核心工具方法
    def query_tickets(self, date: str, from_station: str, to_station: str, 
                     train_filter: str = "", show_no_seat: bool = False):
        """查询车票信息"""
        params = {
            "date": date,
            "fromStation": from_station,
            "toStation": to_station,
            "trainFilterFlags": train_filter,
            "showNoSeat": show_no_seat
        }
        return self.send_request("get-tickets", params)
    
    def query_interline_tickets(self, date: str, from_station: str, to_station: str,
                               transfer_station: str = "", train_filter: str = "", 
                               show_no_seat: bool = False):
        """查询中转换乘车票"""
        params = {
            "date": date,
            "fromStation": from_station,
            "toStation": to_station,
            "transferStation": transfer_station,
            "trainFilterFlags": train_filter,
            "showNoSeat": show_no_seat
        }
        return self.send_request("get-interline-tickets", params)
    
    def query_train_route(self, train_no: str, from_station: str, to_station: str, date: str):
        """查询列车经停站"""
        params = {
            "trainNo": train_no,
            "fromStation": from_station,
            "toStation": to_station,
            "date": date
        }
        return self.send_request("get-train-route-stations", params)

def format_date_for_display(date_str: str):
    """格式化日期显示"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        today = datetime.now()
        if date_obj.date() == today.date():
            return f"{date_str} (今天)"
        elif date_obj.date() == today.date() + timedelta(days=1):
            return f"{date_str} (明天)"
        elif date_obj.date() == today.date() + timedelta(days=2):
            return f"{date_str} (后天)"
        else:
            return date_str
    except:
        return date_str

def main():
    client = MCP12306Client()
    
    print("🚄 12306 MCP 客户端")
    print("=" * 50)
    
    # 1. 获取当前日期
    print("1. 获取当前日期...")
    current_date = client.get_current_date()
    if current_date:
        print(f"   当前日期: {format_date_for_display(current_date)}")
    
    # 2. 示例1：直接查询北京到上海的车票
    print("\n2. 直接查询北京到上海的高铁票...")
    tickets_result = client.query_tickets(
        date=current_date,
        from_station="BJP",  # 北京
        to_station="SHH",    # 上海
        train_filter="G"     # 高铁
    )
    
    if tickets_result:
        print(f"   找到 {len(tickets_result)} 个车次")
        for i, ticket in enumerate(tickets_result[:3], 1):  # 只显示前3个
            print(f"   {i}. {ticket.get('train_no', '')} - {ticket.get('from_station_name', '')} → {ticket.get('to_station_name', '')}")
    
    # 3. 示例2：完整的查询流程（城市名 → 车站ID → 车票查询）
    print("\n3. 完整查询流程：广州到深圳...")
    
    # 3.1 获取城市车站代码
    city_codes = client.get_city_station_code("广州|深圳")
    if city_codes:
        guangzhou_code = city_codes.get("广州", {}).get("station_code")
        shenzhen_code = city_codes.get("深圳", {}).get("station_code")
        
        print(f"   广州车站代码: {guangzhou_code}")
        print(f"   深圳车站代码: {shenzhen_code}")
        
        # 3.2 查询车票
        if guangzhou_code and shenzhen_code:
            gz_sz_tickets = client.query_tickets(
                date=current_date,
                from_station=guangzhou_code,
                to_station=shenzhen_code,
                train_filter=""
            )
            
            if gz_sz_tickets:
                print(f"   找到 {len(gz_sz_tickets)} 个车次")
                for i, ticket in enumerate(gz_sz_tickets[:2], 1):
                    print(f"   {i}. {ticket.get('train_no', '')} - {ticket.get('start_time', '')} → {ticket.get('arrive_time', '')}")
    
    # 4. 示例3：查询特定车次的经停站
    print("\n4. 查询列车经停站信息...")
    if tickets_result and len(tickets_result) > 0:
        first_train = tickets_result[0]
        train_no = first_train.get('train_no')
        
        route_info = client.query_train_route(
            train_no=train_no,
            from_station="BJP",
            to_station="SHH", 
            date=current_date
        )
        
        if route_info:
            print(f"   {train_no} 经停站信息:")
            stations = route_info.get('stations', [])
            for station in stations[:5]:  # 只显示前5个站
                print(f"     - {station.get('station_name', '')} ({station.get('arrive_time', '')} → {station.get('start_time', '')})")
    
    # 5. 示例4：中转换乘查询
    print("\n5. 中转换乘查询：北京到广州，经过武汉中转...")
    
    # 5.1 获取武汉车站代码
    wuhan_code = client.get_city_station_code("武汉")
    if wuhan_code and "武汉" in wuhan_code:
        wuhan_station = wuhan_code["武汉"]["station_code"]
        
        interline_result = client.query_interline_tickets(
            date=current_date,
            from_station="BJP",      # 北京
            to_station=guangzhou_code, # 广州
            transfer_station=wuhan_station  # 武汉中转
        )
        
        if interline_result:
            print(f"   找到 {len(interline_result)} 个中转方案")
            for i, plan in enumerate(interline_result[:2], 1):
                first_leg = plan.get('first', {})
                second_leg = plan.get('second', {})
                print(f"   方案 {i}:")
                print(f"     第一程: {first_leg.get('train_no', '')} ({first_leg.get('from_station_name', '')} → {first_leg.get('to_station_name', '')})")
                print(f"     第二程: {second_leg.get('train_no', '')} ({second_leg.get('from_station_name', '')} → {second_leg.get('to_station_name', '')})")
    
    # 6. 车站详细信息查询
    print("\n6. 车站详细信息查询...")
    station_detail = client.get_station_detail("BJP")
    if station_detail:
        print(f"   北京站详细信息:")
        print(f"     - 车站ID: {station_detail.get('station_id', '')}")
        print(f"     - 车站名: {station_detail.get('station_name', '')}")
        print(f"     - 拼音: {station_detail.get('station_pinyin', '')}")
        print(f"     - 城市: {station_detail.get('city', '')}")

def interactive_query():
    """交互式查询示例"""
    client = MCP12306Client()
    
    print("\n🎫 交互式车票查询")
    print("=" * 30)
    
    while True:
        print("\n请选择查询类型:")
        print("1. 直接车票查询")
        print("2. 城市名查询")
        print("3. 中转换乘")
        print("4. 列车经停站")
        print("5. 退出")
        
        choice = input("请输入选择 (1-5): ").strip()
        
        if choice == "1":
            # 直接车票查询
            from_station = input("出发站代码 (如 BJP): ").strip()
            to_station = input("到达站代码 (如 SHH): ").strip()
            date = input("日期 (YYYY-MM-DD, 回车使用今天): ").strip()
            
            if not date:
                date = client.get_current_date()
            
            result = client.query_tickets(date, from_station, to_station)
            if result:
                print(f"\n找到 {len(result)} 个车次:")
                for ticket in result:
                    print(f"  {ticket.get('train_no')} - {ticket.get('from_station_name')} → {ticket.get('to_station_name')}")
        
        elif choice == "2":
            # 城市名查询
            from_city = input("出发城市: ").strip()
            to_city = input("到达城市: ").strip()
            
            city_codes = client.get_city_station_code(f"{from_city}|{to_city}")
            if city_codes:
                from_code = city_codes.get(from_city, {}).get("station_code")
                to_code = city_codes.get(to_city, {}).get("station_code")
                
                if from_code and to_code:
                    result = client.query_tickets(client.get_current_date(), from_code, to_code)
                    if result:
                        print(f"\n找到 {len(result)} 个车次:")
                        for ticket in result[:5]:  # 只显示前5个
                            print(f"  {ticket.get('train_no')} - {ticket.get('start_time')} → {ticket.get('arrive_time')}")
        
        elif choice == "3":
            # 中转换乘
            from_city = input("出发城市: ").strip()
            to_city = input("到达城市: ").strip()
            transfer_city = input("中转城市: ").strip()
            
            city_codes = client.get_city_station_code(f"{from_city}|{to_city}|{transfer_city}")
            if city_codes:
                from_code = city_codes.get(from_city, {}).get("station_code")
                to_code = city_codes.get(to_city, {}).get("station_code")
                transfer_code = city_codes.get(transfer_city, {}).get("station_code")
                
                if all([from_code, to_code, transfer_code]):
                    result = client.query_interline_tickets(
                        client.get_current_date(), from_code, to_code, transfer_code
                    )
                    if result:
                        print(f"\n找到 {len(result)} 个中转方案:")
                        for plan in result:
                            first = plan.get('first', {})
                            second = plan.get('second', {})
                            print(f"  第一程: {first.get('train_no')} | 第二程: {second.get('train_no')}")
        
        elif choice == "4":
            # 列车经停站
            train_no = input("车次号: ").strip()
            from_station = input("出发站代码: ").strip()
            to_station = input("到达站代码: ").strip()
            date = input("日期 (YYYY-MM-DD): ").strip()
            
            result = client.query_train_route(train_no, from_station, to_station, date)
            if result:
                stations = result.get('stations', [])
                print(f"\n{train_no} 经停 {len(stations)} 个车站:")
                for station in stations:
                    print(f"  {station.get('station_name')} - 到达: {station.get('arrive_time')}, 出发: {station.get('start_time')}")
        
        elif choice == "5":
            print("再见！")
            break
        
        else:
            print("无效选择，请重新输入。")

if __name__ == "__main__":
    # 运行示例查询
    main()
    
    # 运行交互式查询
    # interactive_query()