
import subprocess
import json
import time
import threading
import requests
import os
from datetime import datetime
from pathlib import Path


class Text2ImageMCPClient:
    def __init__(self, directory_path=None, server_port=8888):
        """
        初始化Text2Image MCP客户端
        
        Args:
            directory_path (str): text2image服务的目录路径
            server_port (int): 本地服务器端口
        """
        # 如果没有指定目录，尝试自动查找text2image.py
        if directory_path is None:
            self.directory_path = self._find_text2image_script()
        else:
            self.directory_path = os.path.abspath(directory_path)
        
        self.server_port = server_port
        self.base_url = f"http://127.0.0.1:{server_port}/mcp"
        self.session_id = None
        self.initialized = False
        self.process = None
        self.server_running = False

    def _find_text2image_script(self):
        """
        自动查找text2image.py文件
        """
        # 首先在当前工作目录查找
        current_dir = os.getcwd()
        script_path = os.path.join(current_dir, "text2image.py")
        if os.path.exists(script_path):
            return current_dir
        
        # 然后在当前脚本所在目录查找
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, "text2image.py")
        if os.path.exists(script_path):
            return script_dir
        
        # 如果都没找到，返回当前脚本所在目录
        return script_dir

    def start_local_server(self):
        """
        启动本地text2image服务
        """
        try:
            # 确保目录路径存在
            if not os.path.exists(self.directory_path):
                print(f"❌ 目录不存在: {self.directory_path}")
                return False
            
            # 检查text2image.py文件是否存在
            text2image_script = os.path.join(self.directory_path, "text2image.py")
            if not os.path.exists(text2image_script):
                print(f"❌ text2image.py文件不存在: {text2image_script}")
                print("💡 提示: 请确保text2image.py文件存在于指定目录中")
                return False
            
            # 使用uv命令运行text2image服务
            cmd = ["uv", "run", "text2image.py"]
            
            # 在指定目录中启动服务
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.directory_path  # 设置工作目录
            )
            
            print(f"✅ 正在启动text2image服务，进程ID: {self.process.pid}")
            print(f"📁 服务目录: {self.directory_path}")
            
            # 等待服务启动，最多等待15秒
            timeout = 15
            start_time = time.time()
            while time.time() - start_time < timeout:
                # 检查进程是否仍然运行
                if self.process.poll() is not None:
                    stdout, stderr = self.process.communicate()
                    print(f"❌ 服务启动失败，错误信息: {stderr}")
                    return False
                
                # 尝试连接到服务，看是否已启动
                try:
                    response = requests.get(f"http://127.0.0.1:{self.server_port}/health", timeout=2)
                    if response.status_code == 200:
                        print("✅ 服务已成功启动并响应")
                        self.server_running = True
                        return True
                except requests.exceptions.RequestException:
                    pass  # 服务可能尚未完全启动，继续等待
                
                time.sleep(1)
            
            # 如果超时仍未启动成功
            if not self.server_running:
                print(f"❌ 服务启动超时 ({timeout}秒)")
                self.stop_local_server()
                return False
                
        except FileNotFoundError:
            print("❌ 未找到uv命令，请确保已安装uv并添加到系统PATH中")
            print("💡 提示: 可以通过 'pip install uv' 安装uv")
            return False
        except Exception as e:
            print(f"❌ 启动text2image服务失败: {e}")
            return False

    def stop_local_server(self):
        """
        停止本地text2image服务
        """
        if self.process and self.server_running:
            try:
                print("🛑 正在停止text2image服务...")
                self.process.terminate()  # 优雅终止
                try:
                    self.process.wait(timeout=5)  # 等待最多5秒
                except subprocess.TimeoutExpired:
                    print("⚠️ 服务未在5秒内停止，强制终止...")
                    self.process.kill()  # 强制终止
            except Exception as e:
                print(f"❌ 停止服务时出错: {e}")
            finally:
                self.server_running = False
                print("✅ text2image服务已停止")

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
            "User-Agent": "python-text2image-mcp-client/1.0.0"
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
                "name": "python-text2image-mcp-client",
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
                    "User-Agent": "python-text2image-mcp-client/1.0.0"
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
                            "Accept": "application/json, text-event-stream",
                            "User-Agent": "python-text2image-mcp-client/1.0.0",
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

    def generate_image(self, prompt, width=512, height=512, negative_prompt=""):
        """
        生成图像
        
        Args:
            prompt (str): 图像生成的提示文本
            width (int): 图像宽度
            height (int): 图像高度
            negative_prompt (str): 负面提示文本
            
        Returns:
            dict: 图像生成结果或错误信息
        """
        if not self.initialized:
            if not self.initialize():
                return {"error": "Failed to initialize"}
            
        return self._send_request("tools/call", {
            "name": "text-to-image",
            "arguments": {
                "prompt": prompt,
                "width": width,
                "height": height,
                "negative_prompt": negative_prompt
            }
        }, "generate_image")


def run_text2image_mcp(directory_path=None, prompt="a beautiful landscape"):
    """
    运行text2image MCP服务的便捷函数
    
    Args:
        directory_path (str): text2image服务的目录路径
        prompt (str): 图像生成的提示文本
        
    Returns:
        dict: 生成结果
    """
    # 创建客户端实例
    client = Text2ImageMCPClient(directory_path=directory_path)
    
    # 启动本地服务
    if not client.start_local_server():
        return {"error": "Failed to start local server"}
    
    try:
        # 确保服务已启动后等待一点时间
        time.sleep(3)
        
        # 获取工具列表
        tools_result = client.list_tools()
        if "error" in tools_result:
            print(f"❌ 获取工具列表失败: {tools_result['error']}")
        else:
            print("✅ 获取工具列表成功")
        
        # 生成图像
        print(f"🖼️ 正在生成图像，提示: {prompt}")
        result = client.generate_image(prompt)
        
        return result
        
    finally:
        # 确保服务被正确停止
        client.stop_local_server()


def main():
    """
    主函数 - 演示如何使用text2image MCP服务
    """
    print("🚀 Text2Image MCP客户端演示")
    print("=" * 50)
    
    # 获取用户输入，如果为空则使用自动查找
    directory_path = input("请输入text2image服务的目录路径 (直接回车使用自动查找): ").strip()
    if not directory_path:
        directory_path = None  # 使用自动查找
    
    prompt = input("请输入图像生成的提示 (默认: a beautiful landscape): ").strip()
    if not prompt:
        prompt = "a beautiful landscape"
    
    print(f"\n🔧 启动text2image MCP服务...")
    if directory_path:
        print(f"📁 目录路径: {directory_path}")
    else:
        print("📁 目录路径: 自动查找")
    print(f"💡 提示: {prompt}")
    
    result = run_text2image_mcp(directory_path=directory_path, prompt=prompt)
    
    if "error" in result:
        print(f"❌ 图像生成失败: {result['error']}")
        if "message" in result:
            print(f"详细信息: {result['message']}")
    else:
        print("✅ 图像生成成功")
        if "result" in result:
            print(f"图像生成结果: {result['result']}")
        else:
            print("响应内容:", json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 50)
    print("✅ Text2Image MCP演示完成")


if __name__ == "__main__":
    main()