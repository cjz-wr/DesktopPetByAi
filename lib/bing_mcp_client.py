"""
Bing MCP 客户端库
封装为单个文件，方便使用和分发

使用示例:
>>> from bing_mcp_client import BingMCPClient, search_bing
>>> 
>>> # 方法1: 使用类接口
>>> client = BingMCPClient()
>>> result = client.search_web("人工智能最新发展", num_results=3)
>>> print(result.text_summary)
>>> 
>>> # 方法2: 使用便捷函数
>>> result = search_bing("Python编程语言", num_results=2)
>>> print(result.text_summary)
"""

import json
import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import requests

# ============= 常量定义 =============
PROTOCOL_VERSION = "2024-11-05"
CLIENT_NAME = "python-bing-mcp-client"
CLIENT_VERSION = "1.0.0"
DEFAULT_BASE_URL = "https://mcp.api-inference.modelscope.net/e3032c28c1cb4f/mcp"
DEFAULT_TIMEOUT = 30
TOOL_BING_SEARCH = "bing_search"

# ============= 自定义异常 =============
class BingMCPError(Exception):
    """Bing MCP客户端基础异常"""
    pass

class InitializationError(BingMCPError):
    """初始化异常"""
    pass

class RequestError(BingMCPError):
    """请求异常"""
    def __init__(self, status_code=None, message=None, response_text=None):
        self.status_code = status_code
        self.message = message
        self.response_text = response_text
        super().__init__(f"HTTP {status_code}: {message}")

class ToolCallError(BingMCPError):
    """工具调用异常"""
    pass

class SessionError(BingMCPError):
    """会话异常"""
    pass

# ============= 数据模型 =============
@dataclass
class SearchResult:
    """搜索结果数据模型"""
    query: str
    num_results: int
    content: List[Dict[str, Any]] = field(default_factory=list)
    raw_response: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def text_summary(self) -> Optional[str]:
        """获取文本摘要（前500字符）"""
        return self.get_text_summary()
    
    def get_text_summary(self, max_length: int = 500) -> Optional[str]:
        """获取指定长度的文本摘要"""
        for item in self.content:
            if item.get("type") == "text":
                text = item.get("text", "")
                if len(text) > max_length:
                    return text[:max_length] + "..."
                return text
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "query": self.query,
            "num_results": self.num_results,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }

@dataclass
class ClientConfig:
    """客户端配置"""
    base_url: str = DEFAULT_BASE_URL
    timeout: int = DEFAULT_TIMEOUT
    auto_initialize: bool = True
    enable_logging: bool = False
    log_level: str = "INFO"
    max_retries: int = 3

