"""
通用工具函数模块
包含目录创建、文件操作等常用功能
"""

import os
import logging

logger = logging.getLogger(__name__)

def ensure_ai_memory_directory():
    """
    确保 ai_memory 目录存在
    
    如果 ai_memory 目录不存在，则自动创建该目录。
    使用 os.makedirs 而不是 os.mkdir，确保可以递归创建多级目录。
    
    Returns:
        str: ai_memory 目录的路径
    """
    ai_memory_dir = "ai_memory"
    try:
        # 使用 exist_ok=True 避免重复创建时报错
        os.makedirs(ai_memory_dir, exist_ok=True)
        logger.info(f"已确保 {ai_memory_dir} 目录存在")
        return ai_memory_dir
    except Exception as e:
        logger.error(f"创建 {ai_memory_dir} 目录失败: {e}")
        raise

def get_memory_file_path(identity):
    """
    获取对话历史文件的完整路径
    
    Args:
        identity (str): 对话标识符
        
    Returns:
        str: 完整的文件路径
    """
    ai_memory_dir = ensure_ai_memory_directory()
    return os.path.join(ai_memory_dir, f"memory_{identity}.json")

# 兼容性函数，保持原有接口
def create_ai_memory_dir():
    """
    兼容旧版本的目录创建函数
    """
    return ensure_ai_memory_directory()