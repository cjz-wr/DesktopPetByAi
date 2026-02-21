import random,time,asyncio
from lib.temp_message_box import show_temp_message
import logging
import lib.LogManager as LogManager
from PyQt6.QtCore import QTimer, QObject
import json

class  PetReminder(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.remind_list = [
            ""
        ]
        LogManager.init_logging()
        self.logger = logging.getLogger(__name__)
        
        self._remindTalk()
        self._remindEat()
        
    def _show_random_message(self, message_list):
        """显示随机提醒消息"""
        if self.parent():
            message = random.choice(message_list)
            self.logger.info(f"[提醒] {message}")
            show_temp_message(self.parent(), message, duration=2000, fade_duration=1000)


    def _show_eat_message(self, message_list):
        if self.parent():
            try:
                with open("demo_setting.json", "r", encoding="utf-8") as f:
                    eat = json.load(f)
                    eat_y = eat.get("hunger",10)
                    if eat_y < 50:
                        message = random.choice(message_list)
                        self.logger.info(f"[吃饭提醒] {message}")
                        show_temp_message(self.parent(), message, duration=2000, fade_duration=1000)
            except Exception as e:
                self.logger.warning(f"加载吃饭提醒配置失败: {e}")
    
    def start_talk_reminder(self, parent, remind_time=30):
        """启动说话提醒 - 使用Qt定时器"""
        if not self.talk_timer.isActive():
            self.setParent(parent)  # 设置父对象
            self.talk_timer.start(remind_time * 1000)  # 转换为毫秒
            self.logger.info(f"说话提醒已启动，间隔{remind_time}秒")
        else:
            self.logger.info("说话提醒已在运行中")


    def start_eat_reminder(self, parent, remind_time=60):
        """启动吃饭提醒 - 使用Qt定时器"""        
        if not self.eat_timer.isActive():
            self.setParent(parent)  # 设置父对象
            self.eat_timer.start(remind_time * 1000)  # 转换为毫秒
            self.logger.info(f"吃饭提醒已启动，间隔{remind_time}秒")
        else:
            self.logger.info("吃饭提醒已在运行中")
    
    def stop_talk_reminder(self):
        """停止说话提醒"""
        if self.talk_timer.isActive():
            self.talk_timer.stop()
            self.logger.info("说话提醒已停止")


    def stop_eat_reminder(self):
        """停止吃饭提醒"""
        if self.eat_timer.isActive():
            self.eat_timer.stop()
            self.logger.info("吃饭提醒已停止")
    

    def _remindTalk(self):
        talk_list = [
            "我好无聊啊",
            "陪我说说话吧",
            "找我聊聊天呗"
        ]
        # 创建Qt定时器
        self.talk_timer = QTimer(self)
        self.talk_timer.timeout.connect(lambda: self._show_random_message(talk_list))

    def _remindEat(self):
        self.eat_list = [
            "我要吃饭了",
            "吃饭了",
            "我好饿啊",
            "我的の饭饭呢"
        ]
        self.eat_timer = QTimer(self)
        self.eat_timer.timeout.connect(lambda: self._show_eat_message(self.eat_list))
        

        

    async def remindRest(self):
        pass