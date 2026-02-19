"""
MCP管理器模块
负责管理MCP服务器连接、工具调用和配置管理
"""

import json
import os
import asyncio
import logging
from typing import Dict, List, Any, Optional
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from datetime import datetime

# MCP相关导入
try:
    from mcp import ClientSession
    from mcp.client.sse import sse_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logging.warning("MCP库未安装，MCP功能将不可用")

@dataclass
class MCPServerConfig:
    """MCP服务器配置"""
    name: str
    type: str  # sse, stdio等
    url: str
    enabled: bool = True
    timeout: int = 30

@dataclass
class MCPTool:
    """MCP工具信息"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str

class MCPManager:
    """MCP管理器主类"""
    
    def __init__(self, config_file: str = "mcp_config.json"):
        self.config_file = config_file
        self.servers: Dict[str, MCPServerConfig] = {}
        self.tools: Dict[str, MCPTool] = {}
        self.sessions: Dict[str, ClientSession] = {}
        self.stack = AsyncExitStack()
        self.logger = logging.getLogger(__name__)
        
        # 加载配置
        self.load_config()
        
    def load_config(self):
        """加载MCP配置文件"""
        if not os.path.exists(self.config_file):
            self.create_default_config()
            return
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # 解析服务器配置
            mcp_servers = config.get('mcpServers', {})
            for name, server_info in mcp_servers.items():
                self.servers[name] = MCPServerConfig(
                    name=name,
                    type=server_info.get('type', 'sse'),
                    url=server_info.get('url', ''),
                    enabled=server_info.get('enabled', True),
                    timeout=server_info.get('timeout', 30)
                )
                
            self.logger.info(f"已加载 {len(self.servers)} 个MCP服务器配置")
            
        except Exception as e:
            self.logger.error(f"加载MCP配置失败: {e}")
            self.create_default_config()
    
    def create_default_config(self):
        """创建默认MCP配置"""
        default_config = {
            "mcpServers": {
                "bing-search": {
                    "type": "sse",
                    "url": "https://mcp.api-inference.modelscope.net/e3032c28c1cb4f/mcp",
                    "enabled": True,
                    "timeout": 30
                }
            },
            "defaultTools": ["bing_search"],
            "timeout": 30
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            self.logger.info("已创建默认MCP配置文件")
        except Exception as e:
            self.logger.error(f"创建默认配置文件失败: {e}")
    
    async def initialize(self):
        """初始化所有MCP服务器连接"""
        if not MCP_AVAILABLE:
            self.logger.warning("MCP库不可用，跳过初始化")
            return False
            
        if not self.servers:
            self.logger.info("没有配置MCP服务器")
            return True
            
        success_count = 0
        for name, server in self.servers.items():
            if not server.enabled:
                continue
                
            try:
                await self.connect_server(name, server)
                success_count += 1
                self.logger.info(f"✅ 成功连接MCP服务器: {name}")
            except Exception as e:
                self.logger.error(f"❌ 连接MCP服务器 {name} 失败: {e}")
        
        self.logger.info(f"MCP初始化完成，成功连接 {success_count}/{len([s for s in self.servers.values() if s.enabled])} 个服务器")
        return success_count > 0
    
    async def connect_server(self, name: str, server: MCPServerConfig):
        """连接单个MCP服务器"""
        if server.type != "sse":
            raise ValueError(f"不支持的服务器类型: {server.type}")
            
        # 建立SSE连接
        streams = await self.stack.enter_async_context(sse_client(url=server.url))
        session = await self.stack.enter_async_context(ClientSession(streams[0], streams[1]))
        await session.initialize()
        
        # 获取工具列表
        tools_result = await session.list_tools()
        tools = tools_result.tools
        
        # 缓存工具信息
        for tool in tools:
            mcp_tool = MCPTool(
                name=tool.name,
                description=tool.description,
                input_schema=tool.inputSchema,
                server_name=name
            )
            self.tools[tool.name] = mcp_tool
        
        # 保存会话
        self.sessions[name] = session
    
    def get_available_tools(self) -> List[MCPTool]:
        """获取所有可用工具"""
        return list(self.tools.values())
    
    def get_tools_for_openai(self) -> List[Dict[str, Any]]:
        """转换为OpenAI工具格式"""
        openai_tools = []
        for tool in self.tools.values():
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema
                }
            })
        return openai_tools
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """调用指定工具"""
        if tool_name not in self.tools:
            self.logger.warning(f"工具 {tool_name} 不存在")
            return None
            
        tool = self.tools[tool_name]
        session = self.sessions.get(tool.server_name)
        
        if not session:
            self.logger.warning(f"服务器 {tool.server_name} 未连接")
            return None
            
        try:
            result = await session.call_tool(tool_name, arguments=arguments)
            if result.content and hasattr(result.content[0], 'text'):
                return result.content[0].text
            else:
                return json.dumps(result.content, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"调用工具 {tool_name} 失败: {e}")
            return f"工具调用失败: {e}"
    
    def add_server(self, name: str, server_config: Dict[str, Any]) -> bool:
        """添加新的MCP服务器"""
        try:
            # 更新内存配置
            self.servers[name] = MCPServerConfig(
                name=name,
                type=server_config.get('type', 'sse'),
                url=server_config.get('url', ''),
                enabled=server_config.get('enabled', True),
                timeout=server_config.get('timeout', 30)
            )
            
            # 更新配置文件
            self.save_config()
            return True
        except Exception as e:
            self.logger.error(f"添加服务器失败: {e}")
            return False
    
    def remove_server(self, name: str) -> bool:
        """移除MCP服务器"""
        if name in self.servers:
            del self.servers[name]
            # 也移除相关工具
            tools_to_remove = [tool_name for tool_name, tool in self.tools.items() 
                             if tool.server_name == name]
            for tool_name in tools_to_remove:
                del self.tools[tool_name]
            
            self.save_config()
            return True
        return False
    
    def save_config(self):
        """保存配置到文件"""
        config = {
            "mcpServers": {},
            "timeout": 30
        }
        
        for name, server in self.servers.items():
            config["mcpServers"][name] = {
                "type": server.type,
                "url": server.url,
                "enabled": server.enabled,
                "timeout": server.timeout
            }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
    
    async def cleanup(self):
        """清理资源"""
        try:
            await self.stack.aclose()
            self.sessions.clear()
            self.tools.clear()
            self.logger.info("MCP管理器资源已清理")
        except Exception as e:
            self.logger.error(f"清理资源失败: {e}")

# 便捷函数
async def create_mcp_manager(config_file: str = "mcp_config.json") -> MCPManager:
    """创建并初始化MCP管理器"""
    manager = MCPManager(config_file)
    await manager.initialize()
    return manager