"""
插件管理器 - 负责插件数据的读写和管理
"""

import json
import os
from typing import Dict, Any, List
import logging
from pathlib import Path

class PluginManager:
    """插件管理核心类"""
    
    def __init__(self, skill_file_path="yyskills/skill_list.json"):
        """
        初始化插件管理器
        
        Args:
            skill_file_path (str): 插件数据文件路径
        """
        self.skill_file_path = skill_file_path
        self.plugins = {}
        self.logger = logging.getLogger(__name__)
        self.load_plugins()
    
    def load_plugins(self) -> bool:
        """
        从JSON文件加载插件数据
        
        Returns:
            bool: 加载成功返回True，失败返回False
        """
        try:
            # 确保目录存在
            skill_dir = os.path.dirname(self.skill_file_path)
            if skill_dir and not os.path.exists(skill_dir):
                os.makedirs(skill_dir)
            
            # 如果文件不存在，创建默认文件
            if not os.path.exists(self.skill_file_path):
                self._create_default_skill_file()
                return True
            
            # 读取插件数据
            with open(self.skill_file_path, 'r', encoding='utf-8') as f:
                self.plugins = json.load(f)
            
            self.logger.info(f"成功加载 {len(self.plugins)} 个插件")
            return True
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析错误: {e}")
            self.plugins = {}
            return False
        except Exception as e:
            self.logger.error(f"加载插件数据失败: {e}")
            self.plugins = {}
            return False
    
    def _create_default_skill_file(self):
        """创建默认的技能文件"""
        default_plugins = {
            "get_time": {
                "discription": "获取当前系统的时间",
                "format": "[USESKILLS:GetTime:GetTime]",
                "usage": "必须按固定格式执行该技能",
                "attention": "该技能会返回当前系统的时间信息",
                "AI_can_use": True,
                "detailed_info": False
            },
            "test_skill": {
                "discription": "测试技能描述",
                "format": "[TEST:test]",
                "usage": "这是一个测试技能",
                "attention": "仅供测试使用",
                "AI_can_use": True,
                "detailed_info": True
            }
        }
        
        try:
            with open(self.skill_file_path, 'w', encoding='utf-8') as f:
                json.dump(default_plugins, f, ensure_ascii=False, indent=4)
            self.plugins = default_plugins
            self.logger.info("创建默认技能文件成功")
        except Exception as e:
            self.logger.error(f"创建默认技能文件失败: {e}")
    
    def save_plugins(self) -> bool:
        """
        保存插件数据到JSON文件
        
        Returns:
            bool: 保存成功返回True，失败返回False
        """
        try:
            # 确保目录存在
            skill_dir = os.path.dirname(self.skill_file_path)
            if skill_dir and not os.path.exists(skill_dir):
                os.makedirs(skill_dir)
            
            # 保存插件数据
            with open(self.skill_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.plugins, f, ensure_ascii=False, indent=4)
            
            self.logger.info("插件数据保存成功")
            return True
            
        except Exception as e:
            self.logger.error(f"保存插件数据失败: {e}")
            return False
    
    def add_plugin(self, plugin_name: str, plugin_data: Dict[str, Any]) -> bool:
        """
        添加新插件
        
        Args:
            plugin_name (str): 插件名称
            plugin_data (dict): 插件数据
            
        Returns:
            bool: 添加成功返回True，失败返回False
        """
        try:
            # 验证插件名称
            if not plugin_name or not plugin_name.strip():
                raise ValueError("插件名称不能为空")
            
            # 检查插件是否已存在
            if plugin_name in self.plugins:
                raise ValueError(f"插件 '{plugin_name}' 已存在")
            
            # 验证必需字段
            required_fields = ['discription', 'format', 'usage', 'attention']
            for field in required_fields:
                if field not in plugin_data:
                    raise ValueError(f"缺少必需字段: {field}")
            
            # 设置默认值
            plugin_data.setdefault('AI_can_use', True)
            plugin_data.setdefault('detailed_info', False)
            
            # 添加插件
            self.plugins[plugin_name] = plugin_data
            
            # 保存到文件
            if self.save_plugins():
                self.logger.info(f"成功添加插件: {plugin_name}")
                return True
            else:
                # 保存失败时回滚
                del self.plugins[plugin_name]
                return False
                
        except Exception as e:
            self.logger.error(f"添加插件失败: {e}")
            return False
    
    def update_plugin(self, plugin_name: str, plugin_data: Dict[str, Any]) -> bool:
        """
        更新插件信息
        
        Args:
            plugin_name (str): 插件名称
            plugin_data (dict): 插件数据
            
        Returns:
            bool: 更新成功返回True，失败返回False
        """
        try:
            # 检查插件是否存在
            if plugin_name not in self.plugins:
                raise ValueError(f"插件 '{plugin_name}' 不存在")
            
            # 验证必需字段
            required_fields = ['discription', 'format', 'usage', 'attention']
            for field in required_fields:
                if field not in plugin_data:
                    raise ValueError(f"缺少必需字段: {field}")
            
            # 设置默认值
            plugin_data.setdefault('AI_can_use', True)
            plugin_data.setdefault('detailed_info', False)
            
            # 更新插件
            self.plugins[plugin_name] = plugin_data
            
            # 保存到文件
            if self.save_plugins():
                self.logger.info(f"成功更新插件: {plugin_name}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"更新插件失败: {e}")
            return False
    
    def delete_plugin(self, plugin_name: str) -> bool:
        """
        删除插件
        
        Args:
            plugin_name (str): 插件名称
            
        Returns:
            bool: 删除成功返回True，失败返回False
        """
        try:
            # 检查插件是否存在
            if plugin_name not in self.plugins:
                raise ValueError(f"插件 '{plugin_name}' 不存在")
            
            # 删除插件
            del self.plugins[plugin_name]
            
            # 保存到文件
            if self.save_plugins():
                self.logger.info(f"成功删除插件: {plugin_name}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"删除插件失败: {e}")
            return False
    
    def get_plugins(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有插件
        
        Returns:
            dict: 所有插件数据
        """
        return self.plugins.copy()
    
    def get_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """
        获取指定插件
        
        Args:
            plugin_name (str): 插件名称
            
        Returns:
            dict: 插件数据，如果不存在返回None
        """
        return self.plugins.get(plugin_name, None)
    
    def plugin_exists(self, plugin_name: str) -> bool:
        """
        检查插件是否存在
        
        Args:
            plugin_name (str): 插件名称
            
        Returns:
            bool: 存在返回True，不存在返回False
        """
        return plugin_name in self.plugins
    
    def get_plugin_count(self) -> int:
        """
        获取插件数量
        
        Returns:
            int: 插件总数
        """
        return len(self.plugins)
    
    def validate_plugin_data(self, plugin_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        验证插件数据格式
        
        Args:
            plugin_data (dict): 插件数据
            
        Returns:
            tuple: (是否有效, 错误信息)
        """
        try:
            # 检查必需字段
            required_fields = ['discription', 'format', 'usage', 'attention']
            for field in required_fields:
                if field not in plugin_data:
                    return False, f"缺少必需字段: {field}"
                if not isinstance(plugin_data[field], str):
                    return False, f"字段 {field} 必须是字符串类型"
            
            # 检查布尔字段
            if 'AI_can_use' in plugin_data and not isinstance(plugin_data['AI_can_use'], bool):
                return False, "AI_can_use 必须是布尔类型"
            
            if 'detailed_info' in plugin_data and not isinstance(plugin_data['detailed_info'], bool):
                return False, "detailed_info 必须是布尔类型"
            
            return True, ""
            
        except Exception as e:
            return False, f"数据验证异常: {e}"

# 使用示例和测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 测试插件管理器
    pm = PluginManager()
    
    print("=== 插件管理器测试 ===")
    print(f"当前插件数量: {pm.get_plugin_count()}")
    print(f"所有插件: {list(pm.get_plugins().keys())}")
    
    # 测试添加插件
    new_plugin = {
        "discription": "测试新插件",
        "format": "[TEST:new_plugin]",
        "usage": "这是一个测试插件",
        "attention": "仅用于测试",
        "AI_can_use": True,
        "detailed_info": False
    }
    
    if pm.add_plugin("new_test_plugin", new_plugin):
        print("添加插件成功")
    else:
        print("添加插件失败")
    
    print(f"更新后插件数量: {pm.get_plugin_count()}")