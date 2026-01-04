import requests
import json
from datetime import datetime, timedelta


class MCP12306Client:
    def __init__(self, base_url="https://mcp.api-inference.modelscope.net/b822d06c4c7345/mcp"):
        """
        初始化MCP 12306客户端
        
        Args:
            base_url (str): MCP服务的基础URL
        """
        self.base_url = base_url
        self.session_id = None
        self.initialized = False

    def _send_request(self, method, params=None, request_id=None):
        """
        发送请求到MCP服务器
        
        Args:
            method (str): 要调用的方法名
            params (dict): 方法参数
            request_id (str): 请求ID
            
        Returns:
            dict: 服务器响应
        """
        if request_id is None:
            request_id = str(int(datetime.now().timestamp() * 1000))
            
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {}
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": "python-mcp-client/1.0.0"
        }
        
        # 如果已有session_id，则添加到请求头
        if self.session_id:
            headers["mcp-session-id"] = self.session_id

        try:
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                text = response.text.strip()
                
                if text.startswith('data:'):
                    json_str = text.split('data:', 1)[1].split('\n')[0].strip()
                    if json_str:
                        return json.loads(json_str)
                    else:
                        return {"error": "Empty response"}
                else:
                    return response.json()
            else:
                return {"error": f"HTTP {response.status_code}", "message": response.text}
                
        except requests.exceptions.RequestException as e:
            return {"error": "RequestException", "message": str(e)}
        except json.JSONDecodeError as e:
            return {"error": "JSONDecodeError", "message": str(e), "raw_response": response.text}
        except Exception as e:
            return {"error": "Exception", "message": str(e)}

    def initialize(self):
        """
        初始化MCP会话
        
        Returns:
            bool: 初始化是否成功
        """
        if self.initialized:
            return True

        payload = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "python-mcp-client",
                "version": "1.0.0"
            }
        }

        try:
            response = requests.post(
                self.base_url,
                json={
                    "jsonrpc": "2.0",
                    "id": "initialize_" + str(int(datetime.now().timestamp() * 1000)),
                    "method": "initialize",
                    "params": payload
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "User-Agent": "python-mcp-client/1.0.0"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                # 从响应头获取session ID
                self.session_id = response.headers.get('mcp-session-id')
                
                # 发送initialized通知
                if self.session_id:
                    notify_response = requests.post(
                        self.base_url,
                        json={
                            "jsonrpc": "2.0",
                            "method": "notifications/initialized",
                            "params": {}
                        },
                        headers={
                            "Content-Type": "application/json",
                            "Accept": "application/json, text/event-stream",
                            "User-Agent": "python-mcp-client/1.0.0",
                            "mcp-session-id": self.session_id
                        },
                        timeout=30
                    )
                    
                self.initialized = True
                return True
            else:
                print(f"初始化失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"初始化异常: {e}")
            return False

    def list_tools(self):
        """
        获取可用工具列表
        
        Returns:
            dict: 工具列表或错误信息
        """
        if not self.initialize():
            return {"error": "Failed to initialize"}
            
        return self._send_request("tools/list")

    def get_current_date(self):
        """
        获取当前日期
        
        Returns:
            dict: 当前日期信息或错误信息
        """
        if not self.initialize():
            return {"error": "Failed to initialize"}
            
        return self._send_request("tools/call", {
            "name": "get-current-date",
            "arguments": {}
        }, "get_current_date")

    def get_station_codes(self, cities):
        """
        获取城市车站代码
        
        Args:
            cities (str): 城市名称，多个城市用'|'分隔
            
        Returns:
            dict: 车站代码信息或错误信息
        """
        if not self.initialize():
            return {"error": "Failed to initialize"}
            
        return self._send_request("tools/call", {
            "name": "get-station-code-of-citys",
            "arguments": {
                "citys": cities
            }
        }, "get_station_codes")

    def query_tickets(self, date, from_station, to_station):
        """
        查询车票信息
        
        Args:
            date (str): 查询日期，格式为 YYYY-MM-DD
            from_station (str): 出发车站代码
            to_station (str): 到达车站代码
            
        Returns:
            dict: 车票信息或错误信息
        """
        if not self.initialize():
            return {"error": "Failed to initialize"}
            
        return self._send_request("tools/call", {
            "name": "get-tickets",
            "arguments": {
                "date": date,
                "fromStation": from_station,
                "toStation": to_station
            }
        }, "query_tickets")

    def query_interline_tickets(self, date, from_station, to_station, middle_station=""):
        """
        查询中转车票信息
        
        Args:
            date (str): 查询日期，格式为 YYYY-MM-DD
            from_station (str): 出发车站代码
            to_station (str): 到达车站代码
            middle_station (str): 中转车站代码（可选）
            
        Returns:
            dict: 中转车票信息或错误信息
        """
        if not self.initialize():
            return {"error": "Failed to initialize"}
            
        arguments = {
            "date": date,
            "fromStation": from_station,
            "toStation": to_station
        }
        
        if middle_station:
            arguments["middleStation"] = middle_station
            
        return self._send_request("tools/call", {
            "name": "get-interline-tickets",
            "arguments": arguments
        }, "query_interline_tickets")


def query_12306_tickets(from_city="北京", to_city="上海", date="tomorrow"):
    """
    查询12306车票信息的便捷函数
    
    Args:
        from_city (str): 出发城市
        to_city (str): 到达城市
        date (str): 查询日期，支持 today/tomorrow/after_tomorrow 或 YYYY-MM-DD 格式
        
    Returns:
        dict: 查询结果
    """
    # 处理相对日期
    if date == "today":
        query_date = datetime.now().strftime("%Y-%m-%d")
    elif date == "tomorrow":
        query_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    elif date == "after_tomorrow":
        query_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    else:
        query_date = date
    
    # 创建客户端
    client = MCP12306Client()
    
    # 获取城市车站代码
    stations_result = client.get_station_codes(f"{from_city}|{to_city}")
    
    if "error" in stations_result:
        return stations_result
    
    # 解析车站代码
    from_station_code = None
    to_station_code = None
    
    if "result" in stations_result:
        contents = stations_result["result"].get("content", [])
        for item in contents:
            if item.get("type") == "text":
                try:
                    station_data = json.loads(item.get("text", "{}"))
                    from_station_code = station_data.get(from_city, {}).get("station_code")
                    to_station_code = station_data.get(to_city, {}).get("station_code")
                    break
                except json.JSONDecodeError:
                    pass
    
    if not from_station_code or not to_station_code:
        return {"error": "Failed to get station codes"}
    
    # 查询车票
    tickets_result = client.query_tickets(query_date, from_station_code, to_station_code)
    return tickets_result


def main():
    """
    主函数 - 演示如何使用函数接口
    """
    print("🚀 MCP 12306客户端函数接口演示")
    print("=" * 50)
    
    # 使用便捷函数查询车票
    print("🔍 使用便捷函数查询北京到上海的车票（明天）...")
    result = query_12306_tickets("北京", "上海", "2026-01-06")
    
    if "error" in result:
        print(f"❌ 查询失败: {result['error']}")
        if "message" in result:
            print(f"详细信息: {result['message']}")
    else:
        print("✅ 查询成功")
        if "result" in result:
            contents = result["result"].get("content", [])
            for item in contents:
                if item.get("type") == "text":
                    ticket_text = item.get("text", "")
                    print(f"\n📄 车票信息摘要 (前500字符):")
                    print(ticket_text[:500] + ("..." if len(ticket_text) > 500 else ""))
                    break
    
    print("\n" + "=" * 50)
    
    # 使用类接口进行更详细的查询
    print("🔧 使用类接口进行详细查询...")
    client = MCP12306Client()
    
    # 获取工具列表
    print("📋 获取工具列表...")
    tools = client.list_tools()
    if "error" not in tools:
        print("✅ 获取工具列表成功")
    else:
        print(f"❌ 获取工具列表失败: {tools['error']}")
    
    # 获取当前日期
    print("📅 获取当前日期...")
    current_date = client.get_current_date()
    if "error" not in current_date:
        print("✅ 获取当前日期成功")
    else:
        print(f"❌ 获取当前日期失败: {current_date['error']}")
    
    print("\n✅ 演示完成")


if __name__ == "__main__":
    main()