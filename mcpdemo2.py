import requests
import json
import subprocess
import time
import os
from datetime import datetime


class AMapMCPClient:
    def __init__(self, api_key="ec34429b28ceccc8b935d240e33fe20f", 
                 port=8889):
        """
        初始化高德地图MCP客户端
        
        Args:
            api_key (str): 高德地图API密钥
            port (int): 本地服务端口
        """
        self.api_key = api_key
        self.port = port
        self.base_url = f"http://127.0.0.1:{port}/mcp"
        self.session_id = None
        self.initialized = False
        self.process = None

    def start_server(self):
        """
        启动AMap MCP服务器
        
        Returns:
            bool: 启动是否成功
        """
        try:
            # 设置环境变量
            env = os.environ.copy()
            env["AMAP_MAPS_API_KEY"] = self.api_key
            
            # 启动服务进程
            self.process = subprocess.Popen([
                "uvx", "amap-mcp-server", "streamable-http"
            ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # 等待服务启动
            time.sleep(5)
            
            # 检查进程是否仍在运行
            if self.process.poll() is None:
                print("✅ AMap MCP服务器启动成功")
                return True
            else:
                stdout, stderr = self.process.communicate()
                print(f"❌ AMap MCP服务器启动失败")
                print(f"stdout: {stdout.decode()}")
                print(f"stderr: {stderr.decode()}")
                return False
                
        except FileNotFoundError:
            print("❌ 未找到uvx命令，请确保已安装uv工具")
            print("安装方法: ")
            print("  Windows: powershell -ExecutionPolicy ByPass -c \"irm https://astral.sh/uv/install.ps1 | iex\"")
            print("  其他系统: curl -LsSf https://astral.sh/uv/install.sh | sh")
            return False
        except Exception as e:
            print(f"❌ 启动服务器时发生错误: {e}")
            return False

    def stop_server(self):
        """
        停止AMap MCP服务器
        """
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process.wait()
            print("⏹️  AMap MCP服务器已停止")

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
            "User-Agent": "python-amap-mcp-client/1.0.0"
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

        # 如果服务器未启动，则启动它
        if not self.process or self.process.poll() is not None:
            if not self.start_server():
                return False

        payload = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "python-amap-mcp-client",
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
                    "User-Agent": "python-amap-mcp-client/1.0.0"
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
                            "User-Agent": "python-amap-mcp-client/1.0.0",
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

    def geocode(self, address):
        """
        地理编码：将地址转换为经纬度坐标
        
        Args:
            address (str): 地址信息
            
        Returns:
            dict: 地理编码结果或错误信息
        """
        if not self.initialize():
            return {"error": "Failed to initialize"}
            
        return self._send_request("tools/call", {
            "name": "geocode",
            "arguments": {
                "address": address
            }
        }, "geocode")

    def regeocode(self, location):
        """
        逆地理编码：将经纬度坐标转换为地址
        
        Args:
            location (str): 经纬度坐标，格式为 "经度,纬度"
            
        Returns:
            dict: 逆地理编码结果或错误信息
        """
        if not self.initialize():
            return {"error": "Failed to initialize"}
            
        return self._send_request("tools/call", {
            "name": "regeocode",
            "arguments": {
                "location": location
            }
        }, "regeocode")

    def walking_route(self, origin, destination):
        """
        步行路线规划
        
        Args:
            origin (str): 起点坐标，格式为 "经度,纬度"
            destination (str): 终点坐标，格式为 "经度,纬度"
            
        Returns:
            dict: 步行路线规划结果或错误信息
        """
        if not self.initialize():
            return {"error": "Failed to initialize"}
            
        return self._send_request("tools/call", {
            "name": "walking-route",
            "arguments": {
                "origin": origin,
                "destination": destination
            }
        }, "walking_route")

    def driving_route(self, origin, destination, waypoints=None):
        """
        驾车路线规划
        
        Args:
            origin (str): 起点坐标，格式为 "经度,纬度"
            destination (str): 终点坐标，格式为 "经度,纬度"
            waypoints (str): 途经点坐标，格式为 "经度,纬度|经度,纬度"（可选）
            
        Returns:
            dict: 驾车路线规划结果或错误信息
        """
        if not self.initialize():
            return {"error": "Failed to initialize"}
            
        arguments = {
            "origin": origin,
            "destination": destination
        }
        
        if waypoints:
            arguments["waypoints"] = waypoints
            
        return self._send_request("tools/call", {
            "name": "driving-route",
            "arguments": arguments
        }, "driving_route")

    def weather(self, city):
        """
        获取天气信息
        
        Args:
            city (str): 城市名称
            
        Returns:
            dict: 天气信息或错误信息
        """
        if not self.initialize():
            return {"error": "Failed to initialize"}
            
        return self._send_request("tools/call", {
            "name": "weather",
            "arguments": {
                "city": city
            }
        }, "weather")


def query_location(address):
    """
    查询地理位置信息的便捷函数
    
    Args:
        address (str): 地址信息
        
    Returns:
        dict: 查询结果
    """
    # 创建客户端
    client = AMapMCPClient()
    
    try:
        # 地理编码
        result = client.geocode(address)
        return result
    finally:
        # 确保服务器被停止
        client.stop_server()


def main():
    """
    主函数 - 演示如何使用高德地图MCP客户端
    """
    print("🚀 高德地图MCP客户端演示")
    print("=" * 50)
    
    # 创建客户端
    client = AMapMCPClient()
    
    try:
        # 1. 获取工具列表
        print("📋 获取工具列表...")
        tools = client.list_tools()
        if "error" not in tools:
            print("✅ 获取工具列表成功")
            if "result" in tools and "tools" in tools["result"]:
                print("可用工具:")
                for tool in tools["result"]["tools"]:
                    print(f"  - {tool['name']}: {tool.get('description', '无描述')}")
        else:
            print(f"❌ 获取工具列表失败: {tools['error']}")
        
        # 2. 地理编码示例
        print("\n📍 地理编码示例...")
        geocode_result = client.geocode("北京市天安门广场")
        if "error" not in geocode_result:
            print("✅ 地理编码成功")
            print(json.dumps(geocode_result, ensure_ascii=False, indent=2)[:300] + "...")
        else:
            print(f"❌ 地理编码失败: {geocode_result['error']}")
        
        # 3. 逆地理编码示例
        print("\n🗺️ 逆地理编码示例...")
        regeocode_result = client.regeocode("116.397468,39.908832")  # 天安门坐标
        if "error" not in regeocode_result:
            print("✅ 逆地理编码成功")
            print(json.dumps(regeocode_result, ensure_ascii=False, indent=2)[:300] + "...")
        else:
            print(f"❌ 逆地理编码失败: {regeocode_result['error']}")
        
        # 4. 步行路线规划示例
        print("\n🚶 步行路线规划示例...")
        walk_result = client.walking_route("116.397468,39.908832", "116.401284,39.909214")  # 天安门到国家博物馆
        if "error" not in walk_result:
            print("✅ 步行路线规划成功")
            print(json.dumps(walk_result, ensure_ascii=False, indent=2)[:300] + "...")
        else:
            print(f"❌ 步行路线规划失败: {walk_result['error']}")
        
        # 5. 驾车路线规划示例
        print("\n🚗 驾车路线规划示例...")
        drive_result = client.driving_route("116.397468,39.908832", "116.401284,39.909214")  # 天安门到国家博物馆
        if "error" not in drive_result:
            print("✅ 驾车路线规划成功")
            print(json.dumps(drive_result, ensure_ascii=False, indent=2)[:300] + "...")
        else:
            print(f"❌ 驾车路线规划失败: {drive_result['error']}")
        
        # 6. 天气查询示例
        print("\n☀️ 天气查询示例...")
        weather_result = client.weather("北京")
        if "error" not in weather_result:
            print("✅ 天气查询成功")
            print(json.dumps(weather_result, ensure_ascii=False, indent=2)[:300] + "...")
        else:
            print(f"❌ 天气查询失败: {weather_result['error']}")
        
        print("\n✅ 演示完成")
        
    finally:
        # 确保服务器被停止
        client.stop_server()


if __name__ == "__main__":
    main()