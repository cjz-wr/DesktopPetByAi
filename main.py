import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QSystemTrayIcon, QMenu, 
    QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox, QWidget, QPushButton, QScrollArea,
    QHBoxLayout, QMessageBox, QSplitter, QFrame
)
from PyQt6.QtGui import QIcon, QPixmap, QAction, QMovie, QTextCursor, QColor, QTextCharFormat, QFont, QImage, QPainter
from PyQt6.QtCore import Qt, QPoint, QThread, pyqtSignal

import zhipu
from settingwindow import CustomDialog,FontManager

class AIWorker(QThread):
    finished = pyqtSignal(str)  # 发送 AI 回复
    error = pyqtSignal(str)     # 发送错误信息

    def __init__(self, messages, parent=None):
        super().__init__(parent)
        self.messages = messages

    def run(self):
        try:
            reply = zhipu.get_ai_reply_sync(self.messages)
            self.finished.emit(reply)
        except Exception as e:
            self.error.emit(str(e))


class ChatDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ICAT")
        self.resize(600, 500)  # 增加窗口大小以适应聊天界面
        self.parent_window = parent

        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 创建分割器来管理聊天区域和输入区域
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 聊天历史区域
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 10px;
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
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.send_button = QPushButton("发送")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.send_button.setFixedWidth(100)
        
        self.clear_button = QPushButton("清空")
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
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
    
    def load_conversation(self):
        """加载历史对话并显示在聊天区域"""
        messages = zhipu.load_conversation("default")
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
        sender_format.setFontWeight(QFont.Weight.Bold)
        if is_user:
            sender_format.setForeground(QColor("#1a73e8"))  # 用户消息颜色
        else:
            sender_format.setForeground(QColor("#ea4335"))  # AI消息颜色
            
        cursor.insertText(f"{sender}: ", sender_format)
        
        # 添加消息内容
        message_format = QTextCharFormat()
        cursor.insertText(f"{message}\n\n", message_format)
        
        # 滚动到底部
        self.chat_history.verticalScrollBar().setValue(
            self.chat_history.verticalScrollBar().maximum()
        )
    
    def handle_send(self):
        input_text = self.input_edit.toPlainText().strip()
        if not input_text:
            QMessageBox.warning(self, "输入错误", "输入内容不能为空！")
            return
        
        # 添加用户消息到聊天区域
        self.add_message("你", input_text, is_user=True)
        
        # 构建消息
        messages = zhipu.load_conversation("default")
        messages.append({"role": "user", "content": input_text})
        zhipu.save_conversation("default", messages)
        
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
        
        # 添加AI回复
        self.add_message("ICAT", reply, is_user=False)
        
        # 保存对话
        messages = zhipu.load_conversation("default")
        messages.append({"role": "assistant", "content": reply})
        zhipu.save_conversation("default", messages)

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
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |  # 无边框窗口
            Qt.WindowType.WindowStaysOnTopHint | # 窗口置顶
            Qt.WindowType.Tool  # 作为工具窗口
        )
        self.init_tray_icon()
        self.setting_dialog = None  # 添加设置对话框引用
        self.transparency_value = 1.0  # 默认完全不透明
        # 设置初始窗口透明度
        self.setWindowOpacity(self.transparency_value)

        # 设置窗口背景透明
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # 创建一个标签用于显示动画
        self.label = QLabel(self)
        self.label.setStyleSheet("background-color: transparent;")  # 设置标签背景透明
        self.label.setScaledContents(True)  # 设置标签内容自适应大小
        self.setCentralWidget(self.label)   # 设置为主窗口的中央组件

        # 加载GIF动画
        self.load_gif_from_setting()

    def load_gif_from_setting(self):
        import json
        try:
            with open("demo_setting.json", "r", encoding="utf-8") as f:
                setting = json.load(f)
            gif_name = setting.get("gif", "2.gif")
            gif_path = gif_name
            # 如果不是绝对路径，则加上默认目录
            if not (gif_path.startswith("/") or ":" in gif_path):
                gif_path = f"gif/蜡笔小新组/{gif_name}"
        except Exception as e:
            print(f"读取demo_setting.json失败: {e}")
            gif_path = "gif/2.gif"
        self.movie = QMovie(gif_path)
        self.movie.frameChanged.connect(self.update_gif_transparency)
        self.label.setMovie(self.movie)
        self.movie.start()

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
            painter.setOpacity(self.transparency_value)
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
    
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # 创建并显示聊天对话框（非模态）
            self.chat_dialog = ChatDialog(self)
            self.chat_dialog.setModal(False)
            self.chat_dialog.show()

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
        self.tray_icon = QSystemTrayIcon(self) # 创建系统托盘图标
        self.tray_icon.setIcon(QIcon('ico/ico.png'))  # 设置托盘图标
        self.tray_icon.setToolTip('Desktop Pet')  # 设置鼠标悬停提示
        
        menu = QMenu(self)  # 创建托盘菜单
        
        show_action = QAction('显示', self)  # 创建显示菜单项
        show_action.triggered.connect(self.show)  # 绑定显示事件
        menu.addAction(show_action)  # 添加显示菜单项

        hide_action = QAction('隐藏', self)
        hide_action.triggered.connect(self.hide)  # 绑定隐藏事件
        menu.addAction(hide_action)  # 添加隐藏菜单项

        setting_action = QAction('更多', self)
        setting_action.triggered.connect(self.show_setting_windows)
        menu.addAction(setting_action)  # 添加设置菜单项

        # chat_action = QAction('打开聊天', self)
        # chat_action.triggered.connect(self.open_chat_dialog)
        # menu.addAction(chat_action)  # 添加打开聊天菜单项

        self.tray_icon.setContextMenu(menu)  # 设置托盘菜单

        exit_action = QAction('退出', self)  # 创建退出菜单项
        exit_action.triggered.connect(lambda: sys.exit(0))  # 绑定退出事件
        menu.addAction(exit_action)  # 添加退出菜单项
        
        self.tray_icon.show()  # 显示托盘图标

    def open_chat_dialog(self):
        """从托盘菜单打开聊天对话框"""
        if not hasattr(self, 'chat_dialog') or not self.chat_dialog.isVisible():
            self.chat_dialog = ChatDialog(self)
            self.chat_dialog.setModal(False)
            self.chat_dialog.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.position() # 记录鼠标按下时的位置
            self.setCursor(Qt.CursorShape.ClosedHandCursor) # 设置鼠标为抓手形状

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.position() - self.drag_start_pos # 计算鼠标移动的距离
            self.move(self.pos() + delta.toPoint()) # 移动窗口位置
    
    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    pet = DesktopPet()
    pet.show()
    sys.exit(app.exec())