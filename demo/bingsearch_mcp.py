import requests
import json
from datetime import datetime


class BingMCPClient:
    def __init__(self, base_url="https://mcp.api-inference.modelscope.net/e3032c28c1cb4f/mcp"):
        """
        初始化Bing-CN-MCP客户端
        
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
            "User-Agent": "python-bing-mcp-client/1.0.0"
        }
        
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
                "name": "python-bing-mcp-client",
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
                    "User-Agent": "python-bing-mcp-client/1.0.0"
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
                            "User-Agent": "python-bing-mcp-client/1.0.0",
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

    def search_web(self, query, num_results=5):
        """
        使用Bing搜索网络
        
        Args:
            query (str): 搜索查询
            num_results (int): 返回结果数量，默认为5
            
        Returns:
            dict: 搜索结果或错误信息
        """
        if not self.initialize():
            return {"error": "Failed to initialize"}
            
        params = {
            "name": "bing_search",
            "arguments": {
                "query": query,
                "num_results": num_results
            }
        }
        
        return self._send_request("tools/call", params, f"search_{int(datetime.now().timestamp())}")


def search_bing(query, num_results=5):
    """
    使用Bing搜索的便捷函数
    
    Args:
        query (str): 搜索查询
        num_results (int): 返回结果数量
        
    Returns:
        dict: 搜索结果
    """
    client = BingMCPClient()
    result = client.search_web(query, num_results)
    return result


def main():
    """
    主函数 - 演示如何使用Bing-CN-MCP服务
    """
    print("🚀 Bing-CN-MCP客户端演示")
    print("=" * 50)
    
    # 创建客户端
    client = BingMCPClient()
    
    # 获取工具列表
    print("📋 获取可用工具列表...")
    tools = client.list_tools()
    if "error" not in tools:
        print("✅ 获取工具列表成功")
        if "result" in tools:
            print(f"工具列表: {tools['result']}")
    else:
        print(f"❌ 获取工具列表失败: {tools['error']}")
        if "message" in tools:
            print(f"详细信息: {tools['message']}")
    
    print("\n" + "-" * 30)
    
    # 使用便捷函数搜索
    print("🔍 使用便捷函数搜索 '人工智能最新发展' ...")
    result = search_bing("人工智能最新发展", num_results=3)
    
    if "error" in result:
        print(f"❌ 搜索失败: {result['error']}")
        if "message" in result:
            print(f"详细信息: {result['message']}")
    else:
        print("✅ 搜索成功")
        if "result" in result:
            contents = result["result"].get("content", [])
            for item in contents:
                if item.get("type") == "text":
                    search_text = item.get("text", "")
                    print(f"\n📄 搜索结果摘要 (前500字符):")
                    print(search_text[:500] + ("..." if len(search_text) > 500 else ""))
                    break
        else:
            print("未找到搜索结果内容")
    
    print("\n" + "-" * 30)
    
    # 使用类接口进行搜索
    print("🔧 使用类接口搜索 'Python编程语言' ...")
    search_result = client.search_web("Python编程语言", num_results=2)
    
    if "error" not in search_result:
        print("✅ 搜索成功")
        if "result" in search_result:
            contents = search_result["result"].get("content", [])
            for item in contents:
                if item.get("type") == "text":
                    search_text = item.get("text", "")
                    print(f"\n📄 搜索结果摘要 (前500字符):")
                    print(search_text[:500] + ("..." if len(search_text) > 500 else ""))
                    break
    else:
        print(f"❌ 搜索失败: {search_result['error']}")
        if "message" in search_result:
            print(f"详细信息: {search_result['message']}")
    
    print("\n" + "=" * 50)
    print("✅ Bing-CN-MCP演示完成")


if __name__ == "__main__":
    main()