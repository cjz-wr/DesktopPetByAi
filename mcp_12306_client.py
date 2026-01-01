import requests
import json

class AdvancedMCP12306Client:
    def __init__(self, base_url="http://127.0.0.1:8888"):
        self.base_url = base_url
        self.mcp_endpoint = f"{base_url}/mcp"
    
    def initialize(self):
        """初始化 MCP 会话"""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "python-client",
                    "version": "1.0.0"
                }
            }
        }
        return self._send_request(payload)
    
    def list_tools(self):
        """列出所有工具"""
        payload = {
            "jsonrpc": "2.0", 
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        return self._send_request(payload)
    
    def call_tool(self, tool_name, arguments):
        """调用工具"""
        payload = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        return self._send_request(payload)
    
    def _send_request(self, payload):
        """发送请求到 MCP 服务器"""
        try:
            response = requests.post(self.mcp_endpoint, json=payload, headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'python-mcp-client/1.0.0'
            })
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"请求错误: {e}")
            return None

class MCP12306Client:
    def __init__(self, base_url="http://127.0.0.1:8888"):
        self.client = AdvancedMCP12306Client(base_url)
        # 初始化连接
        self.client.initialize()
    
    def get_current_date(self):
        """获取当前日期"""
        result = self.client.call_tool("mcp_get-current-date", {
            "random_string": "get_current_date"
        })
        if result and "result" in result:
            # 解析结果中的文本内容
            contents = result["result"].get("content", [])
            if contents:
                for item in contents:
                    if item.get("type") == "text":
                        return item.get("text")
        return None
    
    def get_station_code_of_citys(self, citys):
        """获取城市车站代码"""
        result = self.client.call_tool("mcp_get-station-code-of-citys", {
            "citys": citys
        })
        if result and "result" in result:
            contents = result["result"].get("content", [])
            if contents:
                for item in contents:
                    if item.get("type") == "text":
                        try:
                            # 解析JSON格式的结果
                            return json.loads(item.get("text", "{}"))
                        except json.JSONDecodeError:
                            print(f"解析车站代码结果失败: {item.get('text')}")
                            return {}
        return {}
    
    def get_tickets(self, date, from_station, to_station, train_filter_flags=""):
        """查询车票信息"""
        arguments = {
            "date": date,
            "fromStation": from_station,
            "toStation": to_station
        }
        if train_filter_flags:
            arguments["trainFilterFlags"] = train_filter_flags
            
        result = self.client.call_tool("mcp_get-tickets", arguments)
        if result and "result" in result:
            contents = result["result"].get("content", [])
            if contents:
                for item in contents:
                    if item.get("type") == "text":
                        return item.get("text")
        return "未查询到车票信息"

# 完整的使用流程
def main():
    client = AdvancedMCP12306Client()
    
    # 1. 初始化
    print("初始化连接...")
    init_result = client.initialize()
    if init_result and "error" not in init_result:
        print("初始化成功!")
    else:
        print("初始化失败:", init_result)
        return
    
    # 2. 获取可用工具
    print("\n获取可用工具...")
    tools_result = client.list_tools()
    if tools_result and "result" in tools_result:
        tools = tools_result["result"].get("tools", [])
        print(f"找到 {len(tools)} 个工具:")
        for tool in tools:
            print(f"  - {tool.get('name', '未知工具')}: {tool.get('description', '无描述')}")
        
        # 3. 调用工具（使用第一个工具作为示例）
        if tools:
            first_tool = tools[0]
            tool_name = first_tool.get('name')
            print(f"\n尝试调用工具: {tool_name}")
            
            # 根据工具描述猜测参数
            if "query" in tool_name.lower() or "搜索" in tool_name.lower():
                result = client.call_tool(tool_name, {
                    "from_station": "北京",
                    "to_station": "上海",
                    "date": "2024-01-15"
                })
            else:
                result = client.call_tool(tool_name, {})
            
            if result:
                print(f"调用结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    else:
        print("获取工具列表失败")

if __name__ == "__main__":
    main()