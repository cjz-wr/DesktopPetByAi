import requests
import json
from datetime import datetime


class GenericMCPClient:
    def __init__(self, base_url, api_key=None):
        """
        初始化通用MCP客户端
        
        Args:
            base_url (str): MCP服务的基础URL
            api_key (str): API密钥（可选）
        """
        self.base_url = base_url
        self.session_id = None
        self.initialized = False
        self.api_key = api_key

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
            "User-Agent": "python-generic-mcp-client/1.0.0"
        }
        
        # 添加API密钥（如果提供）
        if self.api_key:
            headers["Authorization"] = self.api_key
            
        # 如果已有session_id，则添加到请求头
        if self.session_id:
            headers["mcp-session-id"] = self.session_id

        try:
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                text = response.text.strip()
                
                if text.startswith('data:'):
                    # 处理SSE流式响应
                    lines = text.split('\n')
                    for line in lines:
                        if line.startswith('data:'):
                            json_str = line[5:].strip()  # 移除 'data:' 前缀
                            if json_str:
                                try:
                                    return json.loads(json_str)
                                except json.JSONDecodeError:
                                    continue
                    return {"error": "No valid JSON in SSE response"}
                else:
                    # 直接JSON响应
                    try:
                        return response.json()
                    except json.JSONDecodeError:
                        return {"error": "Invalid JSON response", "raw_response": response.text}
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
                "name": "python-generic-mcp-client",
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
                    "User-Agent": "python-generic-mcp-client/1.0.0"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                # 从响应头获取session ID
                self.session_id = response.headers.get('mcp-session-id') or response.headers.get('Mcp-Session-Id')
                
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
                            "User-Agent": "python-generic-mcp-client/1.0.0",
                            "mcp-session-id": self.session_id
                        },
                        timeout=30
                    )
                    
                self.initialized = True
                return True
            else:
                print(f"初始化失败: HTTP {response.status_code}")
                print(f"响应内容: {response.text}")
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

    def call_tool(self, tool_name, arguments):
        """
        调用指定工具
        
        Args:
            tool_name (str): 工具名称
            arguments (dict): 工具参数
            
        Returns:
            dict: 工具调用结果
        """
        if not self.initialize():
            return {"error": "Failed to initialize"}
            
        params = {
            "name": tool_name,
            "arguments": arguments
        }
        
        return self._send_request("tools/call", {"name": tool_name, "arguments": arguments})


def call_mcp_interface(base_url, api_key=None, tool_name=None, arguments=None):
    """
    通用MCP接口调用函数
    
    Args:
        base_url (str): MCP服务的基础URL
        api_key (str): API密钥（可选）
        tool_name (str): 工具名称（可选，如果为None则只初始化会话）
        arguments (dict): 工具参数（可选）
        
    Returns:
        dict: 调用结果
    """
    client = GenericMCPClient(base_url, api_key)
    
    if tool_name is None:
        # 仅初始化会话
        success = client.initialize()
        return {"success": success, "session_id": client.session_id}
    
    # 调用指定工具
    result = client.call_tool(tool_name, arguments or {})
    return result


def interactive_mcp_call():
    """
    交互式MCP接口调用函数
    允许用户输入任意MCP接口参数并获取结果
    """
    print("🚀 交互式MCP接口调用")
    print("=" * 50)
    
    # 获取用户输入
    print("请输入MCP接口信息：")
    
    base_url = input("MCP服务URL (例如: https://open.bigmodel.cn/api/mcp/web_search/sse): ").strip()
    if not base_url:
        print("❌ URL不能为空")
        return
    
    api_key = input("API密钥 (可选，直接回车跳过): ").strip()
    if not api_key:
        api_key = None
    
    # 如果API密钥存在，尝试构建合适的头部
    if api_key:
        # 假设是Bearer token格式
        if not api_key.lower().startswith(('bearer', 'apikey', 'token')):
            api_key = f"Bearer {api_key}"
    
    tool_name = input("工具名称 (例如: web_search): ").strip()
    if not tool_name:
        print("❌ 工具名称不能为空")
        return
    
    print("工具参数 (JSON格式，例如: {\"query\": \"搜索内容\"})")
    arguments_input = input("参数: ").strip()
    
    try:
        # 尝试解析JSON参数
        if arguments_input:
            arguments = json.loads(arguments_input)
        else:
            arguments = {}
    except json.JSONDecodeError as e:
        print(f"❌ JSON参数格式错误: {e}")
        print("使用空参数继续...")
        arguments = {}
    
    print("\n🔧 正在调用MCP接口...")
    print(f"URL: {base_url}")
    print(f"工具: {tool_name}")
    print(f"参数: {arguments}")
    
    # 调用接口
    client = GenericMCPClient(base_url, api_key)
    result = client.call_tool(tool_name, arguments)
    
    print("\n📈 调用结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    """
    主函数 - 演示如何使用通用MCP接口调用
    """
    print("🚀 通用MCP客户端演示")
    print("=" * 50)
    
    while True:
        print("\n请选择操作:")
        print("1. 交互式调用MCP接口")
        print("2. 查看使用示例")
        print("3. 退出")
        
        choice = input("请输入选择 (1/2/3): ").strip()
        
        if choice == "1":
            interactive_mcp_call()
        elif choice == "2":
            # 示例1: 调用智谱Web搜索SSE接口
            print("\n🔍 示例: 调用12306 MCP接口")
            mcp_12306_url = "https://mcp.api-inference.modelscope.net/b822d06c4c7345/mcp"
            client = GenericMCPClient(mcp_12306_url)
            
            # 获取工具列表
            print("📋 获取工具列表...")
            tools = client.list_tools()
            if "error" not in tools:
                print("✅ 获取工具列表成功")
                if "result" in tools and "content" in tools["result"]:
                    print(f"工具列表: {tools['result']['content']}")
            else:
                print(f"❌ 获取工具列表失败: {tools['error']}")
                if "message" in tools:
                    print(f"详细信息: {tools['message']}")
        elif choice == "3":
            print("\n👋 退出程序")
            break
        else:
            print("\n❌ 无效选择，请重新输入")


if __name__ == "__main__":
    main()