# plugins/hello_plugin.py
def say_hello(a=1,b=2,c=3):
    print(f"Hello from plugin with a={a}, b={b}, c={c}!")

def register():
    return say_hello