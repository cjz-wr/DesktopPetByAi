import importlib.util
import sys
from pathlib import Path


class PluginManager:
    def __init__(self):
        pass

    def load_plugins(plugin_dir="plugins"):
        """加载所有插件，返回 {plugin_name: callable} 字典"""
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(__file__).parent

        plugin_path = base_dir / plugin_dir
        if not plugin_path.exists():
            print(f"插件目录 {plugin_path} 不存在")
            return {}

        plugins = {}
        for py_file in plugin_path.glob("*.py"):
            module_name = py_file.stem  # 插件名
            spec = importlib.util.spec_from_file_location(module_name, py_file)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            try:
                spec.loader.exec_module(module)
            except Exception as e:
                print(f"加载插件 {module_name} 失败: {e}")
                continue

            if hasattr(module, 'register'):
                try:
                    plugin_func = module.register()
                    plugins[module_name] = plugin_func
                except Exception as e:
                    print(f"执行插件 {module_name}.register() 失败: {e}")
            else:
                print(f"插件 {module_name} 缺少 register 函数，已忽略")
        return plugins

    def call_plugin(plugins_dict, plugin_name, *args, **kwargs):
        """调用指定的插件（如果存在）"""
        if plugin_name in plugins_dict:
            return plugins_dict[plugin_name](*args, **kwargs)
        else:
            print(f"插件 {plugin_name} 未找到")
            return None
        
def main():
    plugins = PluginManager.load_plugins()
    a = PluginManager.call_plugin(plugins, "GetTime")
    print(a)
    ll = [3,5,6]
    cc = {"a":1,"b":2,"c":3}
    PluginManager.call_plugin(plugins, "demo2", *ll)
    PluginManager.call_plugin(plugins, "demo2", **cc)
    # PluginManager.call_plugin(plugins, "demo", 1)

if __name__ == "__main__":
    main()