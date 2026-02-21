import asyncio
from email import message
import sys,os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QSystemTrayIcon, QMenu, 
    QDialog, QVBoxLayout, QTextEdit,  QPushButton, 
    QHBoxLayout, QMessageBox, QSplitter, QFrame
)
from PyQt6.QtGui import QIcon, QPixmap, QAction, QMovie, QTextCursor, QColor, QTextCharFormat, QFont, QImage, QPainter, QFontMetrics, QPainterPath
from PyQt6.QtCore import Qt, QPoint, QThread, pyqtSignal, QTimer
# from PyQt6.QtWidgets import QGraphicsDropShadowEffect
import json
from datetime import datetime

import AiAPI
# 移除了对zhipu的直接导入
import openai_api
from settingwindow import CustomDialog,FontManager
import logging
from lib.food_manager import RecipeButton, RecipePopup, FoodVerification, feed_pet_with_food
from lib.pet_status_bar import StatBarWindow
from lib.feeding_timer import EatingTimer, format_time
from lib.pet_stats_manager import PetStatsManager  # 导入新的宠物状态管理模块
import lib.LogManager as LogManager
import logging


from lib.pet_reminder import PetReminder

# from stegano import lsb

# def format_time(seconds):
#     """格式化秒数为 HH:MM:SS 格式"""
#     hours = seconds // 3600
#     minutes = (seconds % 3600) // 60
#     secs = seconds % 60
#     return f"{hours:02d}:{minutes:02d}:{secs:02d}"


class AIWorker(QThread):
    finished = pyqtSignal(str)  # 发送 AI 回复
    error = pyqtSignal(str)     # 发送错误信息

    def __init__(self, messages, parent=None):
        super().__init__(parent)
        self.messages = messages

    def run(self):
        try:
            # 使用异步方式获取AI回复，现在统一使用OpenAI兼容接口
            ai_api = AiAPI.AiAPI()
            reply = asyncio.run(ai_api.get_ai_reply(self.messages))
            self.finished.emit(reply)
        except Exception as e:
            self.error.emit(str(e))


