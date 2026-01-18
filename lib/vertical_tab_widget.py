import sys
import json, os
from PyQt6.QtWidgets import (QApplication, QStackedWidget, QDialog, QFontDialog, QStyle, QButtonGroup, 
                            QFrame, QVBoxLayout, QDoubleSpinBox, QSpinBox, QFileDialog, QTabBar, 
                            QHBoxLayout, QLabel, QPushButton, QWidget, QTabWidget, QScrollArea,
                            QTextEdit, QDialogButtonBox, QMessageBox, QSplitter, QMenu, QSystemTrayIcon, QComboBox, QLineEdit)
from PyQt6.QtCore import Qt, QPoint, QSize, QRectF, pyqtSignal, QObject, QRect, QThread
from PyQt6.QtGui import (QIcon, QMouseEvent, QPainter, QImage, QPixmap, QFontMetrics, QPen, QColor, 
                         QPainterPath, QFont, QTextCursor, QTextCharFormat, QMovie)

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
        from lib.chat_widget import ChatWidget
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

        # OpenAI API 设置区域
        openai_group = QWidget()
        openai_group.setStyleSheet("background-color: rgba(255, 255, 255, 150); border-radius: 5px; padding: 10px;")
        openai_layout = QVBoxLayout(openai_group)

        openai_label = QLabel("<b style='color: black;'>OpenAI API 设置</b>")
        if self.font_manager:
            self.font_manager.register_widget(openai_label)
        openai_layout.addWidget(openai_label)

        # OpenAI API Key
        openai_key_label = QLabel("OpenAI API Key:")
        if self.font_manager:
            self.font_manager.register_widget(openai_key_label)
        openai_layout.addWidget(openai_key_label)

        self.openai_key_edit = QTextEdit()
        self.openai_key_edit.setPlaceholderText("请输入OpenAI API Key...")
        self.openai_key_edit.setMaximumHeight(60)
        self.openai_key_edit.setStyleSheet("background-color: rgba(255, 255, 255, 200); border: 1px solid #cccccc; border-radius: 5px; padding: 8px;")
        if self.font_manager:
            self.font_manager.register_widget(self.openai_key_edit)
        openai_layout.addWidget(self.openai_key_edit)

        # OpenAI Base URL
        openai_base_label = QLabel("OpenAI Base URL:")
        if self.font_manager:
            self.font_manager.register_widget(openai_base_label)
        openai_layout.addWidget(openai_base_label)

        self.openai_base_edit = QLineEdit()
        self.openai_base_edit.setPlaceholderText("https://api.openai.com/v1")
        self.openai_base_edit.setStyleSheet("background-color: rgba(255, 255, 255, 200); border: 1px solid #cccccc; border-radius: 5px; padding: 8px;")
        if self.font_manager:
            self.font_manager.register_widget(self.openai_base_edit)
        openai_layout.addWidget(self.openai_base_edit)

        # OpenAI Model
        openai_model_label = QLabel("OpenAI Model:")
        if self.font_manager:
            self.font_manager.register_widget(openai_model_label)
        openai_layout.addWidget(openai_model_label)

        self.openai_model_edit = QLineEdit()
        self.openai_model_edit.setPlaceholderText("gpt-3.5-turbo")
        self.openai_model_edit.setStyleSheet("background-color: rgba(255, 255, 255, 200); border: 1px solid #cccccc; border-radius: 5px; padding: 8px;")
        if self.font_manager:
            self.font_manager.register_widget(self.openai_model_edit)
        openai_layout.addWidget(self.openai_model_edit)

        # 添加常用模型提示
        openai_hint = QLabel("常用模型: gpt-3.5-turbo, gpt-4, gpt-4o, gpt-4-turbo")
        openai_hint.setStyleSheet("color: #666666; font-size: 12px;")
        if self.font_manager:
            self.font_manager.register_widget(openai_hint)
        openai_layout.addWidget(openai_hint)

        # 加载当前OpenAI配置
        self.load_openai_config()

        save_openai_button = QPushButton("保存OpenAI配置")
        save_openai_button.setStyleSheet("padding: 8px; background-color: rgba(240, 240, 240, 200);")
        save_openai_button.clicked.connect(self.save_openai_config)
        if self.font_manager:
            self.font_manager.register_widget(save_openai_button)
        openai_layout.addWidget(save_openai_button)

        scroll_layout.addWidget(openai_group)

        # 分隔线
        line6 = QFrame()
        line6.setFrameShape(QFrame.Shape.HLine)
        line6.setFrameShadow(QFrame.Shadow.Sunken)
        line6.setStyleSheet("margin: 15px 0; background-color: rgba(255, 255, 255, 100);")  # 半透明分隔线
        scroll_layout.addWidget(line6)

        # API选择区域
        api_group = QWidget()
        api_group.setStyleSheet("background-color: rgba(255, 255, 255, 150); border-radius: 5px; padding: 10px;")
        api_layout = QVBoxLayout(api_group)

        api_label = QLabel("<b style='color: black;'>API 选择</b>")
        if self.font_manager:
            self.font_manager.register_widget(api_label)
        api_layout.addWidget(api_label)

        # 创建API选择下拉框
        self.api_selector = QComboBox()
        self.api_selector.addItems(["智谱AI (ZhipuAI)", "OpenAI"])
        self.api_selector.setStyleSheet("background-color: rgba(255, 255, 255, 200); border: 1px solid #cccccc; border-radius: 5px; padding: 8px;")
        if self.font_manager:
            self.font_manager.register_widget(self.api_selector)
        api_layout.addWidget(self.api_selector)

        # 加载当前API选择
        self.load_api_selection()

        save_api_button = QPushButton("保存API选择")
        save_api_button.setStyleSheet("padding: 8px; background-color: rgba(240, 240, 240, 200);")
        save_api_button.clicked.connect(self.save_api_selection)
        if self.font_manager:
            self.font_manager.register_widget(save_api_button)
        api_layout.addWidget(save_api_button)

        scroll_layout.addWidget(api_group)

        # 分隔线
        line7 = QFrame()
        line7.setFrameShape(QFrame.Shape.HLine)
        line7.setFrameShadow(QFrame.Shadow.Sunken)
        line7.setStyleSheet("margin: 15px 0; background-color: rgba(255, 255, 255, 100);")  # 半透明分隔线
        scroll_layout.addWidget(line7)

        # 创建并注册选择字体按钮
        self.select_font_ = QPushButton("选择字体")
        self.select_font_.setStyleSheet("padding: 8px; background-color: rgba(240, 240, 240, 200);")  # 半透明按钮
        self.select_font_.clicked.connect(self.select_font)
        if self.font_manager:
            self.font_manager.register_widget(self.select_font_)
        scroll_layout.addWidget(self.select_font_)

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
            <p style='color: black;'><b>版本信息：</b> v2.1.5</p>
            <p style='color: black;'><b>开发者：</b> CJZ-WR</p>
            <p style='color: black;'><b>如有问题请提issues：</b> https://github.com/cjz-wr/DesktopPetByAi/issues</p>
            <p style='color: black;'><b>使用说明：</b></p>
            <ul style='color: black;'>
                <li>在设置页面可以配置背景图片</li>
                <li>调整透明度使图片更符合您的需求</li>
                <li>调整亮度优化显示效果</li>
                <li>需要自行配置API密钥</li>
            </ul>
            <p style='color: red; font-size: 20px;'><b>注意：</b></p>
            <ul style='color: black;'>
                <li>本项目仅供学习和研究使用，请勿用于商业用途。</li>
                <li>请遵守相关法律法规，尊重知识产权。</li>
                <li>请勿用于非法用途。如涉及侵犯他人权益的行为,与开发者无关。</li>
            </ul>
            <p style='color: black;'><b>更新说明：</b></p>
            <ul style='color: black;'>
                <li>添加openai api支持</li>
                <li>可以调用本地模型（需自行部署）</li>
                <li>修复一些bug</li>
                <li>我要让她更像人,啊啊啊啊</li>
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

    def load_openai_config(self):
        """从配置文件中加载当前OpenAI配置"""
        try:
            # 从data_setting中获取OpenAI配置
            openai_key = self.data_setting.get("openai_key", "")
            openai_base_url = self.data_setting.get("openai_base_url", "https://api.openai.com/v1")
            openai_model = self.data_setting.get("openai_model", "gpt-3.5-turbo")
            
            self.openai_key_edit.setPlainText(openai_key)
            self.openai_base_edit.setText(openai_base_url)
            self.openai_model_edit.setText(openai_model)
        except Exception as e:
            QMessageBox.warning(self, "加载失败", f"无法加载OpenAI配置: {str(e)}")

    def save_openai_config(self):
        """保存新的OpenAI配置到配置文件"""
        openai_key = self.openai_key_edit.toPlainText().strip()
        openai_base_url = self.openai_base_edit.text().strip()
        openai_model = self.openai_model_edit.text().strip()
        
        if not openai_key:
            QMessageBox.warning(self, "输入错误", "OpenAI API Key不能为空！")
            return
        
        if not openai_base_url:
            openai_base_url = "https://api.openai.com/v1"
        
        if not openai_model:
            openai_model = "gpt-3.5-turbo"

        try:
            # 更新data_setting中的OpenAI配置
            self.data_setting["openai_key"] = openai_key
            self.data_setting["openai_base_url"] = openai_base_url
            self.data_setting["openai_model"] = openai_model
            
            # 保存到配置文件
            with open("demo_setting.json", "w", encoding="utf-8") as f:
                json.dump(self.data_setting, f, indent=4, ensure_ascii=False)

            QMessageBox.information(self, "保存成功", "OpenAI配置已成功更新！\n请注意：修改配置后需要重启程序才能生效。")
        except Exception as e:
            QMessageBox.warning(self, "保存失败", f"无法保存OpenAI配置: {str(e)}")

    def load_api_selection(self):
        """从配置文件中加载当前API选择"""
        try:
            # 从data_setting中获取API选择
            api_provider = self.data_setting.get("api_provider", "zhipu")
            if api_provider == "openai":
                self.api_selector.setCurrentIndex(1)
            else:
                # 默认选择智谱AI
                self.api_selector.setCurrentIndex(0)
        except Exception as e:
            print(f"加载API选择失败: {str(e)}")

    def save_api_selection(self):
        """保存新的API选择到配置文件"""
        current_index = self.api_selector.currentIndex()
        api_provider = "openai" if current_index == 1 else "zhipu"
        
        try:
            # 更新data_setting中的API选择
            self.data_setting["api_provider"] = api_provider
            # 保存到配置文件
            with open("demo_setting.json", "w", encoding="utf-8") as f:
                json.dump(self.data_setting, f, indent=4, ensure_ascii=False)

            QMessageBox.information(self, "保存成功", "API选择已成功更新！\n请注意：修改API后需要重启程序才能生效。")
        except Exception as e:
            QMessageBox.warning(self, "保存失败", f"无法保存API选择: {str(e)}")

    def get_luminance_img_value(self):
        try:
            return int(self.data_setting.get("luminance_img", 128))
        except (TypeError, ValueError):
            return 128