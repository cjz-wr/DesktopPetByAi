import winreg
import os

def find_software_in_registry(software_name):
    """
    在注册表中搜索指定软件名的安装路径。
    返回第一个匹配的路径，若未找到返回 None。
    """
    # 常见的注册表路径
    registry_paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",  # 32位软件在64位系统
    ]
    
    for root_path in registry_paths:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, root_path) as key:
                index = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, index)
                        subkey_path = f"{root_path}\\{subkey_name}"
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey_path) as subkey:
                            # 尝试获取显示名称
                            try:
                                display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                if software_name.lower() in display_name.lower():
                                    # 获取安装路径
                                    try:
                                        install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                                        return install_location
                                    except FileNotFoundError:
                                        # 如果没有InstallLocation，尝试DisplayIcon（图标路径）或直接返回子键名
                                        try:
                                            display_icon = winreg.QueryValueEx(subkey, "DisplayIcon")[0]
                                            return os.path.dirname(display_icon)
                                        except:
                                            pass
                            except FileNotFoundError:
                                pass
                        index += 1
                    except WindowsError:
                        break
        except FileNotFoundError:
            continue
    return None

# 示例：查找微信
wechat_path = find_software_in_registry("")
if wechat_path:
    print(f"pycharm安装路径: {wechat_path}")
else:
    print("未找到pycharm")