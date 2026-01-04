try:
    from lib.MCP12306 import query_12306_tickets as query_12306_tickets
except ImportError:
    import os, sys
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # 假设lib目录在项目根目录下,即获取上级目录
    sys.path.insert(0, project_root)
    from lib.MCP12306 import query_12306_tickets as query_12306_tickets
result = query_12306_tickets("北京", "上海", "2026-01-06")
if "error" in result:
    print(result["error"])
else:
    if "result" in result:
            contents = result["result"].get("content", [])
            for item in contents:
                if item.get("type") == "text":
                    ticket_text = item.get("text", "")
                    print(f"\n📄 ===========车票信息=========")
                    print(ticket_text)
            print("\n" + "=" * 50)