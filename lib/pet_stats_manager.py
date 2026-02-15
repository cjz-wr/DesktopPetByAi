"""宠物状态管理模块"""

import json
from datetime import datetime
from PyQt6.QtWidgets import QWidget
import os
import lib.LogManager as LogManager
import logging

class PetStatsManager:
    """管理宠物状态（饥饿度、水分）的类"""
    
    def __init__(self, parent_window):

        LogManager.init_logging()
        self.logger = logging.getLogger(__name__)


        self.parent_window = parent_window
        # 添加宠物状态变量
        self.pet_hunger = 50  # 饥饿度，0-100
        self.pet_water = 60   # 水分，0-100
        # 初始化上次更新时间
        self.last_update_time = datetime.now()
        
        # 从配置文件加载宠物状态
        self.load_pet_stats()

        # 从配置文件加载上次更新时间
        self.load_last_update_time()

        # 根据上次更新时间计算当前状态
        self.calculate_and_apply_depletion()

        # 确保状态值被保存到配置文件中（如果不存在的话）
        self.ensure_pet_stats_saved()

    def load_pet_stats(self):
        """从demo_setting.json加载宠物状态"""
        try:
            with open("demo_setting.json", "r", encoding="utf-8") as f:
                setting = json.load(f)
            # 将加载的值转换为浮点数以支持小数
            self.pet_hunger = float(setting.get("hunger", 50.0))  # 默认值为50.0
            self.pet_water = float(setting.get("water", 60.0))    # 默认值为60.0
        except FileNotFoundError:
            # 如果文件不存在，使用默认值
            self.pet_hunger = 50.0
            self.pet_water = 60.0
        except json.JSONDecodeError:
            # 如果JSON格式错误，使用默认值
            self.pet_hunger = 50.0
            self.pet_water = 60.0
        except ValueError:
            # 如果值无法转换为浮点数，使用默认值
            self.pet_hunger = 50.0
            self.pet_water = 60.0

    def save_pet_stats(self):
        """保存宠物状态到demo_setting.json"""
        try:
            with open("demo_setting.json", "r", encoding="utf-8") as f:
                setting = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # 如果文件不存在或格式错误，初始化一个空字典
            setting = {}
        
        # 更新状态值，保留一位小数以避免浮点数精度问题
        setting["hunger"] = round(float(self.pet_hunger), 1)
        setting["water"] = round(float(self.pet_water), 1)

        # 写回文件
        with open("demo_setting.json", "w", encoding="utf-8") as f:
            json.dump(setting, f, ensure_ascii=False, indent=4)
            
    def calculate_and_apply_depletion(self):
        """根据上次更新时间计算饥饿度和水分的减少"""
        try:
            with open("demo_setting.json", "r", encoding="utf-8") as f:
                setting = json.load(f)
            last_update_str = setting.get("last_update_time", "")
            
            if last_update_str:
                last_update = datetime.fromisoformat(last_update_str)
                now = datetime.now()
                
                # 计算时间差（单位：小时）
                time_diff_hours = (now - last_update).total_seconds() / 3600
                
                # 计算应该减少的饥饿度和水分（使用浮点数）
                hunger_decrease = time_diff_hours * 5  # 每小时减少5点饥饿度
                water_decrease = time_diff_hours * 3   # 每小时减少3点水分
                
                # 应用减少（保持为浮点数）
                self.pet_hunger = max(0.0, self.pet_hunger - hunger_decrease)
                self.pet_water = max(0.0, self.pet_water - water_decrease)
                
                # 保存更新后的状态
                self.save_pet_stats()
                
        except Exception as e:
            self.logger.error(f"计算状态减少时出错: {e}")
            

    def save_last_update_time(self):
        """保存最后更新时间到配置文件"""
        try:
            with open("demo_setting.json", "r", encoding="utf-8") as f:
                setting = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            setting = {}
        
        setting["last_update_time"] = datetime.now().isoformat()
        
        with open("demo_setting.json", "w", encoding="utf-8") as f:
            json.dump(setting, f, ensure_ascii=False, indent=4)

    def load_last_update_time(self):
        """从配置文件加载最后更新时间"""
        try:
            with open("demo_setting.json", "r", encoding="utf-8") as f:
                setting = json.load(f)
            last_update_str = setting.get("last_update_time", "")
            if last_update_str:
                self.last_update_time = datetime.fromisoformat(last_update_str)
            else:
                # 如果没有保存过最后更新时间，则使用当前时间
                self.last_update_time = datetime.now()
                self.save_last_update_time()
        except Exception:
            # 如果解析时间出错，使用当前时间
            self.last_update_time = datetime.now()
            self.save_last_update_time()

    def update_pet_stats(self, hunger_change, water_change):
        """更新宠物状态并保存"""
        # 更新状态值，确保在0-100范围内
        # 使用浮点数进行计算，然后在显示时进行四舍五入
        self.pet_hunger = max(0.0, min(100.0, float(self.pet_hunger) + float(hunger_change)))
        self.pet_water = max(0.0, min(100.0, float(self.pet_water) + float(water_change)))
        
        # 保存到配置文件 - 保存时使用整数，以避免配置文件中存储过多小数位
        self.save_pet_stats()
        
        # 保存最新的更新时间
        self.save_last_update_time()
        
        # 如果状态窗口已显示，更新显示（显示时四舍五入到整数）
        if (hasattr(self.parent_window, 'stat_window') and 
            self.parent_window.stat_window and 
            self.parent_window.stat_window.isVisible()):
            rounded_hunger = round(self.pet_hunger)
            rounded_water = round(self.pet_water)
            self.parent_window.stat_window.update_values(rounded_hunger, rounded_water)
    
    def ensure_pet_stats_saved(self):
        """确保宠物状态已保存到配置文件中（如果不存在的话）"""
        try:
            with open("demo_setting.json", "r", encoding="utf-8") as f:
                setting = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # 如果文件不存在或格式错误，初始化一个空字典
            setting = {}
        
        # 检查配置中是否已有这些值，如果没有则保存默认值（使用浮点数）
        if "hunger" not in setting or "water" not in setting:
            setting["hunger"] = round(float(self.pet_hunger), 1)
            setting["water"] = round(float(self.pet_water), 1)
            
            # 写回文件
            with open("demo_setting.json", "w", encoding="utf-8") as f:
                json.dump(setting, f, ensure_ascii=False, indent=4)