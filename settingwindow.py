import sys
import json, os
from PyQt6.QtWidgets import (QApplication, QStackedWidget, QDialog, QFontDialog, QStyle, QButtonGroup, 
                            QFrame, QVBoxLayout, QDoubleSpinBox, QSpinBox, QFileDialog, QTabBar, 
                            QHBoxLayout, QLabel, QPushButton, QWidget, QTabWidget, QScrollArea,
                            QTextEdit, QDialogButtonBox, QMessageBox, QSplitter, QMenu, QSystemTrayIcon, QComboBox, QLineEdit)
from PyQt6.QtCore import Qt, QPoint, QSize, QRectF, pyqtSignal, QObject, QRect, QThread
from PyQt6.QtGui import (QIcon, QMouseEvent, QPainter, QImage, QPixmap, QFontMetrics, QPen, QColor, 
                         QPainterPath, QFont, QTextCursor, QTextCharFormat, QMovie)
import zhipu

import toVoice

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

class FontManager(QObject):
    font_changed_signal = pyqtSignal(QFont)

    def __init__(self):
        super().__init__()
        self.font = QFont("SimSun", 12)  # 默认字体
        self.widgets = []  # 存储需要同步字体的所有控件

    def register_widget(self, widget):
        """注册一个需要同步字体的控件"""
        if widget not in self.widgets:
            self.widgets.append(widget)
            widget.setFont(self.font)  # 初始化字体
            return True
        return False

    def change_font(self, font):
        """更改字体并通知所有注册的控件"""
        self.font = font
        self.font_changed_signal.emit(font)

    def load_from_dict(self, font_dict):
        """从字典恢复字体"""
        font = QFont()
        font.setFamily(font_dict.get("family", "SimSun"))
        point_size = font_dict.get("pointSize")
        if point_size and point_size > 0:
            font.setPointSize(point_size)
        font.setBold(font_dict.get("bold", False))
        font.setItalic(font_dict.get("italic", False))
        font.setUnderline(font_dict.get("underline", False))
        weight = font_dict.get("weight", QFont.Weight.Normal)
        font.setWeight(weight)
        self.change_font(font)

    def to_dict(self):
        """将当前字体转为字典用于保存"""
        return {
            "family": self.font.family(),
            "pointSize": self.font.pointSize(),
            "bold": self.font.bold(),
            "italic": self.font.italic(),
            "underline": self.font.underline(),
            "weight": self.font.weight(),
        }

    def update_registered_widgets(self, new_font):
        """更新所有已注册控件的字体"""
        for widget in self.widgets:
            widget.setFont(new_font)

class VerticalTabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paintEvent(self, event):
        painter = QPainter(self)
        font_metrics = QFontMetrics(self.font())

        for i in range(self.count()):
            rect = self.tabRect(i)
            text = self.tabText(i)

            # 设置选中样式
            if i == self.currentIndex():
                painter.fillRect(rect, Qt.GlobalColor.gray)
                painter.setFont(self.font())
                painter.setPen(Qt.GlobalColor.white)
            else:
                color = QColor(211, 211, 211)  # LightGray
                color.setAlpha(150)  # 设置透明度（0-255之间）
                painter.fillRect(rect, color)
                painter.setFont(self.font())
                painter.setPen(Qt.GlobalColor.black)

            # 逐字竖排绘制
            x = rect.left() + 10
            y = rect.top() + font_metrics.ascent()
            for char in text:
                painter.drawText(x, y, char)
                y += font_metrics.height()


