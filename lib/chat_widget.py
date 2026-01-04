import sys
import json, os
from PyQt6.QtWidgets import (QApplication, QStackedWidget, QDialog, QFontDialog, QStyle, QButtonGroup, 
                            QFrame, QVBoxLayout, QDoubleSpinBox, QSpinBox, QFileDialog, QTabBar, 
                            QHBoxLayout, QLabel, QPushButton, QWidget, QTabWidget, QScrollArea,
                            QTextEdit, QDialogButtonBox, QMessageBox, QSplitter, QMenu, QSystemTrayIcon, QComboBox, QLineEdit)
from PyQt6.QtCore import Qt, QPoint, QSize, QRectF, pyqtSignal, QObject, QRect, QThread
from PyQt6.QtGui import (QIcon, QMouseEvent, QPainter, QImage, QPixmap, QFontMetrics, QPen, QColor, 
                         QPainterPath, QFont, QTextCursor, QTextCharFormat, QMovie)
import zhipu as zhipu

import lib.toVoice as toVoice

class AIWorker(QThread):
    """AI工作线程"""
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

class ChatWidget(QWidget):
    """聊天界面组件"""
    def __init__(self, font_manager=None, parent=None):
        super().__init__(parent)
        self.font_manager = font_manager
        self.init_ui()
        
    def init_ui(self):
        """初始化UI布局"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建分割器来管理聊天区域和输入区域
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 聊天历史区域
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                background-color: rgba(240, 240, 240, 220);
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        # 注册字体
        if self.font_manager:
            self.font_manager.register_widget(self.chat_history)
        
        # 输入区域
        input_frame = QFrame()
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(0, 0, 0, 0)
        
        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText("输入消息...")
        self.input_edit.setMaximumHeight(100)
        self.input_edit.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 255, 255, 200);
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        
        # 注册字体
        if self.font_manager:
            self.font_manager.register_widget(self.input_edit)
        
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
        
        # 注册字体
        if self.font_manager:
            self.font_manager.register_widget(self.send_button)
        
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
        
        # 注册字体
        if self.font_manager:
            self.font_manager.register_widget(self.clear_button)
        
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
        self.load_conversation()
    
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
        message_format.setForeground(QColor("#333333"))
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

        # 异步输出音频
        toVoice.TextToSpeech().speak_async(reply)
        
        # 重新启用发送按钮
        self.send_button.setEnabled(True)
        self.input_edit.setEnabled(True)
        self.input_edit.setFocus()
        
        # 通知主窗口刷新GIF动画
        # 兼容通过main.py打开的settingwindow.py
        main_window = None
        parent = self.parent()
        while parent is not None:
            # 直接QMainWindow或DesktopPet
            if hasattr(parent, "refresh_gif"):
                main_window = parent
                break
            # QDialog嵌套时再向上找
            if hasattr(parent, "parent"):
                parent = parent.parent()
            else:
                break
        # 如果没找到，再尝试通过QApplication遍历所有顶层窗口
        if main_window is None:
            for widget in QApplication.topLevelWidgets():
                if hasattr(widget, "refresh_gif"):
                    main_window = widget
                    break
        if main_window and hasattr(main_window, "refresh_gif"):
            main_window.refresh_gif()
    
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