class ChatDialog(QDialog):
    def __init__(self, parent=None):
        LogManager.init_logging()
        self.logger = logging.getLogger(__name__)
        super().__init__(parent)
        self.setWindowTitle("ICAT")
        self.resize(600, 500)  # 增加窗口大小以适应聊天界面
        self.parent_window = parent

        # 设置窗口样式
        self.setStyleSheet("""
            QDialog {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                                 stop: 0 #e8f4fd, stop: 1 #ffffff);
                border-radius: 10px;
            }
        """)

        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 创建分割器来管理聊天区域和输入区域
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 聊天历史区域
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                color: #000000;
                background-color: #ffffff;
                border: 2px solid #4CAF50;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
                selection-background-color: #a3d8a5;
            }
        """)
        
        # 输入区域
        input_frame = QFrame()
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(0, 0, 0, 0)
        
        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText("输入消息...")
        self.input_edit.setMaximumHeight(100)
        self.input_edit.setStyleSheet("""
            QTextEdit {
                color: #000000;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                padding: 8px;
                font-size: 14px;
                background-color: #ffffff;
            }
        """)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.send_button = QPushButton("发送")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                                 stop: 0 #4CAF50, stop: 1 #2E7D32);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                                 stop: 0 #45a049, stop: 1 #1B5E20);
            }
            QPushButton:pressed {
                background-color: #2E7D32;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.send_button.setFixedWidth(100)
        
        self.clear_button = QPushButton("清空")
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                                 stop: 0 #f44336, stop: 1 #d32f2f);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                                 stop: 0 #e57373, stop: 1 #b71c1c);
            }
            QPushButton:pressed {
                background-color: #d32f2f;
            }
        """)
        self.clear_button.setFixedWidth(100)
        
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        button_layout.addWidget(self.send_button)
        
        input_layout.addWidget(self.input_edit)
        input_layout.addLayout(button_layout)
        
        # 添加到分割器
        splitter.addWidget(self.chat_history)
        splitter.addWidget(input_frame)
        splitter.setSizes([400, 100])  # 设置初始大小比例
        
        main_layout.addWidget(splitter)
        
        # 连接信号
        self.send_button.clicked.connect(self.handle_send)
        self.clear_button.clicked.connect(self.clear_chat)
        
        # 加载历史对话
        # self.load_conversation()


        #检测相关配置文件是否存在
        if not os.path.exists("demo_setting.json"):
            with open("demo_setting.json", "w", encoding="utf-8") as f:
                f.write('{"gif": "啦啦啦.gif"}')
            self.logger.info("已创建demo_setting.json文件")
        #检测ai_memory文件夹是否存在
        if not os.path.exists("ai_memory"):
            os.mkdir("ai_memory")
            self.logger.info("已创建ai_memory文件夹")
    
    def load_conversation(self):
        """加载历史对话并显示在聊天区域"""
        # 使用AiAPI加载对话历史
        ai_api = AiAPI.AiAPI()
        messages = ai_api.load_conversation("default")
        for msg in messages:
            if msg['role'] == 'user':
                self.add_message("你", msg['content'], is_user=True)
            elif msg['role'] == 'assistant':
                self.add_message("ICAT", msg['content'], is_user=False)
    
    def add_message(self, sender, message, is_user=True):
        """添加消息到聊天区域"""
        # 设置消息样式
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # 添加发送者标签
        sender_format = QTextCharFormat()
        font = QFont()
        font.setPointSize(10)  # 设置有效的字体大小
        sender_format.setFont(font)
        sender_format.setFontWeight(QFont.Weight.Bold)
        
        # 根据消息类型设置不同颜色
        if is_user:
            sender_format.setForeground(QColor("#2E7D32"))  # 用户消息绿色
        elif sender == "系统":
            sender_format.setForeground(QColor("#FF6B35"))  # 系统消息橙色
        else:
            sender_format.setForeground(QColor("#D32F2F"))  # AI消息红色
            
        cursor.insertText(f"{sender}: ", sender_format)
        
        # 添加消息内容
        message_format = QTextCharFormat()
        font = QFont()
        font.setPointSize(10)  # 设置有效的字体大小
        message_format.setFont(font)
        cursor.insertText(f"{message}\n\n", message_format)
        
        # 滚动到底部
        self.chat_history.verticalScrollBar().setValue(
            self.chat_history.verticalScrollBar().maximum()
        )

    def add_system_message(self, message):
        """添加系统消息到聊天区域（便捷方法）"""
        self.add_message("系统:", message, is_user=False)
    
    def handle_send(self):
        input_text = self.input_edit.toPlainText().strip()
        if not input_text:
            QMessageBox.warning(self, "输入错误", "输入内容不能为空！")
            return
        
        # 添加用户消息到聊天区域
        self.add_message("你", input_text, is_user=True)
        
        # 构建消息
        ai_api = AiAPI.AiAPI()
        messages = ai_api.load_conversation("default")
        messages.append({"role": "user", "content": input_text})
        ai_api.save_conversation("default", messages)
        
        # 禁用发送按钮，防止重复发送
        self.send_button.setEnabled(False)
        self.input_edit.setEnabled(False)
        
        # 显示加载提示
        self.add_message("系统", "ICAT 正在思考...", is_user=False)
        
        # 创建并启动工作线程
        self.worker = AIWorker(messages)
        self.worker.finished.connect(self.on_ai_reply_received)
        self.worker.error.connect(self.on_ai_error)
        self.worker.start()
        
        # 清空输入框
        self.input_edit.clear()
    
    def on_ai_reply_received(self, reply):
        # 移除"AI正在思考"提示
        self.chat_history.undo()
        self.chat_history.undo()
        self.chat_history.undo()
        self.chat_history.undo()
        
        # 添加AI回复
        self.add_message("ICAT", reply, is_user=False)
        
        # 保存对话
        ai_api = AiAPI.AiAPI()
        messages = ai_api.load_conversation("default")
        messages.append({"role": "assistant", "content": reply})
        ai_api.save_conversation("default", messages)

        # 重新启用发送按钮
        self.send_button.setEnabled(True)
        self.input_edit.setEnabled(True)
        self.input_edit.setFocus()

        # 通知主窗口刷新GIF动画
        if self.parent_window and hasattr(self.parent_window, "refresh_gif"):
            self.parent_window.refresh_gif()
    
    def on_ai_error(self, error_msg):
        # 移除"AI正在思考"提示
        self.chat_history.undo()
        self.chat_history.undo()
        
        # 显示错误信息
        self.add_message("系统", f"发生错误：{error_msg}", is_user=False)
        
        # 重新启用发送按钮
        self.send_button.setEnabled(True)
        self.input_edit.setEnabled(True)
        self.input_edit.setFocus()
    
    def clear_chat(self):
        """清空当前聊天界面（不删除历史记录）"""
        self.chat_history.clear()
        # self.load_conversation()  # 重新加载历史记录
    
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.handle_send()
                event.accept()
                return
        super().keyPressEvent(event)


