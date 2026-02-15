# import sys
from PyQt6.QtCore import QTimer
from datetime import datetime, timedelta
import lib.LogManager as LogManager
import logging

class EatingTimer:
    """管理宠物进食倒计时的类"""
    def __init__(self, parent_window):

        LogManager.init_logging()
        self.logger = logging.getLogger(__name__)

        self.parent_window = parent_window
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.start_time = None  # 开始进食的时间戳
        self.end_time = None    # 预计结束进食的时间戳
        self.total_time = 0     # 总共需要的时间（秒）
        
        # 保存食物信息，用于在进食过程中逐渐更新
        self.current_food_calories = 0
        self.current_food_water = 0
        # 记录已添加的数值，避免重复添加
        self.added_calories = 0
        self.added_water = 0

    def start_feeding(self, food_time_seconds, food_calories=0, food_water=0):
        """开始进食倒计时"""
        if food_time_seconds <= 0:
            return

        self.total_time = food_time_seconds
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(seconds=food_time_seconds)
        
        # 保存食物信息
        self.current_food_calories = food_calories
        self.current_food_water = food_water
        self.added_calories = 0
        self.added_water = 0
        
        # 启动计时器，每秒更新一次
        self.timer.start(1000)

        # 显示进食消息
        self.parent_window.add_system_message_to_chat(f"开始进食，预计需要 {format_time(food_time_seconds)} 时间")
        # 更新状态窗口显示
        self.update_status_window()

    def tick(self):
        """倒计时滴答"""
        remaining_time = self.calculate_remaining_time()
        if remaining_time > 0:
            # 计算已经过去的时间
            elapsed_time = self.total_time - remaining_time
            # 根据已过去的时间按比例计算应该增加的数值
            completion_ratio = elapsed_time / self.total_time
            
            # 计算总共应该添加的数值（使用浮点数以支持小数）
            target_calories = self.current_food_calories * completion_ratio
            target_water = self.current_food_water * completion_ratio
            
            # 计算本次需要添加的数值
            calorie_increment = target_calories - self.added_calories
            water_increment = target_water - self.added_water
            
            # 更新宠物状态
            if abs(calorie_increment) > 0.001 or abs(water_increment) > 0.001:  # 使用小的阈值避免浮点数精度问题
                # 使用PetStatsManager更新宠物状态
                self.parent_window.pet_stats_manager.update_pet_stats(calorie_increment, water_increment)
                self.added_calories = target_calories
                self.added_water = target_water
            
            # 更新状态窗口
            self.update_status_window()
            # 保存当前进度到配置文件
            self.save_progress()
        else:
            # 倒计时结束，停止计时器
            self.timer.stop()
            # 完成进食，更新宠物状态（处理可能的舍入误差）
            self.finish_feeding()

    def calculate_remaining_time(self):
        """计算剩余时间"""
        if self.end_time is None:
            return 0
        
        now = datetime.now()
        remaining_delta = self.end_time - now
        remaining_seconds = max(0, int(remaining_delta.total_seconds()))
        return remaining_seconds


    def finish_feeding(self):
        """完成进食，更新宠物状态"""
        # 停止计时器
        self.timer.stop()
        
        # 确保所有营养值都被添加（处理可能的舍入误差）
        remaining_calories = self.current_food_calories - self.added_calories
        remaining_water = self.current_food_water - self.added_water
        
        if abs(remaining_calories) > 0.001 or abs(remaining_water) > 0.001:
            # 使用PetStatsManager更新宠物状态
            self.parent_window.pet_stats_manager.update_pet_stats(remaining_calories, remaining_water)
        
        # 显示完成消息
        self.parent_window.add_system_message_to_chat("进食完成！宠物感到很满足。")
        
        # 隐藏倒计时显示
        self.update_status_window()
        
        # 重置时间
        self.start_time = None
        self.end_time = None
        self.total_time = 0
        self.current_food_calories = 0
        self.current_food_water = 0
        self.added_calories = 0
        self.added_water = 0
        
        # 更改宠物动画为闭眼状态
        try:
            import json
            from PyQt6.QtGui import QMovie
            
            with open("demo_setting.json", "r", encoding="utf-8") as f:
                setting = json.load(f)
            
            # 更新设置中的GIF
            setting["gif"] = "闭眼.gif"
            
            # 保存回文件
            with open("demo_setting.json", "w", encoding="utf-8") as f:
                import json
                json.dump(setting, f, ensure_ascii=False, indent=4)
            
            # 更改宠物动画
            gif_folder = setting.get('gif_folder', '蜡笔小新组')
            self.parent_window.movie = QMovie(f"{gif_folder}/闭眼.gif")
            self.parent_window.label.setMovie(self.parent_window.movie)
            self.parent_window.movie.start()
        except Exception as e:
            self.logger.error(f"更改宠物动画失败: {e}")

    def update_status_window(self):
        """更新状态窗口的显示"""
        remaining_time = self.calculate_remaining_time()
        if self.parent_window.stat_window and self.parent_window.stat_window.isVisible():
            self.parent_window.stat_window.update_eating_timer(remaining_time)

    def save_progress(self):
        """保存当前进食进度到配置文件"""
        if self.end_time is not None:
            progress_data = {
                'start_time': self.start_time.isoformat(),
                'end_time': self.end_time.isoformat(),
                'total_time': self.total_time,
                'current_food_calories': self.current_food_calories,
                'current_food_water': self.current_food_water,
                'added_calories': self.added_calories,
                'added_water': self.added_water
            }
        else:
            progress_data = {}
        self.parent_window.save_eating_progress(progress_data)

    def load_progress(self, progress_data):
        """从配置文件加载进食进度"""
        if progress_data and 'end_time' in progress_data:
            try:
                self.start_time = datetime.fromisoformat(progress_data['start_time'])
                self.end_time = datetime.fromisoformat(progress_data['end_time'])
                self.total_time = progress_data.get('total_time', 0)
                self.current_food_calories = progress_data.get('current_food_calories', 0)
                self.current_food_water = progress_data.get('current_food_water', 0)
                self.added_calories = progress_data.get('added_calories', 0)
                self.added_water = progress_data.get('added_water', 0)
                
                remaining_time = self.calculate_remaining_time()
                if remaining_time > 0:
                    # 重新启动计时器
                    self.timer.start(1000)
                    # 更新状态窗口
                    self.update_status_window()
                else:
                    # 如果时间已过，则直接完成进食
                    self.finish_feeding()
            except ValueError:
                # 如果日期格式不正确，则忽略
                pass

    def is_feeding(self):
        """检查是否正在进食"""
        return self.calculate_remaining_time() > 0


def format_time(seconds):
    """格式化秒数为 HH:MM:SS 格式"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"