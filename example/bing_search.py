try:
    from lib.bing_mcp_client import BingMCPClient
except ImportError:
    import os,sys
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # 假设lib目录在项目根目录下,即获取上级目录
    sys.path.insert(0, project_root) # 添加项目路径到sys.path
    from lib.bing_mcp_client import BingMCPClient

# 创建客户端（自动初始化）
client = BingMCPClient()

# 搜索网络
result = client.search_web("人工智能最新发展", num_results=5)

# 获取结果摘要
print(result.text_summary)

# 获取完整结果
for item in result.content:
    if item.get("type") == "text":
        print(item.get("text"))