'''
读取食物图片里面信息

这是一个向后兼容的导入模块，实际功能已在food_manager模块中实现
'''



import json
from stegano import lsb
import os
#读取
print(os.listdir("./outfood/"))
for i in os.listdir("./outfood/"):
    print(f"图片名称: {i}")
    try:
        data = lsb.reveal(f"D:\code\python\DesktopPetByAiNew\DesktopPet\outfood\{i}")
        print(json.loads(data))
    except IndexError:
        print("没有信息")
    