class VerticalTabWidget(QWidget):
    # 添加信号用于通知设置变化
    transparency_changed = pyqtSignal(float)
    luminance_changed = pyqtSignal(int)
    background_changed = pyqtSignal(str)
    
    def __init__(self, parent=None, font_manager=None):
        super().__init__(parent)
        self.font_manager = font_manager
        self.data_setting = self.load_settings()
        
        # 加载保存的字体设置
        if "font" in self.data_setting:
            self.font_manager.load_from_dict(self.data_setting["font"])
        
        # 主布局：左侧按钮 + 右侧堆叠页面
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 左侧按钮区域
        button_container = QWidget()
        button_container.setFixedWidth(150)  # 固定宽度使布局更整齐
        button_container.setStyleSheet("background-color: transparent;")  # 设置透明背景
        button_layout = QVBoxLayout(button_container)
        button_layout.setContentsMargins(5, 10, 5, 10)
        button_layout.setSpacing(5)
        
        # 自定义样式表 - 更新为透明背景
        button_style = """
            QPushButton {
                text-align: left;
                padding: 12px 16px;
                margin: 2px 0;
                border: none;
                border-radius: 5px;
                background-color: rgba(240, 240, 240, 150);  /* 半透明背景 */
                font-size: 14px;
                color: #333;
            }
            QPushButton:hover {
                background-color: rgba(224, 224, 224, 180);  /* 半透明悬停效果 */
            }
            QPushButton:checked {
                background-color: rgba(77, 148, 255, 200);  /* 半透明选中效果 */
                color: white;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: rgba(58, 123, 213, 200);  /* 半透明按下效果 */
            }
        """
        
        # 创建按钮组
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.tab_buttons = []
        
        # 标签名称和图标
        tab_names = ["聊天", "设置", "帮助&关于"]
        icons = [
            QStyle.StandardPixmap.SP_ComputerIcon,
            QStyle.StandardPixmap.SP_FileDialogDetailedView,
            QStyle.StandardPixmap.SP_DialogHelpButton
        ]
        
        # 创建堆叠页面
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background-color: transparent;")  # 设置透明背景
        
        # 创建三个页面
        self.tab1 = QWidget()
        self.tab1.setStyleSheet("background-color: transparent;")  # 设置透明背景
        self.tab2 = QWidget()
        self.tab2.setStyleSheet("background-color: transparent;")  # 设置透明背景
        self.tab3 = QWidget()
        self.tab3.setStyleSheet("background-color: transparent;")  # 设置透明背景
        
        self.stacked_widget.addWidget(self.tab1)
        self.stacked_widget.addWidget(self.tab2)
        self.stacked_widget.addWidget(self.tab3)
        
        # 初始化页面内容
        self.init_tab1_ui()
        self.init_tab2_ui()
        self.init_tab3_ui()
        
        # 创建按钮
        for i, (name, icon) in enumerate(zip(tab_names, icons)):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setStyleSheet(button_style)
            btn.setIcon(self.style().standardIcon(icon))
            btn.setIconSize(QSize(24, 24))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            # 注册按钮到字体管理器
            if self.font_manager:
                self.font_manager.register_widget(btn)
            
            self.button_group.addButton(btn, i)
            self.tab_buttons.append(btn)
            button_layout.addWidget(btn)
        
        # 添加弹簧使按钮顶部对齐
        button_layout.addStretch()
        
        # 设置第一个按钮为选中状态
        self.tab_buttons[0].setChecked(True)
        
        # 连接信号
        self.button_group.buttonClicked.connect(self.switch_tab)
        
        # 添加分隔线 - 更新为半透明
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: rgba(208, 208, 208, 150);")  # 半透明分隔线
        
        # 添加到主布局
        main_layout.addWidget(button_container, 0)
        main_layout.addWidget(separator, 0)
        main_layout.addWidget(self.stacked_widget, 1)

    def switch_tab(self, button):
        index = self.button_group.id(button)
        self.stacked_widget.setCurrentIndex(index)
    
    def load_settings(self):
        setting_path = "demo_setting.json"
        if not os.path.exists(setting_path):
            with open(setting_path, "w", encoding="utf-8") as f:
                f.write("{}")
            return {}

        try:
            with open(setting_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            with open(setting_path, "w", encoding="utf-8") as f:
                f.write("{}")
            return {}
    
    def init_tab1_ui(self):
        """初始化主界面标签页 - 添加AI聊天功能"""
        layout = QVBoxLayout(self.tab1)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 添加聊天组件
        chat_widget = ChatWidget(self.font_manager)
        layout.addWidget(chat_widget)
    
    def init_tab2_ui(self):
        """初始化设置标签页 - 添加滚动功能"""
        # 创建主布局
        main_layout = QVBoxLayout(self.tab2)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(200, 200, 200, 100);
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(150, 150, 150, 150);
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
            }
        """)
        
        # 创建滚动内容部件
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(20, 20, 30, 20)  # 右边距增加以适应滚动条
        scroll_layout.setSpacing(15)
        
        # 图片选择区域
        img_group = QWidget()
        img_group.setStyleSheet("background-color: rgba(255, 255, 255, 150); border-radius: 5px; padding: 10px;")  # 半透明背景
        img_layout = QVBoxLayout(img_group)
        
        bg_setting_label = QLabel("<b style='color: black;'>背景图片设置</b>")
        if self.font_manager:
            self.font_manager.register_widget(bg_setting_label)
        img_layout.addWidget(bg_setting_label)
        
        self.img_label = QLabel("未选择任何文件")
        self.img_label.setWordWrap(True)
        if self.font_manager:
            self.font_manager.register_widget(self.img_label)
        
        if "background_path" in self.data_setting and self.data_setting["background_path"]:
            self.img_label.setText(self.data_setting["background_path"])

        select_button = QPushButton("选择背景图片")
        select_button.setStyleSheet("padding: 8px; background-color: rgba(240, 240, 240, 200);")  # 半透明按钮
        select_button.clicked.connect(self.show_file_dialog)
        if self.font_manager:
            self.font_manager.register_widget(select_button)

        img_layout.addWidget(select_button)
        img_layout.addWidget(self.img_label)
        
        scroll_layout.addWidget(img_group)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("margin: 15px 0; background-color: rgba(255, 255, 255, 100);")  # 半透明分隔线
        scroll_layout.addWidget(line)

        # 浮点数设置区域 - 图片透明度 (0.0 ~ 1.0)
        self.spin_label = QLabel(f"<span style='color: black;'>图片透明度当前值(0.0~1.0)：{self.get_transparency_img_value()}</span>")
        if self.font_manager:
            self.font_manager.register_widget(self.spin_label)
            
        self.double_spin = QDoubleSpinBox()
        self.double_spin.setStyleSheet("background-color: rgba(255, 255, 255, 200);")  # 半透明背景
        self.double_spin.setRange(0.0, 1.0)
        self.double_spin.setSingleStep(0.1)
        self.double_spin.setDecimals(1)
        self.double_spin.setValue(self.get_transparency_img_value())
        self.double_spin.valueChanged.connect(self.on_value_changed_img)
        if self.font_manager:
            self.font_manager.register_widget(self.double_spin)

        trans_label = QLabel("<b style='color: black;'>图片透明度</b>")
        if self.font_manager:
            self.font_manager.register_widget(trans_label)
            
        scroll_layout.addWidget(trans_label)
        scroll_layout.addWidget(self.spin_label)
        scroll_layout.addWidget(self.double_spin)

        # 分隔线
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFrameShadow(QFrame.Shadow.Sunken)
        line2.setStyleSheet("margin: 15px 0; background-color: rgba(255, 255, 255, 100);")  # 半透明分隔线
        scroll_layout.addWidget(line2)

        # 整数设置区域 - 透明度或亮度 (0 ~ 255)
        self.int_label = QLabel(f"<span style='color: black;'>亮度值当前值(0~255)：{self.get_luminance_img_value()}</span>")
        if self.font_manager:
            self.font_manager.register_widget(self.int_label)
            
        self.int_spin = QSpinBox()
        self.int_spin.setStyleSheet("background-color: rgba(255, 255, 255, 200);")  # 半透明背景
        self.int_spin.setRange(0, 255)
        self.int_spin.setSingleStep(1)
        self.int_spin.setValue(self.get_luminance_img_value())  # 获取之前保存的值
        self.int_spin.valueChanged.connect(self.on_value_changed_int)
        if self.font_manager:
            self.font_manager.register_widget(self.int_spin)

        luminance_label = QLabel("<b style='color: black;'>图片亮度</b>")
        if self.font_manager:
            self.font_manager.register_widget(luminance_label)
            
        scroll_layout.addWidget(luminance_label)
        scroll_layout.addWidget(self.int_label)
        scroll_layout.addWidget(self.int_spin)

        # 分隔线
        line3 = QFrame()
        line3.setFrameShape(QFrame.Shape.HLine)
        line3.setFrameShadow(QFrame.Shadow.Sunken)
        line3.setStyleSheet("margin: 15px 0; background-color: rgba(255, 255, 255, 100);")  # 半透明分隔线
        scroll_layout.addWidget(line3)

        # AI Key 设置区域
        ai_key_group = QWidget()
        ai_key_group.setStyleSheet("background-color: rgba(255, 255, 255, 150); border-radius: 5px; padding: 10px;")
        ai_key_layout = QVBoxLayout(ai_key_group)

        ai_key_label = QLabel("<b style='color: black;'>AI Key 设置</b>")
        if self.font_manager:
            self.font_manager.register_widget(ai_key_label)
        ai_key_layout.addWidget(ai_key_label)

        self.ai_key_edit = QTextEdit()
        self.ai_key_edit.setPlaceholderText("请输入新的AI Key...")
        self.ai_key_edit.setMaximumHeight(60)
        self.ai_key_edit.setStyleSheet("background-color: rgba(255, 255, 255, 200); border: 1px solid #cccccc; border-radius: 5px; padding: 8px;")
        if self.font_manager:
            self.font_manager.register_widget(self.ai_key_edit)
        ai_key_layout.addWidget(self.ai_key_edit)

        # 加载当前AI Key
        self.load_ai_key()

        save_ai_key_button = QPushButton("保存AI Key")
        save_ai_key_button.setStyleSheet("padding: 8px; background-color: rgba(240, 240, 240, 200);")
        save_ai_key_button.clicked.connect(self.save_ai_key)
        if self.font_manager:
            self.font_manager.register_widget(save_ai_key_button)
        ai_key_layout.addWidget(save_ai_key_button)

        scroll_layout.addWidget(ai_key_group)

        # 分隔线
        line4 = QFrame()
        line4.setFrameShape(QFrame.Shape.HLine)
        line4.setFrameShadow(QFrame.Shadow.Sunken)
        line4.setStyleSheet("margin: 15px 0; background-color: rgba(255, 255, 255, 100);")  # 半透明分隔线
        scroll_layout.addWidget(line4)

        # 模型选择区域
        model_group = QWidget()
        model_group.setStyleSheet("background-color: rgba(255, 255, 255, 150); border-radius: 5px; padding: 10px;")
        model_layout = QVBoxLayout(model_group)

        model_label = QLabel("<b style='color: black;'>模型选择</b>")
        if self.font_manager:
            self.font_manager.register_widget(model_label)
        model_layout.addWidget(model_label)

        self.model_edit = QLineEdit()
        self.model_edit.setStyleSheet("background-color: rgba(255, 255, 255, 200); border: 1px solid #cccccc; border-radius: 5px; padding: 8px;")
        if self.font_manager:
            self.font_manager.register_widget(self.model_edit)
        model_layout.addWidget(self.model_edit)

        # 添加常用模型提示
        model_hint = QLabel("常用模型: glm-4-flash-250414, glm-4, glm-3-turbo, chatglm2-6b, chatglm3-6b")
        model_hint.setStyleSheet("color: #666666; font-size: 12px;")
        if self.font_manager:
            self.font_manager.register_widget(model_hint)
        model_layout.addWidget(model_hint)

        # 加载当前模型
        self.load_model()

        save_model_button = QPushButton("保存模型选择")
        save_model_button.setStyleSheet("padding: 8px; background-color: rgba(240, 240, 240, 200);")
        save_model_button.clicked.connect(self.save_model)
        if self.font_manager:
            self.font_manager.register_widget(save_model_button)
        model_layout.addWidget(save_model_button)

        scroll_layout.addWidget(model_group)

        # 分隔线
        line5 = QFrame()
        line5.setFrameShape(QFrame.Shape.HLine)
        line5.setFrameShadow(QFrame.Shadow.Sunken)
        line5.setStyleSheet("margin: 15px 0; background-color: rgba(255, 255, 255, 100);")  # 半透明分隔线
        scroll_layout.addWidget(line5)

        self.select_font_ = QPushButton("选择字体")
        self.select_font_.setStyleSheet("padding: 8px; background-color: rgba(240, 240, 240, 200);")  # 半透明按钮
        self.select_font_.clicked.connect(self.select_font)
        if self.font_manager:
            self.font_manager.register_widget(self.select_font_)
        scroll_layout.addWidget(self.select_font_)

        # 添加一些额外内容以展示滚动效果
        # for i in range(1, 4):
        #     extra_label = QLabel(f"<b style='color: black;'>额外设置选项 {i}</b>")
        #     extra_spin = QSpinBox()
        #     extra_spin.setRange(0, 100)
        #     extra_spin.setValue(50)
        #     extra_spin.setStyleSheet("background-color: rgba(255, 255, 255, 200);")
            
        #     if self.font_manager:
        #         self.font_manager.register_widget(extra_label)
        #         self.font_manager.register_widget(extra_spin)
                
        #     scroll_layout.addWidget(extra_label)
        #     scroll_layout.addWidget(extra_spin)
            
        #     # 添加分隔线
        #     extra_line = QFrame()
        #     extra_line.setFrameShape(QFrame.Shape.HLine)
        #     extra_line.setFrameShadow(QFrame.Shadow.Sunken)
        #     extra_line.setStyleSheet("margin: 10px 0; background-color: rgba(255, 255, 255, 80);")
        #     scroll_layout.addWidget(extra_line)

        # 保持底部留白
        scroll_layout.addStretch()
        
        # 设置滚动内容
        scroll_area.setWidget(scroll_content)
        
        # 将滚动区域添加到主布局
        main_layout.addWidget(scroll_area)

    def init_tab3_ui(self):
        """初始化帮助和关于标签页"""
        layout = QVBoxLayout(self.tab3)
        
        # 创建并注册标签
        help_label = QLabel("<h1 style='color: black;'>帮助与关于</h1>")
        content_label = QLabel("""
            <p style='color: black;'><b>版本信息：</b> v1.0.0</p>
            <p style='color: black;'><b>开发者：</b> CJZ-WR</p>
            <p style='color: black;'><b>如有问题请提issues：</b> https://github.com/cjz-wr/DesktopPetByAi/issues</p>
            <p style='color: black;'><b>使用说明：</b></p>
            <ul style='color: black;'>
                <li>在设置页面可以配置背景图片</li>
                <li>调整透明度使图片更符合您的需求</li>
                <li>调整亮度优化显示效果</li>
                <li>现在支持实时预览效果</li>
                <li>设置页面已添加滚动功能</li>
                <li>主界面新增AI聊天功能</li>
            </ul>
        """)
        
        if self.font_manager:
            self.font_manager.register_widget(help_label)
            self.font_manager.register_widget(content_label)
            
        layout.addWidget(help_label)
        layout.addWidget(content_label)
        layout.addStretch()
    
    def select_font(self):
        # 使用字体管理器的当前字体初始化对话框
        current_font = self.font_manager.font if self.font_manager else QFont()
        font_dialog = QFontDialog(current_font, self)
        
        # 设置对话框样式
        font_dialog.setStyleSheet("""
            QDialog {
                background-color: #e6f2ff; /* 淡蓝色背景 */
            }
            QLabel {
                background-color: #e6f2ff;
                color: black;
            }
            QPushButton {
                background-color: #d4edff;
                border: 1px solid #a0d2eb;
            }
        """)

        # 显示字体对话框
        if font_dialog.exec() == QFontDialog.DialogCode.Accepted:
            selected_font = font_dialog.selectedFont()
            
            # 通过字体管理器更改字体
            if self.font_manager:
                self.font_manager.change_font(selected_font)
                
                # 保存字体设置
                self.data_setting["font"] = self.font_manager.to_dict()
                with open("demo_setting.json", "w", encoding="utf-8") as f:
                    json.dump(self.data_setting, f, indent=4, ensure_ascii=False)
    
    # 新增：整数变化时保存到配置
    def on_value_changed_int(self, value):
        self.int_label.setText(f"<span style='color: black;'>亮度值当前值(0~255)：{value}</span>")
        self.data_setting["luminance_img"] = value
        with open("demo_setting.json", "w", encoding="utf-8") as f:
            json.dump(self.data_setting, f, indent=4, ensure_ascii=False)
        # 发出亮度变化信号
        self.luminance_changed.emit(value)

    def on_value_changed_img(self, value):
        self.spin_label.setText(f"<span style='color: black;'>图片透明度当前值(0.0~1.0)：{value:.1f}</span>")
        self.transparency_img(value)
        # 发出透明度变化信号
        self.transparency_changed.emit(value)

    def show_file_dialog(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, '选择文件', '.', "图片 (*.jpg *.png *.jpeg);;所有文件 (*)"
        )
        if fname:
            self.img_label.setText(fname)
            self.data_setting["background_path"] = fname
            with open("demo_setting.json", "w", encoding="utf-8") as f:
                json.dump(self.data_setting, f, indent=4, ensure_ascii=False)
            # 发出背景图片变化信号
            self.background_changed.emit(fname)
        else:
            self.img_label.setText("未选择任何文件")

    def get_background_path(self):
        return self.data_setting.get("background_path")
    
    def transparency_img(self, value):
        self.data_setting["transparency_img"] = value
        with open("demo_setting.json", "w", encoding="utf-8") as f:
            json.dump(self.data_setting, f, indent=4, ensure_ascii=False)
    
    def get_transparency_img_value(self):
        try:
            # 注意：这里原代码尝试转换为int，应该是float
            return float(self.data_setting.get("transparency_img", 0.5))
        except (TypeError, ValueError):
            return 0.5
    
    def luminance_img(self, value):
        self.data_setting["luminance_img"] = value
        with open("demo_setting.json", "w", encoding="utf-8") as f:
            json.dump(self.data_setting, f, indent=4, ensure_ascii=False)
    
    def load_ai_key(self):
        """从配置文件中加载当前AI Key"""
        try:
            # 从data_setting中获取AI Key
            ai_key = self.data_setting.get("ai_key", "")
            if ai_key:
                self.ai_key_edit.setText(ai_key)
            else:
                self.ai_key_edit.setPlaceholderText("未找到API Key，请输入...")
        except Exception as e:
            QMessageBox.warning(self, "加载失败", f"无法加载AI Key: {str(e)}")
            self.ai_key_edit.setPlaceholderText("加载失败，请输入...")

    def save_ai_key(self):
        """保存新的AI Key到配置文件"""
        new_api_key = self.ai_key_edit.toPlainText().strip()
        if not new_api_key:
            QMessageBox.warning(self, "输入错误", "AI Key不能为空！")
            return

        try:
            # 更新data_setting中的AI Key
            self.data_setting["ai_key"] = new_api_key
            # 保存到配置文件
            with open("demo_setting.json", "w", encoding="utf-8") as f:
                json.dump(self.data_setting, f, indent=4, ensure_ascii=False)

            QMessageBox.information(self, "保存成功", "AI Key已成功更新！\n请注意：修改AI Key后需要重启程序才能生效。")
        except Exception as e:
            QMessageBox.warning(self, "保存失败", f"无法保存AI Key: {str(e)}")

    def load_model(self):
        """从配置文件中加载当前模型"""
        try:
            # 从data_setting中获取模型名称
            model_name = self.data_setting.get("model", "")
            if model_name:
                self.model_edit.setText(model_name)
            else:
                # 如果配置文件中没有，使用默认模型
                default_model = "glm-4-flash-250414"
                self.model_edit.setText(default_model)
                # 同时保存到配置文件
                self.data_setting["model"] = default_model
                with open("demo_setting.json", "w", encoding="utf-8") as f:
                    json.dump(self.data_setting, f, indent=4, ensure_ascii=False)
        except Exception as e:
            QMessageBox.warning(self, "加载失败", f"无法加载模型: {str(e)}")

    def save_model(self):
        """保存新的模型到配置文件"""
        new_model = self.model_edit.text().strip()
        if not new_model:
            QMessageBox.warning(self, "输入错误", "模型不能为空！")
            return

        try:
            # 更新data_setting中的模型
            self.data_setting["model"] = new_model
            # 保存到配置文件
            with open("demo_setting.json", "w", encoding="utf-8") as f:
                json.dump(self.data_setting, f, indent=4, ensure_ascii=False)

            QMessageBox.information(self, "保存成功", "模型已成功更新！\n请注意：修改模型后需要重启程序才能生效。")
        except Exception as e:
            QMessageBox.warning(self, "保存失败", f"无法保存模型: {str(e)}")

    def get_luminance_img_value(self):
        try:
            return int(self.data_setting.get("luminance_img", 128))
        except (TypeError, ValueError):
            return 128 

class CustomDialog(QDialog):
    def __init__(self, font_manager=None):
        super().__init__()

        self.font_manager = font_manager
        self.window_t = False  # 定义窗口是否是最大化
        self.border_radius = 15  # 圆角半径
        self.transparency_img_value = 0.5  # 透明度值
        self.luminance_img_value = 128  # 亮度值

        # 加载背景图片
        self.background_path = None
        self.background_pixmap = QPixmap(800, 600)
        self.background_pixmap.fill(QColor("white"))  # 默认白色背景
        
        # 创建VerticalTabWidget用于获取初始设置
        self.tab_widget = VerticalTabWidget(font_manager=font_manager)
        
        # 从设置中获取初始值
        self.transparency_img_value = self.tab_widget.get_transparency_img_value()
        self.luminance_img_value = self.tab_widget.get_luminance_img_value()
        self.background_path = self.tab_widget.get_background_path()
        
        # 如果有背景路径，加载图片
        if self.background_path:
            self.background_pixmap = self.load_and_process_image(self.background_path)
        
        # 初始化UI
        self.initUI()

        # 去掉系统标题栏
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        # 启用透明背景
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 设置窗口样式
        self.setStyleSheet("""
            QDialog {
                border-style: none;
                background: transparent;
            }
            QWidget#content {
                background: transparent;
                border-radius: 15px;
            }
        """)
        self.setMinimumSize(200, 200)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 内容容器（用于实现圆角效果）
        self.content_widget = QWidget()
        self.content_widget.setObjectName("content")
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 自定义标题栏
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(30)
        self.title_bar.setStyleSheet("""
            background-color: rgba(51, 51, 51, 230); 
            color: white; 
            border-top-left-radius: 15px;
            border-top-right-radius: 15px;
        """)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 5, 0)

        self.title_label = QLabel("更多")
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")  # 白色文字
        
        # 注册标题标签到字体管理器
        if self.font_manager:
            self.font_manager.register_widget(self.title_label)
            
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()

        # 图标路径（请根据实际情况修改）
        # 注意：这些图标文件需要存在，否则会显示空白
        # 这里使用内置图标代替
        icon_minimize = self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarMinButton)
        icon_maximize = self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarMaxButton)
        icon_restore = self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarNormalButton)
        icon_close = self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarCloseButton)

        # 最小化按钮
        self.minimize_button = QPushButton()
        self.minimize_button.setIcon(icon_minimize)
        self.minimize_button.setIconSize(QSize(16, 16))
        self.minimize_button.setFixedSize(25, 25)
        self.minimize_button.clicked.connect(self.showMinimized)

        # 最大化 / 还原 按钮
        self.maximize_button = QPushButton()
        self.maximize_button.setIcon(icon_maximize)
        self.maximize_button.setIconSize(QSize(16, 16))
        self.maximize_button.setFixedSize(25, 25)
        self.maximize_button.clicked.connect(self.toggle_maximize)

        # 关闭按钮
        self.close_button = QPushButton()
        self.close_button.setIcon(icon_close)
        self.close_button.setIconSize(QSize(16, 16))
        self.close_button.setFixedSize(25, 25)
        self.close_button.setStyleSheet("""
        QPushButton {
            border: none;
            background-color: transparent;
        }
        QPushButton:hover {
            background-color: red;
            border-radius: 4px;
        }
        QPushButton:pressed {
            background-color: #9e0a05;
        }
        """)
        self.close_button.clicked.connect(self.reject)

        # 按钮样式
        btn_style = """
        QPushButton {
            border: none;
            background-color: transparent;
        }
        QPushButton:hover {
            background-color: rgba(255, 255, 255, 30);
            border-radius: 4px;
        }
        QPushButton:pressed {
            background-color: rgba(255, 255, 255, 80);
        }
        """
        self.minimize_button.setStyleSheet(btn_style)
        self.maximize_button.setStyleSheet(btn_style)

        # 添加按钮到布局
        title_layout.addWidget(self.minimize_button)
        title_layout.addWidget(self.maximize_button)
        title_layout.addWidget(self.close_button)

        content_layout.addWidget(self.title_bar)

        # 添加标签页小部件
        content_layout.addWidget(self.tab_widget)
        
        main_layout.addWidget(self.content_widget)

        # 连接设置变化的信号
        self.tab_widget.transparency_changed.connect(self.handle_transparency_changed)
        self.tab_widget.luminance_changed.connect(self.handle_luminance_changed)
        self.tab_widget.background_changed.connect(self.handle_background_changed)

        # 拖动窗口相关
        self.dragging = False
        self.offset = QPoint()
        self.drag_from_maximized = False  # 新增：从最大化状态开始拖动的标志

        # 调整窗口大小相关
        self.resizing = False
        self.resize_area = 10
        self.min_size = QSize(100, 100)
        self.resize_edge = None  # 记录当前调整大小的边缘
        self.original_geometry = None  # 记录调整前的窗口位置和大小
        self.global_drag_start_pos = None  # 记录调整大小时的起始全局位置

        # 窗口状态
        self.is_maximized = False

    def on_setting_closed(self):
        """设置窗口关闭后的清理"""
        self.setting_dialog = None

    def initUI(self):
        self.setGeometry(300, 300, 800, 600)
        self.setWindowTitle('背景图片设置 - 实时预览')

    def load_and_process_image(self, path):
        """ 加载并处理图像透明度 """
        image = QImage(path)
        if image.isNull():
            print("无法加载图片")
            return QPixmap()
        
        # 调整图片大小以匹配窗口尺寸
        scaled_image = image.scaled(self.size(), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)

        # 创建带透明度的新图像
        transparent_image = QImage(scaled_image.size(), QImage.Format.Format_ARGB32)
        transparent_image.fill(Qt.GlobalColor.transparent)

        painter = QPainter(transparent_image)
        painter.setOpacity(self.transparency_img_value)  # 设置整体透明度 (0.0 ~ 1.0)
        painter.drawImage(0, 0, scaled_image)
        painter.end()

        return QPixmap.fromImage(transparent_image)

    def paintEvent(self, event):
        # 创建圆角路径
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), self.border_radius, self.border_radius)
        
        # 创建绘画器
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制背景图片
        if not self.background_pixmap.isNull():
            # 设置裁剪区域为圆角矩形
            painter.setClipPath(path)
            # 绘制背景图片
            painter.drawPixmap(self.rect(), self.background_pixmap)
            # 重置裁剪区域
            painter.setClipping(False)
        
        # 绘制半透明覆盖层
        overlay_color = QColor(0, 0, 0, self.luminance_img_value)
        painter.setBrush(overlay_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path)

        # 确保文字区域也被背景覆盖
        super().paintEvent(event)

    # 处理透明度变化
    def handle_transparency_changed(self, value):
        self.transparency_img_value = value
        # 重新加载并处理图片
        if self.background_path:
            self.background_pixmap = self.load_and_process_image(self.background_path)
        self.update()  # 触发重绘

    # 处理亮度变化
    def handle_luminance_changed(self, value):
        self.luminance_img_value = value
        self.update()  # 触发重绘

    # 处理背景图片变化
    def handle_background_changed(self, path):
        self.background_path = path
        if path:
            self.background_pixmap = self.load_and_process_image(path)
        else:
            # 如果没有选择图片，则使用默认的白色背景
            self.background_pixmap = QPixmap(self.size())
            self.background_pixmap.fill(Qt.GlobalColor.white)
        self.update()  # 触发重绘

    # 切换最大化/还原
    def toggle_maximize(self):
        if self.is_maximized:
            self.showNormal()
            self.maximize_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarMaxButton))  # 使用还原图标
        else:
            self.showMaximized()
            self.maximize_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarNormalButton))  # 使用最大化图标
        self.is_maximized = not self.is_maximized

    # 鼠标双击事件（双击标题栏最大化/还原）
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if (event.button() == Qt.MouseButton.LeftButton and 
            self.title_bar.underMouse()):
            # 调用 toggle 方法确保状态同步更新
            self.toggle_maximize()
            event.accept()  # 标记事件已处理
            return
        super().mouseDoubleClickEvent(event)

    # 鼠标按下事件
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            global_pos = event.globalPosition().toPoint()  # 获取全局位置
            
            # 检测是否在调整大小的区域
            self.resize_edge = self.get_resize_edge(pos)
            if self.resize_edge:
                self.resizing = True
                self.original_geometry = self.geometry()  # 保存原始位置和大小
                self.global_drag_start_pos = global_pos   # 记录鼠标按下的全局位置
                self.setCursorShape(self.resize_edge)
                # 移除 return 语句，让事件继续处理
            
            # 检查标题栏区域用于拖动
            if self.title_bar.underMouse():
                if self.is_maximized:
                    # 设置标志表示从最大化状态开始拖动
                    self.drag_from_maximized = True
                    # 保存鼠标在屏幕上的全局位置
                    self.global_drag_start_pos = global_pos
                else:
                    # 只有不在调整区域时才允许拖动
                    if not self.resize_edge:
                        self.dragging = True
                        self.offset = pos  # 保存鼠标位置偏移量

    # 获取调整大小的边缘
    def get_resize_edge(self, pos):
        rect = self.rect()
        resize_area = self.resize_area
        
        # 左上角
        if (pos.x() <= resize_area and pos.y() <= resize_area):
            return 'top-left'
        # 右上角
        elif (pos.x() >= rect.width() - resize_area and pos.y() <= resize_area):
            return 'top-right'
        # 左下角
        elif (pos.x() <= resize_area and pos.y() >= rect.height() - resize_area):
            return 'bottom-left'
        # 右下角
        elif (pos.x() >= rect.width() - resize_area and pos.y() >= rect.height() - resize_area):
            return 'bottom-right'
        # 上边缘
        elif (pos.y() <= resize_area):
            return 'top'
        # 下边缘
        elif (pos.y() >= rect.height() - resize_area):
            return 'bottom'
        # 左边缘
        elif (pos.x() <= resize_area):
            return 'left'
        # 右边缘
        elif (pos.x() >= rect.width() - resize_area):
            return 'right'
        else:
            return None

    # 鼠标移动事件
    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.position().toPoint()
        global_pos = event.globalPosition().toPoint()
        
        # 处理从最大化状态开始的拖动
        if hasattr(self, 'drag_from_maximized') and self.drag_from_maximized:
            # 先还原窗口
            self.toggle_maximize()
            
            # 计算合适的偏移量（使鼠标位于标题栏中央）
            title_height = self.title_bar.height()
            # 计算窗口的新位置：鼠标位置减去窗口宽度/2和标题栏高度/2
            new_x = global_pos.x() - self.width() // 2
            new_y = global_pos.y() - title_height // 2
            
            # 确保新位置在屏幕范围内
            screen_rect = QApplication.primaryScreen().availableGeometry()
            new_x = max(screen_rect.left(), new_x)
            new_y = max(screen_rect.top(), new_y)
            new_x = min(screen_rect.right() - self.width(), new_x)
            new_y = min(screen_rect.bottom() - self.height(), new_y)
            
            # 移动窗口到新位置
            self.move(new_x, new_y)
            
            # 设置偏移量为标题栏中央
            self.offset = QPoint(self.width() // 2, title_height // 2)
            
            self.drag_from_maximized = False  # 清除标志
            self.dragging = True  # 开始正常拖动
        
        # 调整大小处理
        elif self.resizing and self.resize_edge and self.original_geometry and hasattr(self, 'global_drag_start_pos') and self.global_drag_start_pos:
            # 获取当前鼠标在屏幕上的位置
            current_global_pos = global_pos
            
            # 计算相对于起始位置的偏移量
            delta_x = current_global_pos.x() - self.global_drag_start_pos.x()
            delta_y = current_global_pos.y() - self.global_drag_start_pos.y()
            
            # 根据不同的边缘调整窗口大小
            new_geometry = QRect(self.original_geometry)  # 复制
            
            if 'top' in self.resize_edge:
                new_geometry.setTop(new_geometry.top() + delta_y)
            if 'bottom' in self.resize_edge:
                new_geometry.setBottom(new_geometry.bottom() + delta_y)
            if 'left' in self.resize_edge:
                new_geometry.setLeft(new_geometry.left() + delta_x)
            if 'right' in self.resize_edge:
                new_geometry.setRight(new_geometry.right() + delta_x)
            
            # 确保最小尺寸
            if new_geometry.width() < self.min_size.width():
                if 'left' in self.resize_edge:
                    new_geometry.setLeft(new_geometry.right() - self.min_size.width())
                elif 'right' in self.resize_edge:
                    new_geometry.setRight(new_geometry.left() + self.min_size.width())
            if new_geometry.height() < self.min_size.height():
                if 'top' in self.resize_edge:
                    new_geometry.setTop(new_geometry.bottom() - self.min_size.height())
                elif 'bottom' in self.resize_edge:
                    new_geometry.setBottom(new_geometry.top() + self.min_size.height())
            
            # 应用新的几何属性
            self.setGeometry(new_geometry)
        
        # 正常拖动处理
        elif self.dragging:
            # 计算新位置（考虑当前鼠标偏移）
            new_pos = self.pos() + (global_pos - self.mapToGlobal(self.offset))
            
            self.move(new_pos)
        
        # 更新光标形状（非最大化状态）
        elif not self.is_maximized:
            edge = self.get_resize_edge(pos)
            self.setCursorShape(edge)

    # 设置鼠标样式
    def setCursorShape(self, edge):
        if edge == 'top' or edge == 'bottom':
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        elif edge == 'left' or edge == 'right':
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif edge == 'top-left' or edge == 'bottom-right':
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif edge == 'top-right' or edge == 'bottom-left':
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    # 鼠标释放事件
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.resizing = False
            self.resize_edge = None
            self.original_geometry = None
            
            # 清除从最大化状态拖动的标志
            if hasattr(self, 'drag_from_maximized'):
                self.drag_from_maximized = False
            
            self.setCursor(Qt.CursorShape.ArrowCursor)  # 恢复默认光标

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("主窗口")
        self.resize(350, 300)
        
        # 创建全局字体管理器
        self.font_manager = FontManager()
        
        layout = QVBoxLayout(self)
        btn = QPushButton("打开自定义弹窗")
        btn.clicked.connect(self.show_custom_dialog)
        
        # 注册按钮到字体管理器
        self.font_manager.register_widget(btn)
        
        layout.addWidget(btn)
        
        # 添加说明标签
        info_label = QLabel("点击按钮打开设置窗口，在设置标签页中调整图片透明度和亮度可实时预览效果")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

    def show_custom_dialog(self):
        # 将字体管理器传递给对话框
        dialog = CustomDialog(font_manager=self.font_manager)
        dialog.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())