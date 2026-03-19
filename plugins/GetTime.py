import datetime

def return_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#必要的注册函数
def register():
    return return_time