'''
用于给食物图片写入信息

这是一个向后兼容的导入模块，实际功能已在food_manager模块中实现
'''

from lib.food_manager import FoodVerification
from stegano import lsb
import json

# 保留旧的接口，以便现有代码继续工作
__all__ = ['FoodVerification']

while True:
    data = {
    "FoodName":"", #食物名称
    "FoodDescription":"", #食物描述
    "FoodCalories":"", #食物热量
    "FoodWater":"", #食物水分
    }
    path = input("请输入图片路径: ")
    name = input("请输入保存图片名称: ")
    for i in data.keys():
        data[i] = input(f"{i}: ")

    print(f"{data}")

    # 将数据写入图片
    lsb.hide(path, json.dumps(data)).save("./outfood/"+name+".png")
    print("写入成功，保存路径: "+"./outfood/"+name+".png")