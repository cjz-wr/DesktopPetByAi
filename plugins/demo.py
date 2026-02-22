# plugins/hello_plugin.py
def say_hello():
    print("Hello from plugin!")

def register():
    # 返回一个可调用对象，这里直接返回函数本身
    return say_hello