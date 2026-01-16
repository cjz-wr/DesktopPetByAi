import subprocess
import json
import time
import threading
import requests
import os
from datetime import datetime
from pathlib import Path


class ModelScopeMCPClient:
    def __init__(self, url="https://mcp.api-inference.modelscope.net/b8603f1a5b534e/sse"):
        """
        初始化ModelScope MCP客户端
        
        Args:
            url (str): ModelScope MCP服务的SSE URL
        """
        self.url = url
        self.base_url = url
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
            "User-Agent": "python-modelscope-mcp-client/1.0.0"
        }
        
        # 如果已有session_id，则添加到请求头
        if self.session_id:
            headers["mcp-session-id"] = self.session_id

        try:
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code in [200, 202, 204]:
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
                "name": "python-modelscope-mcp-client",
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
                    "User-Agent": "python-modelscope-mcp-client/1.0.0"
                },
                timeout=30
            )
            
            if response.status_code in [200, 202, 204]:
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
                            "User-Agent": "python-modelscope-mcp-client/1.0.0",
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
        if not self.initialized:
            if not self.initialize():
                return {"error": "Failed to initialize"}
            
        return self._send_request("tools/list")

    def call_tool(self, tool_name, arguments=None):
        """
        调用指定工具
        
        Args:
            tool_name (str): 工具名称
            arguments (dict): 工具参数
            
        Returns:
            dict: 工具调用结果或错误信息
        """
        if not self.initialized:
            if not self.initialize():
                return {"error": "Failed to initialize"}
            
        return self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments or {}
        }, f"call_{tool_name}")


def run_modelscope_mcp(url=None, tool_name="fetch", arguments=None):
    """
    运行ModelScope MCP服务的便捷函数
    
    Args:
        url (str): ModelScope MCP服务的URL
        tool_name (str): 要调用的工具名称
        arguments (dict): 工具参数
        
    Returns:
        dict: 调用结果
    """
    # 创建客户端实例
    client = ModelScopeMCPClient(url=url or "https://mcp.api-inference.modelscope.net/b8603f1a5b534e/sse")
    
    try:
        # 获取工具列表
        print("🔍 获取工具列表...")
        tools_result = client.list_tools()
        if "error" in tools_result:
            print(f"❌ 获取工具列表失败: {tools_result['error']}")
        else:
            print("✅ 获取工具列表成功")
            if "result" in tools_result:
                print(f"工具列表: {json.dumps(tools_result['result'], indent=2, ensure_ascii=False)}")
        
        # 调用工具
        print(f"⚙️  调用工具: {tool_name}")
        result = client.call_tool(tool_name, arguments)
        
        return result
        
    except Exception as e:
        print(f"❌ 操作失败: {e}")
        return {"error": str(e)}


def main():
    """
    主函数 - 演示如何使用ModelScope MCP服务
    """
    print("🚀 ModelScope MCP客户端演示")
    print("=" * 50)
    
    # 获取用户输入
    url = input("请输入ModelScope MCP服务的URL (直接回车使用默认): ").strip()
    if not url:
        url = "https://mcp.api-inference.modelscope.net/b8603f1a5b534e/sse"
    
    tool_name = input("请输入要调用的工具名称 (默认: fetch): ").strip()
    if not tool_name:
        tool_name = "fetch"
    
    print(f"\n🔧 连接ModelScope MCP服务...")
    print(f"🌐 URL: {url}")
    print(f"⚙️  工具: {tool_name}")
    
    # 为fetch工具准备参数
    arguments = {}
    if tool_name == "fetch":
        url_to_fetch = input("请输入要获取的URL (例如: https://httpbin.org/get): ").strip()
        if url_to_fetch:
            arguments = {"url": url_to_fetch}
        else:
            arguments = {"url": "https://httpbin.org/get"}
    
    result = run_modelscope_mcp(url=url, tool_name=tool_name, arguments=arguments)
    
    if "error" in result:
        print(f"❌ 工具调用失败: {result['error']}")
        if "message" in result:
            print(f"详细信息: {result['message']}")
    else:
        print("✅ 工具调用成功")
        if "result" in result:
            print(f"工具调用结果: {json.dumps(result['result'], indent=2, ensure_ascii=False)}")
        else:
            print("响应内容:", json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 50)
    print("✅ ModelScope MCP演示完成")


if __name__ == "__main__":
    main()