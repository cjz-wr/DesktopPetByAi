import os

folder_path = "gif/蜡笔小新组"

try:
    with os.scandir(folder_path) as entries:
        for entry in entries:
            if entry.is_file():  # 只处理文件
                print(f"文件: {entry.name}")
                # 读取文件内容示例
                # with open(entry.path, 'r', encoding='utf-8') as f: # entry.path 是完整路径
                #     content = f.read()
                #     print(content)
except FileNotFoundError:
    print(f"文件夹 '{folder_path}' 不存在。")
except PermissionError:
    print(f"没有权限访问文件夹 '{folder_path}'。")