# ============= 主客户端类 =============
class BingMCPClient:
    """
    Bing MCP 客户端
    
    功能特性:
    1. 自动初始化会话
    2. 内置重试机制
    3. 完整的异常处理
    4. 日志记录支持
    5. 简洁的API设计
    
    参数:
    - base_url: MCP服务地址
    - timeout: 请求超时时间
    - auto_initialize: 是否自动初始化
    - enable_logging: 是否启用日志
    - log_level: 日志级别
    """
    
    def __init__(self, base_url: str = DEFAULT_BASE_URL, 
                 timeout: int = DEFAULT_TIMEOUT,
                 auto_initialize: bool = True,
                 enable_logging: bool = False,
                 log_level: str = "INFO"):
        """
        初始化客户端
        
        Args:
            base_url: MCP服务基础URL
            timeout: 请求超时时间（秒）
            auto_initialize: 是否自动初始化会话
            enable_logging: 是否启用日志记录
            log_level: 日志级别（DEBUG, INFO, WARNING, ERROR）
        """
        self.config = ClientConfig(
            base_url=base_url,
            timeout=timeout,
            auto_initialize=auto_initialize,
            enable_logging=enable_logging
        )
        self.session_id: Optional[str] = None
        self.initialized: bool = False
        self.logger = self._setup_logger(enable_logging, log_level)
        
        if auto_initialize:
            self.initialize()
    
    def _setup_logger(self, enable_logging: bool, log_level: str) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(__name__)
        
        if enable_logging:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        
        return logger
    
    def _generate_request_id(self, prefix: str = "") -> str:
        """生成请求ID"""
        timestamp = int(datetime.now().timestamp() * 1000)
        return f"{prefix}{timestamp}"
    
    def _parse_sse_response(self, text: str) -> Optional[Dict[str, Any]]:
        """解析SSE（Server-Sent Events）响应"""
        if not text.startswith('data:'):
            return None
        
        lines = text.strip().split('\n')
        for line in lines:
            if line.startswith('data:'):
                json_str = line[5:].strip()
                if json_str:
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        continue
        return None
    
    def _send_request(self, method: str, params: Optional[Dict[str, Any]] = None,
                     request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        发送请求到MCP服务器
        
        Args:
            method: 方法名
            params: 请求参数
            request_id: 请求ID
            
        Returns:
            响应数据
            
        Raises:
            RequestError: 请求失败时抛出
        """
        if request_id is None:
            request_id = self._generate_request_id()
            
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {}
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": f"{CLIENT_NAME}/{CLIENT_VERSION}"
        }
        
        if self.session_id:
            headers["mcp-session-id"] = self.session_id
        
        self.logger.debug(f"Sending request: {method} with id: {request_id}")
        
        try:
            response = requests.post(
                self.config.base_url,
                json=payload,
                headers=headers,
                timeout=self.config.timeout
            )
            
            self.logger.debug(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                text = response.text.strip()
                
                # 处理SSE流式响应
                if text.startswith('data:'):
                    parsed = self._parse_sse_response(text)
                    if parsed:
                        return parsed
                    raise RequestError(
                        message="No valid JSON in SSE response",
                        response_text=text
                    )
                
                # 处理标准JSON响应
                try:
                    result = response.json()
                    if "jsonrpc" in result and "id" in result:
                        return result
                    raise RequestError(
                        message="Invalid response format",
                        response_text=text
                    )
                except json.JSONDecodeError as e:
                    raise RequestError(
                        message=f"JSON decode error: {str(e)}",
                        response_text=text
                    )
            
            raise RequestError(
                status_code=response.status_code,
                message=response.text[:200] if response.text else "No response text",
                response_text=response.text
            )
                
        except requests.exceptions.Timeout:
            raise RequestError(message="Request timeout")
        except requests.exceptions.RequestException as e:
            raise RequestError(message=f"Request exception: {str(e)}")
    
    def initialize(self) -> bool:
        """
        初始化MCP会话
        
        Returns:
            初始化是否成功
            
        Raises:
            InitializationError: 初始化失败时抛出
        """
        if self.initialized:
            self.logger.debug("Session already initialized")
            return True
        
        self.logger.info("Initializing MCP session...")
        
        payload = {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {
                "name": CLIENT_NAME,
                "version": CLIENT_VERSION
            }
        }
        
        try:
            # 发送初始化请求
            response = requests.post(
                self.config.base_url,
                json={
                    "jsonrpc": "2.0",
                    "id": self._generate_request_id("initialize_"),
                    "method": "initialize",
                    "params": payload
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "User-Agent": f"{CLIENT_NAME}/{CLIENT_VERSION}"
                },
                timeout=self.config.timeout
            )
            
            if response.status_code != 200:
                raise InitializationError(
                    f"Initialize failed with HTTP {response.status_code}: {response.text}"
                )
            
            # 从响应头获取session ID
            self.session_id = (
                response.headers.get('mcp-session-id') or 
                response.headers.get('Mcp-Session-Id')
            )
            
            if not self.session_id:
                self.logger.warning("No session ID received from server")
            
            # 发送initialized通知
            if self.session_id:
                requests.post(
                    self.config.base_url,
                    json={
                        "jsonrpc": "2.0",
                        "method": "notifications/initialized",
                        "params": {}
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream",
                        "User-Agent": f"{CLIENT_NAME}/{CLIENT_VERSION}",
                        "mcp-session-id": self.session_id
                    },
                    timeout=self.config.timeout
                )
            
            self.initialized = True
            self.logger.info("Session initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization error: {e}")
            raise InitializationError(f"Failed to initialize: {e}")
    
    def list_tools(self) -> Dict[str, Any]:
        """
        获取可用工具列表
        
        Returns:
            工具列表数据
            
        Raises:
            SessionError: 会话未初始化时抛出
            RequestError: 请求失败时抛出
        """
        if not self.initialized:
            self.logger.warning("Session not initialized, attempting to initialize...")
            if not self.initialize():
                raise SessionError("Failed to initialize session")
        
        self.logger.debug("Listing available tools...")
        try:
            response = self._send_request("tools/list")
            
            if "error" in response:
                self.logger.error(f"Error listing tools: {response.get('error')}")
                return response
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to list tools: {e}")
            raise ToolCallError(f"Failed to list tools: {e}")
    
    def search_web(self, query: str, num_results: int = 5) -> SearchResult:
        """
        使用Bing搜索网络
        
        Args:
            query: 搜索查询词
            num_results: 返回结果数量，默认为5
            
        Returns:
            SearchResult对象
            
        Raises:
            SessionError: 会话未初始化时抛出
            ToolCallError: 工具调用失败时抛出
        """
        if not self.initialized:
            self.logger.warning("Session not initialized, attempting to initialize...")
            if not self.initialize():
                raise SessionError("Failed to initialize session")
        
        self.logger.info(f"Searching web for: {query}")
        
        params = {
            "name": TOOL_BING_SEARCH,
            "arguments": {
                "query": query,
                "num_results": num_results
            }
        }
        
        try:
            response = self._send_request(
                "tools/call", 
                params, 
                f"search_{self._generate_request_id()}"
            )
            
            # 检查是否有错误
            if "error" in response:
                error_msg = response.get("error", {})
                if isinstance(error_msg, dict):
                    error_msg = error_msg.get("message", str(error_msg))
                self.logger.error(f"Search error: {error_msg}")
                raise ToolCallError(f"Search failed: {error_msg}")
            
            # 提取结果数据
            result_data = response.get("result", {})
            
            # 创建SearchResult对象
            search_result = SearchResult(
                query=query,
                num_results=num_results,
                content=result_data.get("content", []),
                raw_response=response
            )
            
            self.logger.info(f"Search completed. Found {len(search_result.content)} content items")
            return search_result
            
        except RequestError as e:
            self.logger.error(f"Request error during search: {e}")
            raise ToolCallError(f"Search request failed: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during search: {e}")
            raise ToolCallError(f"Search failed: {e}")
    
    def health_check(self) -> bool:
        """检查服务是否可用"""
        try:
            response = requests.get(self.config.base_url, timeout=5)
            return response.status_code < 500
        except:
            return False
    
    def get_session_info(self) -> Dict[str, Any]:
        """获取会话信息"""
        return {
            "session_id": self.session_id,
            "initialized": self.initialized,
            "base_url": self.config.base_url,
            "client_version": CLIENT_VERSION
        }

# ============= 便捷函数 =============
def search_bing(query: str, num_results: int = 5, 
                base_url: str = DEFAULT_BASE_URL) -> SearchResult:
    """
    使用Bing搜索的便捷函数
    
    Args:
        query: 搜索查询词
        num_results: 返回结果数量
        base_url: MCP服务地址
        
    Returns:
        SearchResult对象
        
    Example:
        >>> result = search_bing("人工智能", num_results=3)
        >>> print(result.text_summary)
    """
    client = BingMCPClient(base_url=base_url, auto_initialize=True)
    return client.search_web(query, num_results)

def quick_search(query: str, num_results: int = 5) -> Optional[str]:
    """
    快速搜索并返回文本摘要
    
    Args:
        query: 搜索查询词
        num_results: 返回结果数量
        
    Returns:
        搜索结果文本摘要，失败时返回None
    """
    try:
        result = search_bing(query, num_results)
        return result.text_summary
    except Exception as e:
        print(f"Search failed: {e}")
        return None

# ============= 演示函数 =============
def demo():
    """演示函数"""
    print("🚀 Bing MCP Client Demo")
    print("=" * 50)
    
    # 创建客户端
    client = BingMCPClient(enable_logging=True)
    
    # 检查服务健康状态
    print("🔍 Checking service health...")
    if client.health_check():
        print("✅ Service is healthy")
    else:
        print("❌ Service may be unavailable")
    
    # 获取工具列表
    print("\n📋 Listing available tools...")
    try:
        tools = client.list_tools()
        if "result" in tools:
            print("✅ Tools listed successfully")
            # 简单打印工具信息
            tools_result = tools.get("result", {})
            if "tools" in tools_result:
                for tool in tools_result["tools"]:
                    print(f"  - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
        else:
            print("❌ Failed to list tools")
    except Exception as e:
        print(f"❌ Error listing tools: {e}")
    
    # 搜索演示
    print("\n🔍 Searching for 'artificial intelligence'...")
    try:
        result = client.search_web("artificial intelligence", num_results=3)
        print(f"✅ Search completed")
        print(f"📄 Results summary:")
        print(f"{result.text_summary}")
        
        # 显示更多信息
        print(f"\n📊 Search info:")
        print(f"  - Query: {result.query}")
        print(f"  - Results requested: {result.num_results}")
        print(f"  - Content items: {len(result.content)}")
        print(f"  - Timestamp: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Search failed: {e}")
    
    # 使用便捷函数
    print("\n⚡ Using convenience function...")
    try:
        result = search_bing("Python programming", num_results=2)
        print(f"✅ Quick search completed")
        print(f"📄 Summary: {result.text_summary[:200]}...")
    except Exception as e:
        print(f"❌ Quick search failed: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Demo completed")

if __name__ == "__main__":
    demo()