class DesktopPet(QMainWindow):
    def __init__(self):
        super().__init__()

        #初始化日志
        LogManager.init_logging() # 初始化日志
        self.logger = logging.getLogger(__name__)



        


        self.init_ui()
        # 修改窗口标志，添加Tool类型以避免出现在任务栏
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool  # 添加Tool标志，避免出现在任务栏
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.dragging = False
        self.offset = QPoint()
        self.chat_dialog = None

        # 初始化透明度值，防止update_gif_transparency方法出错
        self.transparency_value = 1.0  # 默认不透明
        
        # 初始化状态窗口引用
        self.stat_window = None

        # 初始化食谱按钮引用
        self.recipe_button = None

        # 初始化设置对话框引用
        self.setting_dialog = None

        # 初始化宠物状态管理器
        self.pet_stats_manager = PetStatsManager(self)
        # 初始化进食计时器
        self.eating_timer = EatingTimer(self)

        # 从配置文件加载上次更新时间 - 应该由pet_stats_manager处理
        # self.load_last_update_time()  # 这个方法不存在，应该删除或调用正确的对象

        # 根据上次更新时间计算当前状态的损耗
        self.pet_stats_manager.calculate_and_apply_depletion()

        # 从配置文件加载进食进度
        self.load_eating_progress()

        # 确保状态值被保存到配置文件中（如果不存在的话）
        self.pet_stats_manager.ensure_pet_stats_saved()

        # 创建一个定时器，每分钟减少一次宠物状态
        self.depletion_timer = QTimer(self)
        self.depletion_timer.timeout.connect(self.reduce_pet_stats)
        self.depletion_timer.start(60000)  # 每60秒（1分钟）触发一次

        # 初始化系统托盘图标
        self.init_tray_icon()

        # 初始化宠物提醒系统
        self.pet_reminder = PetReminder()
        # 不要在这里直接调用异步函数，而是在适当的时机启动
        # self.pet_reminder.remindtalk(self)  # 错误的做法
        
        # 以下方法已移至 lib.pet_stats_manager.PetStatsManager

    def reduce_pet_stats(self):
        """定期减少宠物的饥饿度和水分"""
        # 由于计算减少已经在pet_stats_manager中实现，这里只需要调用即可
        # 但我们需要调整算法，使其适用于定期减少
        try:
            # 计算从上次更新到现在的时间差（单位：小时）
            now = datetime.now()
            time_diff_hours = (now - self.pet_stats_manager.last_update_time).total_seconds() / 3600
            
            # 如果时间差超过一个很小的阈值（比如1分钟），才更新状态
            if time_diff_hours >= 1/60:  # 至少1分钟才更新一次
                # 计算应该减少的饥饿度和水分
                hunger_decrease = time_diff_hours * 5  # 每小时减少5点饥饿度
                water_decrease = time_diff_hours * 3   # 每小时减少3点水分
                
                # 更新宠物状态
                self.pet_stats_manager.pet_hunger = max(0.0, self.pet_stats_manager.pet_hunger - hunger_decrease)
                self.pet_stats_manager.pet_water = max(0.0, self.pet_stats_manager.pet_water - water_decrease)
                
                # 保存更新后的状态和时间
                self.pet_stats_manager.save_pet_stats()
                self.pet_stats_manager.save_last_update_time()
                self.pet_stats_manager.last_update_time = now
                
                # 如果状态窗口已显示，更新显示
                if (hasattr(self, 'stat_window') and 
                    self.stat_window and 
                    self.stat_window.isVisible()):
                    rounded_hunger = round(self.pet_stats_manager.pet_hunger)
                    rounded_water = round(self.pet_stats_manager.pet_water)
                    self.stat_window.update_values(rounded_hunger, rounded_water)
        except Exception as e:
            self.logger.error(f"定期减少宠物状态时出错: {e}")

    def init_ui(self):
        # 创建一个标签用于显示动画
        self.label = QLabel(self)
        self.label.setStyleSheet("background-color: transparent;")  # 设置标签背景透明
        self.label.setScaledContents(True)  # 设置标签内容自适应大小
        self.label.setAcceptDrops(True)  # 标签也需要接受拖放
        self.setCentralWidget(self.label)   # 设置为主窗口的中央组件
        
        # 设置标签的固定大小以控制GIF显示尺寸
        self.label.setFixedSize(80, 80)  # 可以根据需要调整尺寸

        # 加载GIF动画
        self.load_gif_from_setting()

        #更新prompt,如果修改过的话
        # messages = zhipu.load_conversation("default")
        # zhipu.save_conversation("default", messages)
        # messages = openai_api.load_conversation("default")
        # openai_api.save_conversation("default", messages)
        aiAPI = AiAPI.AiAPI()
        message = aiAPI.load_conversation("default")
        aiAPI.save_conversation("default", message)


    #获取gif里面指定文件夹的gif图片,并修改ai的提示词
    def changMemeoryGif(self,gif_dir):
        try:
            with open("memory_default.json","w+",encoding="utf-8") as f:
                get = f.read()
                import json
                get = json.loads(get)
                listdir = os.listdir(gif_dir) #获取指定文件夹下的所有文件
                get[0]["content"] = f''


        except Exception as e:
            # logging.error(f"写入memory_default.json失败: {e}")
            self.logger.error(f"写入memory_default.json失败: {e}")

    #读取demo_setting.json,获取gif文件路径
    def load_gif_from_setting(self):
        import json
        try:
            with open("demo_setting.json", "r", encoding="utf-8") as f:
                setting = json.load(f)
            gif_name = setting.get("gif", "闭眼.gif") # 获取GIF文件名，默认"闭眼.gif"
            gif_name = gif_name.strip()  # 去除可能的空白字符
            
            # 使用配置中的GIF文件夹路径，如果未配置则使用默认值
            gif_folder = setting.get("gif_folder", "gif/猫")
            
            gif_path = gif_name
            # 如果不是绝对路径，则加上配置中的目录
            if not (gif_path.startswith("/") or ":" in gif_path):
                gif_path = f"{gif_folder}/{gif_name}"
        except Exception as e:
            self.logger.error(f"读取demo_setting.json失败: {e}")
            gif_path = "gif/猫/闭眼.gif"
        
        # 检查GIF文件是否存在
        if not os.path.exists(gif_path):
            self.logger.warning(f"GIF文件不存在: {gif_path}，使用默认GIF")
            gif_path = "gif/猫/闭眼.gif"
        
        try:
            self.movie = QMovie(gif_path)
            if self.movie.isValid():  # 检查movie是否有效
                self.movie.frameChanged.connect(self.update_gif_transparency)
                self.label.setMovie(self.movie)
                self.movie.start()
            else:
                self.logger.warning(f"无法加载GIF文件: {gif_path}")
                # 尝试使用默认路径
                default_gif_path = "gif/猫/闭眼.gif"
                if os.path.exists(default_gif_path):
                    self.movie = QMovie(default_gif_path)
                    if self.movie.isValid():
                        self.movie.frameChanged.connect(self.update_gif_transparency)
                        self.label.setMovie(self.movie)
                        self.movie.start()
                    else:
                        self.logger.warning("默认GIF也无法加载")
                else:
                    self.logger.warning("默认GIF文件不存在")
        except Exception as e:
            self.logger.error(f"加载GIF动画失败: {e}")

    # 刷新GIF动画
    def refresh_gif(self):
        self.load_gif_from_setting()

    def update_gif_transparency(self):
        """更新GIF动画的透明度"""
        current_frame = self.movie.currentPixmap()
        if not current_frame.isNull():
            # 创建透明图像
            transparent_image = QImage(current_frame.size(), QImage.Format.Format_ARGB32)
            transparent_image.fill(Qt.GlobalColor.transparent)

            painter = QPainter(transparent_image)
            # 使用getattr确保即使transparency_value未初始化也能正常工作
            transparency = getattr(self, 'transparency_value', 1.0)
            painter.setOpacity(transparency)
            painter.drawPixmap(0, 0, current_frame)
            painter.end()

            # 更新标签显示
            self.label.setPixmap(QPixmap.fromImage(transparent_image))

    def set_transparency(self, value):
        """设置透明度值"""
        self.transparency_value = value
        # 更新当前帧的透明度
        self.update_gif_transparency()
        # 设置窗口透明度
        self.setWindowOpacity(value)
    
    
    def grab_pet(self):
        with open("demo_setting.json", "r", encoding="utf-8") as f:
            setting = json.load(f)
            dir_name = setting.get("gif_folder", "gif/猫")
        if "站起.gif" in os.listdir(f"{dir_name}"):
            self.movie = QMovie(f"{dir_name}/站起.gif")
            self.label.setMovie(self.movie)
            self.movie.start()

    
    def eat_pet(self):
        with open("demo_setting.json", "r", encoding="utf-8") as f:
            setting = json.load(f)
            dir_name = setting.get("gif_folder", "gif/猫")
        if "吃东西.gif" in os.listdir(f"{dir_name}"):
            # 更新设置中的GIF值
            setting["gif"] = "吃东西.gif"
            # 将修改后的设置写回文件
            with open("demo_setting.json", "w", encoding="utf-8") as f:
                json.dump(setting, f, ensure_ascii=False, indent=4)

            self.movie = QMovie(f"{dir_name}/吃东西.gif")
            self.label.setMovie(self.movie)
            self.movie.start()

    
    def over_eat_pet(self):
        with open("demo_setting.json", "r", encoding="utf-8") as f:
            setting = json.load(f)
            dir_name = setting.get("gif_folder", "gif/猫")
        if "闭眼.gif" in os.listdir(f"{dir_name}"):
            # 更新设置中的GIF值
            setting["gif"] = "闭眼.gif"
            # 将修改后的设置写回文件
            with open("demo_setting.json", "w", encoding="utf-8") as f:
                json.dump(setting, f, ensure_ascii=False, indent=4)

            self.movie = QMovie(f"{dir_name}/闭眼.gif")
            self.label.setMovie(self.movie)
            self.movie.start()


    def put_pet(self):
        self.load_gif_from_setting()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # 记录鼠标按下状态
            self.is_mouse_pressed = True
            self.logger.debug("鼠标按下")
            self.drag_start_pos = event.position() # 记录鼠标按下时的位置
            self.setCursor(Qt.CursorShape.ClosedHandCursor) # 设置鼠标为抓手形状
            self.grab_pet()
        elif event.button() == Qt.MouseButton.RightButton:
            self.logger.debug("鼠标右键按下")
            # 检查状态窗口是否已显示
            if self.stat_window and self.stat_window.isVisible():
                # 如果状态窗口已显示，则隐藏它和食谱按钮
                self.hide_stat_window()
                self.hide_recipe_button()
            else:
                # 如果状态窗口未显示，则同时显示状态窗口和食谱按钮
                self.show_stat_window()
                self.show_recipe_button()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.position() - self.drag_start_pos  # 计算鼠标移动的距离
            self.move(self.pos() + delta.toPoint())  # 移动窗口位置
            # 安全隐藏所有悬浮窗口
            self.hide_stat_window()  # 隐藏状态窗口
            self.hide_recipe_button()  # 隐藏食谱按钮
    
    def mouseReleaseEvent(self, event):
        if hasattr(self, 'is_mouse_pressed') and self.is_mouse_pressed:
            # 检测到完整的点击动作（按下后释放）
            self.logger.debug(True)
            self.is_mouse_pressed = False
            self.put_pet()
        
        self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # 创建并显示聊天对话框（非模态）
            self.chat_dialog = ChatDialog(self)
            self.chat_dialog.setModal(False)
            self.chat_dialog.show()

    def dragEnterEvent(self, event):
        """处理拖拽进入事件"""
        if event.mimeData().hasUrls():
            # 检查拖拽的数据是否包含URLs（通常是文件）
            urls = event.mimeData().urls()
            for url in urls:
                file_path = url.toLocalFile()
                # 检查是否是图片文件
                if self.is_image_file(file_path):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def on_image_dropped(self, file_path):
        pass
    def dropEvent(self, event):
        """处理拖放事件"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                file_path = url.toLocalFile()
                if self.is_image_file(file_path):
                    # 图片拖放到宠物上，执行处理逻辑
                    self.logger.info(f"图片已拖放到宠物上: {file_path}")

                    
                    # 使用 pet_stats_manager 检查宠物状态前，先检查是否正在进食
                    if self.eating_timer.is_feeding():
                        warning_msg = "宠物正在进食，请等待当前食物吃完后再喂食！"
                        self.logger.debug(warning_msg)
                        from lib.temp_message_box import show_temp_message
                        show_temp_message(self, warning_msg, duration=1500, fade_duration=1000)
                        event.ignore()
                        self.image_drop_success = False
                        return
                    
                    # 尝试用食物喂养宠物，这将通过 pet_stats_manager 更新宠物状态
                    success, message, food_time_seconds = feed_pet_with_food(self, file_path) #success表示是否喂食成功，message是提示信息，food_time_seconds是食物的进食时间

                    

                    if success:
                        self.logger.info(message)
                        # 显示成功消息
                        self.add_system_message_to_chat(message)
                        #修改宠物形态为进食状态
                        self.eat_pet()
                    else:
                        self.logger.error(message)
                    
                    self.on_image_dropped(file_path)  #调用处理图片的方法
                    # event.acceptProposedAction() # 接受拖放事件
                    # 可以通过某种方式传递成功状态，而不是直接返回
                    # 例如，可以设置一个实例变量或者触发一个自定义信号
                    self.image_drop_success = True
                    return
        event.ignore() # 忽略非图片文件的拖放
        self.image_drop_success = False

    def is_image_file(self, file_path):
        """检查文件是否为图片格式"""
        if not file_path:
            return False
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp']
        _, ext = os.path.splitext(file_path.lower())
        return ext in image_extensions

    def handle_dropped_image(self, file_path):
        """处理拖放的图片文件"""
        # 在这里实现您需要的功能
        self.logger.debug(f"处理拖放的图片: {file_path}")
        
        # 示例：您可以设置为背景图或做其他处理
        # self.set_background_image(file_path)
        
        # 或者触发其他逻辑
        # self.process_dropped_image(file_path)

    def show_stat_window(self):
        """显示宠物状态窗口（饥饿度和水量）"""
        # 如果状态窗口不存在，则创建它
        if not self.stat_window:
            # 传递PetStatsManager中的状态值给状态窗口
            self.stat_window = StatBarWindow(
                self.pet_stats_manager.pet_hunger, 
                self.pet_stats_manager.pet_water, 
                parent=self
            )
            # 设置为顶层窗口
            self.stat_window.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        else:
            # 如果窗口已存在，更新值
            self.stat_window.update_values(
                round(self.pet_stats_manager.pet_hunger), 
                round(self.pet_stats_manager.pet_water)
            )
            # 更新进食状态显示
            remaining_time = self.eating_timer.calculate_remaining_time() if hasattr(self, 'eating_timer') else 0
            eating_state = {
                'remaining_time': remaining_time
            }
            self.stat_window.set_eating_state(eating_state)
        
        # 计算窗口位置，显示在宠物上方
        pet_geo = self.geometry()
        
        # 窗口位置：显示在宠物上方中央
        x = pet_geo.left() + (pet_geo.width() - self.stat_window.width()) // 2
        y = pet_geo.top() - self.stat_window.height() - 10  # 10像素间距
        
        # 检查是否超出屏幕上边界，如果超出则显示在下方
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        if y < 0:
            y = pet_geo.bottom() + 10

        self.stat_window.move(x, y)
        self.stat_window.show()
        self.logger.debug(f"状态窗口已显示在 ({x}, {y})")

    def hide_stat_window(self):
        """隐藏宠物状态窗口"""
        if self.stat_window:
            self.stat_window.hide()
            self.logger.debug("状态窗口已隐藏")

    def show_recipe_button(self):
        """显示食谱按钮"""
        # 如果食谱按钮不存在，则创建它
        if not self.recipe_button:
            # 直接创建食谱按钮，使用默认的food文件夹
            self.recipe_button = RecipeButton("outfood")
        
        # 计算按钮位置，出现在宠物右下角
        pet_size = self.size()
        
        # 按钮出现在宠物右下角
        x = pet_size.width() - 60  # 按钮宽度60
        y = pet_size.height() - 60  # 按钮高度60
        
        # 确保按钮在窗口内部
        x = max(0, x)
        y = max(0, y)
        
        self.recipe_button.move(x, y)
        self.recipe_button.setParent(self)  # 设置为当前窗口的子控件
        self.recipe_button.show()
        
        self.logger.info("食谱按钮已显示")

    def hide_recipe_button(self):
        """隐藏食谱按钮"""
        if self.recipe_button:
            self.recipe_button.hide()
            self.logger.debug("食谱按钮已隐藏")

    def show_setting_windows(self):
        if not self.setting_dialog:
            self.font_manager = FontManager()
            # 创建非模态设置对话框
            self.setting_dialog = CustomDialog(font_manager=self.font_manager)
            # 设置对话框为独立窗口，不会阻塞主窗口
            self.setting_dialog.setWindowFlags(
                self.setting_dialog.windowFlags() | 
                Qt.WindowType.WindowStaysOnTopHint |
                Qt.WindowType.Dialog
            )
            # 明确设置为非模态
            self.setting_dialog.setModal(False)
            # 连接对话框关闭信号
            self.setting_dialog.finished.connect(self.on_setting_closed)
            # 连接透明度变化信号
            self.setting_dialog.tab_widget.transparency_changed.connect(self.set_transparency)
            # 初始化透明度值
            self.transparency_value = self.setting_dialog.tab_widget.get_transparency_img_value()
    
        # 显示对话框（非阻塞）
        self.setting_dialog.show()
        # 确保对话框在最前面
        self.setting_dialog.raise_()
        self.setting_dialog.activateWindow()
        # 确保对话框关闭时不会退出应用程序
        self.setting_dialog.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
    
    def on_setting_closed(self):
        """设置窗口关闭后的清理"""
        if self.setting_dialog:
            self.setting_dialog.deleteLater()  # 确保对话框资源被正确释放
        self.setting_dialog = None

    def init_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)  # 创建系统托盘图标
        self.tray_icon.setIcon(QIcon('ico/ico.png'))  # 设置托盘图标
        self.tray_icon.setToolTip('Desktop Pet - 智能桌面宠物')  # 设置鼠标悬停提示
        
        # 连接托盘图标激活信号（双击等操作）
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
        menu = QMenu(self)  # 创建托盘菜单
        
        # 添加标题分隔符
        title_action = QAction('🐾 桌面宠物控制面板', self)
        title_action.setEnabled(False)  # 设置为不可点击
        menu.addAction(title_action)
        menu.addSeparator()
        
        show_action = QAction('📺 显示宠物', self)  # 创建显示菜单项
        show_action.triggered.connect(self.show)  # 绑定显示事件
        menu.addAction(show_action)  # 添加显示菜单项

        hide_action = QAction('👻 隐藏宠物', self)
        hide_action.triggered.connect(self.hide)  # 绑定隐藏事件
        menu.addAction(hide_action)  # 添加隐藏菜单项

        menu.addSeparator()  # 添加分隔符

        setting_action = QAction('⚙️ 设置', self)
        setting_action.triggered.connect(self.show_setting_windows)
        menu.addAction(setting_action)  # 添加设置菜单项

        # chat_action = QAction('💬 打开聊天', self)
        # chat_action.triggered.connect(self.open_chat_dialog)
        # menu.addAction(chat_action)  # 添加打开聊天菜单项

        menu.addSeparator()  # 添加分隔符

        exit_action = QAction('❌ 退出程序', self)  # 创建退出菜单项
        exit_action.triggered.connect(self.quit_application)  # 绑定退出事件
        menu.addAction(exit_action)  # 添加退出菜单项
        
        # 关键修复：设置托盘菜单
        self.tray_icon.setContextMenu(menu)
        
        self.tray_icon.show()  # 显示托盘图标

    def on_tray_icon_activated(self, reason):
        """处理托盘图标激活事件"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # 双击托盘图标时切换显示/隐藏状态
            if self.isVisible():
                self.hide()
                self.tray_icon.showMessage(
                    "Desktop Pet", 
                    "宠物已隐藏，双击图标可重新显示",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )
            else:
                self.show()
                self.raise_()
                self.activateWindow()
                self.tray_icon.showMessage(
                    "Desktop Pet", 
                    "宠物已显示",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )

    def quit_application(self):
        """优雅退出应用程序"""
        # 隐藏主窗口
        self.hide()
        # 隐藏所有子窗口
        if self.chat_dialog:
            self.chat_dialog.close()
        if self.stat_window:
            self.stat_window.close()
        if self.recipe_button:
            self.recipe_button.close()
        if self.setting_dialog:
            self.setting_dialog.close()
        # 退出应用程序
        QApplication.instance().quit()

    def open_chat_dialog(self):
        """从托盘菜单打开聊天对话框"""
        if not hasattr(self, 'chat_dialog') or not self.chat_dialog.isVisible():
            self.chat_dialog = ChatDialog(self)
            self.chat_dialog.setModal(False)
            self.chat_dialog.show()

    def showEvent(self, event):
        """窗口显示事件"""
        super().showEvent(event)
        # 窗口显示后启动提醒任务
        if not hasattr(self, '_reminder_started'):
            self._reminder_started = True
            
            # 启动宠物说话提醒（使用Qt定时器方式）
            self.pet_reminder.start_talk_reminder(self, 10*60)  # 每10分钟提醒一次
            self.pet_reminder.start_eat_reminder(self, 3*60) #每3分钟检查一次
            self.logger.info("宠物提醒任务已启动")

    def closeEvent(self, event):
        """窗口关闭事件 - 停止提醒任务"""
        # 停止提醒任务
        if hasattr(self, 'pet_reminder'):
            self.pet_reminder.stop_talk_reminder()
            self.pet_reminder.stop_eat_reminder()
        super().closeEvent(event)

    def save_eating_progress(self, progress_data):
        """保存进食进度到配置文件"""
        try:
            with open("demo_setting.json", "r", encoding="utf-8") as f:
                setting = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # 如果文件不存在或格式错误，初始化一个空字典
            setting = {}
        
        # 更新进食进度
        setting["eating_progress"] = progress_data

        # 写回文件
        with open("demo_setting.json", "w", encoding="utf-8") as f:
            json.dump(setting, f, ensure_ascii=False, indent=4)

    def load_eating_progress(self):
        """从配置文件加载进食进度并恢复"""
        try:
            with open("demo_setting.json", "r", encoding="utf-8") as f:
                setting = json.load(f)
            progress_data = setting.get("eating_progress", {})
            self.eating_timer.load_progress(progress_data)
        except (FileNotFoundError, json.JSONDecodeError):
            # 如果文件不存在或格式错误，不加载进度
            pass

    def interrupt_feeding(self):
        """中断宠物进食"""
        if hasattr(self, 'eating_timer') and self.eating_timer.is_feeding():
            # 获取当前已添加的营养值
            added_calories = self.eating_timer.added_calories
            added_water = self.eating_timer.added_water
            
            # 停止计时器
            self.eating_timer.timer.stop()
            
            # 重置进食状态
            self.eating_timer.start_time = None
            self.eating_timer.end_time = None
            self.eating_timer.total_time = 0
            self.eating_timer.current_food_calories = 0
            self.eating_timer.current_food_water = 0
            self.eating_timer.added_calories = 0
            self.eating_timer.added_water = 0
            
            # 保存进食进度
            self.save_eating_progress({})

            self.over_eat_pet() #修改宠物形态为非进食状态
            
            # 更新宠物状态
            self.pet_stats_manager.update_pet_stats(added_calories, added_water)
            
            # 显示中断消息
            message = f"进食已中断！获得: 饥饿度+{added_calories}, 水分+{added_water}"
            self.logger.debug(message)
            self.add_system_message_to_chat(message)
            
            # 更新状态窗口显示
            if self.stat_window and self.stat_window.isVisible():
                self.stat_window.set_eating_state({'remaining_time': 0})
                
            # 隐藏状态窗口中的中断按钮和倒计时
            if self.stat_window:
                self.stat_window.update_eating_timer(0)

    def add_system_message_to_chat(self, message):
        """添加系统消息到聊天框（如果聊天框存在）"""
        if hasattr(self, 'chat_dialog') and self.chat_dialog:
            self.chat_dialog.add_message("系统", message, is_user=False)

if __name__ == '__main__':
    

    app = QApplication(sys.argv)
    # 设置应用程序属性，确保在没有窗口显示时也能正常运行
    app.setQuitOnLastWindowClosed(False)
    
    pet = DesktopPet()
    # 恢复显示宠物窗口
    pet.show()
    # 确保窗口在最前面
    pet.raise_()
    pet.activateWindow()
    
    # 显示系统托盘提示消息
    pet.tray_icon.showMessage(
        "🐾 Desktop Pet 启动成功", 
        "宠物已显示在桌面上\n"
        "👉 右键点击托盘图标进行操作\n"
        "👉 双击图标快速显示/隐藏宠物",
        QSystemTrayIcon.MessageIcon.Information,
        5000  # 显示5秒
    )
    
    sys.exit(app.exec())