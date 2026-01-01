import pyi_splash,time

def show_progress(steps, total):
    """显示进度"""
    percentage = int((steps / total) * 100)
    pyi_splash.update_text(f"正在初始化... {percentage}%")

# 使用示例
tasks = [
    ("加载配置", 0.2),
    ("连接数据库", 0.3),
    ("初始化界面", 0.5)
]

progress = 0
for task_name, task_time in tasks:
    pyi_splash.update_text(f"{task_name}...")
    time.sleep(task_time)  # 模拟任务执行
    progress += task_time * 100
    pyi_splash.update_text(f"{task_name}完成 ({int(progress)}%)")