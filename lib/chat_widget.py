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
import logging, os
import time,re
import lib.imgin as imgin
import asyncio
import threading

class AIWorker(QThread):
    """AI工作线程"""
    finished = pyqtSignal(str)  # 发送 AI 回复
    error = pyqtSignal(str)     # 发送错误信息

    def __init__(self, messages, parent=None):
        super().__init__(parent)
        self.messages = messages # AI 对话消息列表

    def run(self):
        try:
            reply = zhipu.get_ai_reply_sync(self.messages) # 获取AI回复的同步方法·
            self.finished.emit(reply)
        except Exception as e:
            self.error.emit(str(e))

class ImageAnalysisWorker(QThread):
    """图片分析工作线程"""
    finished = pyqtSignal(str)  # 发送 图片分析结果
    error = pyqtSignal(str)     # 发送错误信息

    def __init__(self, image_path, prompt_text="", parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.prompt_text = prompt_text

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(imgin.analyze_image_with_ai(self.image_path, prompt_text=self.prompt_text))
            loop.close()
            self.finished.emit(result)
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
        # 设置接受拖放
        self.chat_history.setAcceptDrops(True)
        self.chat_history.dragEnterEvent = self.drag_enter_event
        self.chat_history.dropEvent = self.drop_event
        
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
        
        self.image_button = QPushButton("发送\n图片")
        self.image_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        self.image_button.setFixedWidth(100)
        
        # 注册字体
        if self.font_manager:
            self.font_manager.register_widget(self.image_button)
        
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
        
        button_layout.addWidget(self.image_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        button_layout.addWidget(self.send_button)
        
        input_layout.addWidget(self.input_edit)
        input_layout.addLayout(button_layout)
        
        # 添加图片预览区域
        self.image_preview = QLabel()
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setMinimumHeight(100)
        self.image_preview.setMaximumHeight(150)
        self.image_preview.hide()
        self.image_preview.mousePressEvent = self.remove_image_preview
        input_layout.addWidget(self.image_preview)
        
        # 添加预览清除按钮
        self.clear_image_button = QPushButton("移除图片")
        self.clear_image_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        self.clear_image_button.setFixedWidth(100)
        self.clear_image_button.hide()
        self.clear_image_button.clicked.connect(self.remove_image_preview)
        input_layout.addWidget(self.clear_image_button)
        
        
        # 添加到分割器
        splitter.addWidget(self.chat_history)
        splitter.addWidget(input_frame)
        splitter.setSizes([400, 100])  # 设置初始大小比例
        
        main_layout.addWidget(splitter)
        
        # 连接信号
        self.send_button.clicked.connect(self.handle_send)
        self.image_button.clicked.connect(self.select_and_send_image)
        self.clear_button.clicked.connect(self.clear_chat)
        
        # 加载历史对话
        self.load_conversation()
    
    def drag_enter_event(self, event):
        """处理拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def drop_event(self, event):
        """处理拖拽放置事件"""
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                self.add_image_to_chat(file_path)
                break  # 只处理第一个图片文件

    def select_and_send_image(self):
        """选择并发送图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", "图片文件 (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        if file_path:
            self.add_image_to_chat(file_path)

    def add_image_to_chat(self, image_path):
        """在聊天中添加图片"""
        # 显示预览图
        pixmap = QPixmap(image_path)
        scaled_pixmap = pixmap.scaled(400, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.image_preview.setPixmap(scaled_pixmap)
        self.image_preview.show()
        self.clear_image_button.show()
        # 保存图片路径以备发送
        self.current_image_path = image_path

    def remove_image_preview(self, event=None):
        """移除图片预览"""
        self.image_preview.clear()
        self.image_preview.hide()
        self.clear_image_button.hide()
        if hasattr(self, 'current_image_path'):
            delattr(self, 'current_image_path')

    def load_conversation(self):
        """加载历史对话并显示在聊天区域"""
        messages = zhipu.load_conversation("default")
        for msg in messages:
            if msg['role'] == 'user':
                # 检查用户消息是否包含图片路径
                if 'image_path' in msg and msg['image_path']:
                    self.add_message("你", msg['content'], is_user=True, image_path=msg['image_path'])
                elif '*SEND*用户向你发送了一' in msg['content']:
                    pass  # 跳过特殊标记的消息
                else:
                    self.add_message("你", msg['content'], is_user=True)
            elif msg['role'] == 'assistant':
                # 检查AI回复是否包含图片引用
                content = msg['content']
                if "[IMAGE_NAME:" in content:
                    # 提取图片名称
                    reply_img = re.search(r'\[IMAGE_NAME:\s*(.+?)\]', content).group(1).strip()
                    imgPath = os.path.join("imgs", reply_img)
                    # 判断图片是否存在
                    if os.path.exists(imgPath):
                        # 改为绝对路径
                        imgPath = os.path.abspath(imgPath)
                        # 提取纯文本内容
                        text_content = content.replace(f"[IMAGE_NAME: {reply_img}]", "").strip()
                        if text_content != "":
                            self.add_message("ICAT", text_content, is_user=False, image_path=imgPath)
                        else:
                            self.add_message("ICAT", "", is_user=False, image_path=imgPath)
                    else:
                        self.add_message("ICAT", "抱歉，没有找到表情包呢", is_user=False)
                else:
                    self.add_message("ICAT", content, is_user=False)
    
    def add_message(self, sender, message, is_user=True, image_path=None):
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
        cursor.insertText(f"{message}\n", message_format)
        
        # 如果有图片，则添加图片
        if image_path:
            cursor.insertText("\n")  # 添加换行
            # 加载并缩放图片
            image = QImage(image_path)
            # 验证图片是否有效
            if image.isNull():
                cursor.insertText("图片加载失败\n")
            else:
                # 缩放到最大宽度为300像素，保持宽高比
                scaled_image = image.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                # 插入图片到文档中
                cursor.insertImage(scaled_image, f"image_{os.path.basename(image_path)}")
                cursor.insertText("\n")  # 图片后换行
        
        cursor.insertText("\n")  # 添加额外换行分隔消息

        # 滚动到底部
        self.chat_history.verticalScrollBar().setValue(
            self.chat_history.verticalScrollBar().maximum()
        )
    
    def save_message_to_history(self, sender, message, image_path=None):
        """保存消息到历史记录，如果是用户消息且包含图片，需要特殊处理"""
        # 如果是用户消息且包含图片，我们需要在消息中添加图片路径信息
        if sender == "你" and image_path:
            # 保存消息时，将图片路径信息加入到消息内容中
            message_data = {
                "role": "user",
                "content": message,
                "image_path": image_path
            }
        elif sender == "ICAT" and "[IMAGE_NAME:" in message:
            # AI回复包含图片的情况，保持原有格式
            message_data = {
                "role": "assistant", 
                "content": message
            }
        else:
            # 普通文本消息
            role = "user" if sender == "你" else "assistant"
            message_data = {
                "role": role,
                "content": message
            }
        
        # 加载现有对话并添加新消息
        messages = zhipu.load_conversation("default")
        messages.append(message_data)
        zhipu.save_conversation("default", messages)
    
    def GetAiByImg(self,img_path,text):
        # 先将用户消息（包括图片）添加到聊天区域
        self.add_message("你", text, is_user=True, image_path=img_path)
        # 保存包含图片路径的消息到历史记录
        self.save_message_to_history("你", text, image_path=img_path)
        
        # 禁用发送按钮，防止重复发送
        self.send_button.setEnabled(False)
        self.input_edit.setEnabled(False)
        self.image_button.setEnabled(False)
        
        # 显示加载提示
        self.add_message("系统", "正在分析图片...", is_user=False)
        
        # 创建并启动图片分析工作线程，如果有文本输入则作为prompt_text参数
        if text:
            self.image_worker = ImageAnalysisWorker(img_path, prompt_text=text)
        else:
            self.image_worker = ImageAnalysisWorker(img_path)
        self.image_worker.finished.connect(lambda result: self.process_img_text_message(result, img_path, text))
        self.image_worker.error.connect(self.on_ai_error)
        self.image_worker.start()
        
        # 清空输入框和图片预览
        self.input_edit.clear()
        self.remove_image_preview()
    
    def process_img_text_message(self, image_description, img_path, text):
        """处理图片和文本消息"""
        # 构建消息 - 合并文本和图片信息
        messages = zhipu.load_conversation("default")
        if text:
            # 既有图片又有文字
            messages.append({"role": "user", "content": f"**SEND*用户向你发送了一张图片，这是图片描述:{image_description}\n用户还说了以下内容:{text}"})
        else:
            # 只有图片的情况
            messages.append({"role": "user", "content": f"**SEND*用户向你发送了一下内容的图片{image_description}"})
        zhipu.save_conversation("default", messages)
        
        # 更新之前的"正在分析图片"消息为AI正在思考
        for i in range(3):  # 移除之前的几行
            self.chat_history.undo()
        self.add_message("系统", "ICAT 正在思考...", is_user=False)
        
        # 创建并启动AI工作线程
        self.worker = AIWorker(messages)
        self.worker.finished.connect(self.on_ai_reply_received)
        self.worker.error.connect(self.on_ai_error)
        self.worker.start()
    
    def process_message_with_image(self, image_description, input_text):
        """处理包含图片的消息"""
        # 构建消息 - 如果既有文本又有图片，合并在一起
        messages = zhipu.load_conversation("default")
        if input_text:
            # 既有图片又有文本
            messages.append({"role": "user", "content": f"*SEND*用户向你发送了一张图片，这是图片描述:{image_description}\n用户还说了以下内容:{input_text}"})
        else:
            # 只有图片的情况
            messages.append({"role": "user", "content": f"*SEND*用户向你发送了一下内容的图片{image_description}"})
        zhipu.save_conversation("default", messages)
        
        # 更新之前的"正在分析图片"消息为AI正在思考
        for i in range(3):  # 移除之前的几行
            self.chat_history.undo()
        self.add_message("系统", "ICAT 正在思考...", is_user=False)
        
        # 创建并启动AI工作线程
        self.worker = AIWorker(messages)
        self.worker.finished.connect(self.on_ai_reply_received)
        self.worker.error.connect(self.on_ai_error)
        self.worker.start()
    
    def start_analysis_and_ai_processing(self, image_description, input_text):
        """开始图片分析和AI处理流程"""
        self.process_message_with_image(image_description, input_text)
    
    def clear_chat(self):
        """清空当前聊天界面（不删除历史记录）"""
        self.chat_history.clear()
        # self.load_conversation()  # 重新加载历史记录

    def handle_send(self):
        input_text = self.input_edit.toPlainText().strip()
        image_path = getattr(self, 'current_image_path', None)
        
        # 检查是否没有输入文本且没有图片
        if not input_text and not image_path:
            QMessageBox.warning(self, "输入错误", "请输入消息内容或选择一张图片！")
            return
        
        # 如果有图片，先将用户消息（包括图片）添加到聊天区域
        if image_path:
            self.add_message("你", input_text, is_user=True, image_path=image_path)
            # 保存包含图片路径的消息到历史记录
            self.save_message_to_history("你", input_text, image_path=image_path)
        else:
            # 只有文本，添加到聊天区域
            self.add_message("你", input_text, is_user=True)
            # 保存文本消息到历史记录
            self.save_message_to_history("你", input_text)
        
        # 禁用发送按钮，防止重复发送
        self.send_button.setEnabled(False)
        self.input_edit.setEnabled(False)
        self.image_button.setEnabled(False)
        
        # 显示加载提示
        if image_path:
            self.add_message("系统", "正在分析图片...", is_user=False)
            # 创建并启动图片分析工作线程，如果有文本输入则作为prompt_text参数
            if input_text:
                self.image_worker = ImageAnalysisWorker(image_path, prompt_text=input_text)
            else:
                self.image_worker = ImageAnalysisWorker(image_path)
            self.image_worker.finished.connect(lambda result: self.start_analysis_and_ai_processing(result, input_text))
            self.image_worker.error.connect(self.on_ai_error)
            self.image_worker.start()
            
            # 清空输入框和图片预览
            self.input_edit.clear()
            self.remove_image_preview()
        else:
            # 没有图片，直接处理文本消息
            self.process_text_only_message(input_text)
    
    def process_text_only_message(self, input_text):
        """处理只有文本的消息"""
        # # 添加用户消息到聊天区域
        # self.add_message("你", input_text, is_user=True)
        
        # # 保存消息到历史记录
        # self.save_message_to_history("你", input_text)
        
        # 构建消息
        messages = zhipu.load_conversation("default")
        messages.append({"role": "user", "content": input_text})
        zhipu.save_conversation("default", messages)
        
        # 显示加载提示
        self.add_message("系统", "ICAT 正在思考...", is_user=False)
        
        # 创建并启动AI工作线程
        self.worker = AIWorker(messages)
        self.worker.finished.connect(self.on_ai_reply_received)
        self.worker.error.connect(self.on_ai_error)
        self.worker.start()
    
    def on_ai_reply_received(self, reply):
        # 移除"AI正在思考"提示
        # 计算需要撤销的次数，每次添加消息插入了多行内容
        for i in range(3):  # 对于添加消息时的几行内容
            self.chat_history.undo()
        

        if "[IMAGE_NAME:" in reply:
            reply_img = re.search(r'\[IMAGE_NAME:\s*(.+?)\]', reply).group(1).strip()
            imgPath = os.path.join("imgs", reply_img)
            #判断图片是否存在
            if os.path.exists(imgPath):
                #改为绝对路径
                imgPath = os.path.abspath(imgPath)
                print(reply.replace(f"[IMAGE_NAME: {reply_img}]", "").strip())
                if reply.replace(f"[IMAGE_NAME: {reply_img}]", "").strip() != "":
                    self.add_message("ICAT", reply.replace(f"[IMAGE_NAME: {reply_img}]", "").strip(), is_user=False, image_path=imgPath)
                else:
                    self.add_message("ICAT", "", is_user=False, image_path=imgPath)
            else:
                self.add_message("ICAT", "抱歉，没有找到表情包呢", is_user=False)
        else:
            # 添加AI回复
            self.add_message("ICAT", reply, is_user=False)
            # 异步输出音频
            toVoice.TextToSpeech().speak_async(reply)
        
        
        # 保存AI回复到对话历史
        messages = zhipu.load_conversation("default")
        messages.append({"role": "assistant", "content": reply})
        zhipu.save_conversation("default", messages)

        
        
        # 重新启用发送按钮
        self.send_button.setEnabled(True)
        self.input_edit.setEnabled(True)
        self.image_button.setEnabled(True)
        # 清空输入框
        self.input_edit.clear()
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
        # 如果没找到，再尝试通过QApplication遍历所有 topLevel 窗口
        if main_window is None:
            for widget in QApplication.topLevelWidgets():
                if hasattr(widget, "refresh_gif"):
                    main_window = widget
                    break
        if main_window and hasattr(main_window, "refresh_gif"):
            main_window.refresh_gif()

    def on_ai_error(self, error_msg):
        # 移除"AI正在思考"提示
        for i in range(3):  # 对于添加消息时的几行内容
            self.chat_history.undo()
        
        # 显示错误信息
        self.add_message("系统", f"发生错误：{error_msg}", is_user=False)
        
        # 重新启用发送按钮
        self.send_button.setEnabled(True)
        self.input_edit.setEnabled(True)
        self.image_button.setEnabled(True)
        self.input_edit.setFocus()
    
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.handle_send()
                event.accept()
                return
        super().keyPressEvent(event)
