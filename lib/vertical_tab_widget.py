'''
lib.vertical_tab_widget 的 Docstring
描述：
该模块实现了一个自定义的垂直标签页组件 VerticalTabWidget，包含三个主要标签页：聊天、设置和帮助&关于。左侧为垂直排列的按钮，右侧为对应的堆叠页面。用户可以通过按钮切换不同的标签页。设置页面支持背景图片选择、透明度和亮度调整等功能，并保存用户配置。该组件还集成了字体管理器以支持动态字体更改。
'''

import sys
import json, os
from PyQt6.QtWidgets import (QApplication, QStackedWidget, QDialog, QFontDialog, QStyle, QButtonGroup, 
                            QFrame, QVBoxLayout, QDoubleSpinBox, QSpinBox, QFileDialog, QTabBar, 
                            QHBoxLayout, QLabel, QPushButton, QWidget, QTabWidget, QScrollArea,
                            QTextEdit, QDialogButtonBox, QMessageBox, QSplitter, QMenu, QSystemTrayIcon, QComboBox, QLineEdit)
from PyQt6.QtCore import Qt, QPoint, QSize, QRectF, pyqtSignal, QObject, QRect, QThread, QPropertyAnimation, QEasingCurve
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
        
        # 创建四个页面
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
            btn.setObjectName(f"tab_button_{i}")
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
        
        # 应用美化主题和动画效果
        self.apply_beautiful_theme()

    def apply_beautiful_theme(self):
        """应用美化主题和动画效果"""
        from lib.theme_manager import ThemeManager, WidgetEnhancer, AnimationManager
        
        # 应用绿色主题
        theme_manager = ThemeManager()
        theme_manager.apply_theme(self, 'green')
        
        # 增强标签按钮效果
        for i, button in enumerate(self.tab_buttons):
            WidgetEnhancer.enhance_button(button, 'tab')
            
            # 为每个按钮添加淡入动画
            fade_anim = AnimationManager.create_fade_animation(button, duration=300)
            fade_anim.setStartValue(0.0)
            fade_anim.setEndValue(1.0)
            fade_anim.start()
        
        # 为堆叠页面添加切换动画
        self.stacked_widget.currentChanged.connect(self.on_page_changed)
    
    def on_page_changed(self, index):
        """页面切换时的动画效果"""
        from lib.theme_manager import AnimationManager
        current_widget = self.stacked_widget.widget(index)
        
        # 淡入效果
        fade_anim = AnimationManager.create_fade_animation(current_widget, duration=200)
        fade_anim.setStartValue(0.0)
        fade_anim.setEndValue(1.0)
        fade_anim.start()
        
        # 轻微的缩放效果
        scale_anim = QPropertyAnimation(current_widget, b"geometry")
        scale_anim.setDuration(200)
        scale_anim.setEasingCurve(QEasingCurve.Type.OutBack)
        original_geom = current_widget.geometry()
        scale_anim.setStartValue(original_geom.adjusted(10, 10, -10, -10))
        scale_anim.setEndValue(original_geom)
        scale_anim.start()
    
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
        """初始化设置标签页 - 应用美化主题"""
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
        
        # 应用主题管理器
        from lib.theme_manager import ThemeManager, WidgetEnhancer
        theme_manager = ThemeManager()
        theme_manager.apply_theme(self, 'green')
        
        # 背景设置区域 - 美化为卡片样式
        img_group = QWidget()
        img_group.setObjectName("background-setting-card")
        img_layout = QVBoxLayout(img_group)
        img_layout.setSpacing(12)
        
        # 背景设置标题
        bg_title = QLabel("🖼️ 背景图片设置")
        bg_title.setObjectName("card-title")
        if self.font_manager:
            self.font_manager.register_widget(bg_title)
        img_layout.addWidget(bg_title)
        
        # 文件选择按钮
        select_button = QPushButton("📁 选择背景图片")
        select_button.setObjectName("select-image-button")
        select_button.clicked.connect(self.show_file_dialog)
        if self.font_manager:
            self.font_manager.register_widget(select_button)
        
        # 增强按钮效果
        WidgetEnhancer.enhance_button(select_button, 'primary')
        
        img_layout.addWidget(select_button)
        
        # 当前选择显示
        self.img_label = QLabel("未选择任何文件")
        self.img_label.setWordWrap(True)
        self.img_label.setStyleSheet("""
            QLabel {
                color: #2F4F2F;
                background-color: #F8FFF8;
                padding: 10px;
                border-radius: 6px;
                border: 1px solid #B2F2BB;
            }
        """)
        if self.font_manager:
            self.font_manager.register_widget(self.img_label)
        
        if "background_path" in self.data_setting and self.data_setting["background_path"]:
            self.img_label.setText(self.data_setting["background_path"])
        
        img_layout.addWidget(self.img_label)
        
        scroll_layout.addWidget(img_group)
        
        # 透明度设置卡片
        transparency_group = QWidget()
        transparency_group.setObjectName("setting-card")
        trans_layout = QVBoxLayout(transparency_group)
        trans_layout.setSpacing(12)
        
        # 透明度标题
        trans_title = QLabel("🔍 图片透明度调节")
        trans_title.setObjectName("card-title")
        if self.font_manager:
            self.font_manager.register_widget(trans_title)
        trans_layout.addWidget(trans_title)
        
        # 透明度说明
        trans_desc = QLabel("调节宠物的透明度，数值越小越透明 (0.0-1.0)")
        trans_desc.setObjectName("info-label")
        trans_desc.setWordWrap(True)
        if self.font_manager:
            self.font_manager.register_widget(trans_desc)
        trans_layout.addWidget(trans_desc)
        
        # 当前值显示
        self.spin_label = QLabel(f"当前透明度值：<b>{self.get_transparency_img_value():.1f}</b>")
        self.spin_label.setObjectName("value-display")
        if self.font_manager:
            self.font_manager.register_widget(self.spin_label)
        trans_layout.addWidget(self.spin_label)
        
        # 透明度调节滑块
        self.double_spin = QDoubleSpinBox()
        self.double_spin.setObjectName("transparency-slider")
        self.double_spin.setRange(0.0, 1.0)
        self.double_spin.setSingleStep(0.1)
        self.double_spin.setDecimals(1)
        self.double_spin.setValue(self.get_transparency_img_value())
        self.double_spin.valueChanged.connect(self.on_value_changed_img)
        if self.font_manager:
            self.font_manager.register_widget(self.double_spin)
        trans_layout.addWidget(self.double_spin)
        
        scroll_layout.addWidget(transparency_group)
        
        # 亮度设置卡片
        brightness_group = QWidget()
        brightness_group.setObjectName("setting-card")
        bright_layout = QVBoxLayout(brightness_group)
        bright_layout.setSpacing(12)
        
        # 亮度标题
        bright_title = QLabel("💡 图片亮度调节")
        bright_title.setObjectName("card-title")
        if self.font_manager:
            self.font_manager.register_widget(bright_title)
        bright_layout.addWidget(bright_title)
        
        # 亮度说明
        bright_desc = QLabel("调节宠物显示亮度，数值越大越明亮 (0-255)")
        bright_desc.setObjectName("info-label")
        bright_desc.setWordWrap(True)
        if self.font_manager:
            self.font_manager.register_widget(bright_desc)
        bright_layout.addWidget(bright_desc)
        
        # 当前值显示
        self.int_label = QLabel(f"当前亮度值：<b>{self.get_luminance_img_value()}</b>")
        self.int_label.setObjectName("value-display")
        if self.font_manager:
            self.font_manager.register_widget(self.int_label)
        bright_layout.addWidget(self.int_label)
        
        # 亮度调节滑块
        self.int_spin = QSpinBox()
        self.int_spin.setObjectName("brightness-slider")
        self.int_spin.setRange(0, 255)
        self.int_spin.setSingleStep(5)
        self.int_spin.setValue(self.get_luminance_img_value())
        self.int_spin.valueChanged.connect(self.on_value_changed_int)
        if self.font_manager:
            self.font_manager.register_widget(self.int_spin)
        bright_layout.addWidget(self.int_spin)
        
        scroll_layout.addWidget(brightness_group)
        
        # 分隔线
        line3 = QFrame()
        line3.setFrameShape(QFrame.Shape.HLine)
        line3.setFrameShadow(QFrame.Shadow.Sunken)
        line3.setStyleSheet("margin: 15px 0; background-color: rgba(255, 255, 255, 100);")  # 半透明分隔线
        scroll_layout.addWidget(line3)
        
        # 个性化设置卡片
        personal_group = QWidget()
        personal_group.setObjectName("personalization-card")
        personal_layout = QVBoxLayout(personal_group)
        personal_layout.setSpacing(12)
        
        # 个性化设置标题
        personal_title = QLabel("🎨 个性化设置")
        personal_title.setObjectName("card-title")
        if self.font_manager:
            self.font_manager.register_widget(personal_title)
        personal_layout.addWidget(personal_title)
        
        # API配置说明
        api_info = QLabel("🔧 当前使用OpenAI兼容接口")
        api_info.setObjectName("info-label")
        if self.font_manager:
            self.font_manager.register_widget(api_info)
        personal_layout.addWidget(api_info)
        
        # OpenAI接口配置
        openai_title = QLabel("🌐 OpenAI接口配置")
        openai_title.setObjectName("section-title")
        if self.font_manager:
            self.font_manager.register_widget(openai_title)
        personal_layout.addWidget(openai_title)
        
        # API密钥输入
        api_key_label = QLabel("🔑 API密钥:")
        api_key_label.setObjectName("setting-label")
        if self.font_manager:
            self.font_manager.register_widget(api_key_label)
        personal_layout.addWidget(api_key_label)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setObjectName("api-key-input")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("请输入OpenAI API密钥")
        if self.font_manager:
            self.font_manager.register_widget(self.api_key_input)
        personal_layout.addWidget(self.api_key_input)
        
        # Base URL输入
        base_url_label = QLabel("🔗 基础URL:")
        base_url_label.setObjectName("setting-label")
        if self.font_manager:
            self.font_manager.register_widget(base_url_label)
        personal_layout.addWidget(base_url_label)
        
        self.base_url_input = QLineEdit()
        self.base_url_input.setObjectName("base-url-input")
        self.base_url_input.setPlaceholderText("例如: https://api.openai.com/v1")
        if self.font_manager:
            self.font_manager.register_widget(self.base_url_input)
        personal_layout.addWidget(self.base_url_input)
        
        # 模型名称输入
        model_label = QLabel("🤖 模型名称:")
        model_label.setObjectName("setting-label")
        if self.font_manager:
            self.font_manager.register_widget(model_label)
        personal_layout.addWidget(model_label)
        
        self.model_input = QLineEdit()
        self.model_input.setObjectName("model-input")
        self.model_input.setPlaceholderText("请输入模型名称，例如: gpt-3.5-turbo")
        if self.font_manager:
            self.font_manager.register_widget(self.model_input)
        personal_layout.addWidget(self.model_input)
        
        # 加载当前配置
        self.load_openai_config()
        
        save_openai_button = QPushButton("💾 保存接口配置")
        save_openai_button.setObjectName("save-button")
        save_openai_button.clicked.connect(self.save_openai_config)
        if self.font_manager:
            self.font_manager.register_widget(save_openai_button)
        WidgetEnhancer.enhance_button(save_openai_button, 'primary')
        personal_layout.addWidget(save_openai_button)
        
        # GIF文件夹选择
        gif_title = QLabel("🎮 GIF动画选择")
        gif_title.setObjectName("section-title")
        if self.font_manager:
            self.font_manager.register_widget(gif_title)
        personal_layout.addWidget(gif_title)
        
        self.gif_folder_combo = QComboBox()
        self.gif_folder_combo.setObjectName("gif-folder-selector")
        if self.font_manager:
            self.font_manager.register_widget(self.gif_folder_combo)
        personal_layout.addWidget(self.gif_folder_combo)
        
        # 加载GIF文件夹选项
        self.load_gif_folders()
        
        save_gif_button = QPushButton("💾 保存GIF选择")
        save_gif_button.setObjectName("save-button")
        save_gif_button.clicked.connect(self.save_gif_folder_selection)
        if self.font_manager:
            self.font_manager.register_widget(save_gif_button)
        WidgetEnhancer.enhance_button(save_gif_button, 'secondary')
        personal_layout.addWidget(save_gif_button)
        
        # AI角色设定
        role_title = QLabel("🎭 AI角色设定")
        role_title.setObjectName("section-title")
        if self.font_manager:
            self.font_manager.register_widget(role_title)
        personal_layout.addWidget(role_title)
        
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setObjectName("role-setting-textarea")
        self.prompt_edit.setPlaceholderText("请输入您想要的AI角色个性描述...")
        self.prompt_edit.setMaximumHeight(100)
        if self.font_manager:
            self.font_manager.register_widget(self.prompt_edit)
        personal_layout.addWidget(self.prompt_edit)
        
        # 加载当前AI角色设定
        self.load_prompt()
        
        save_prompt_button = QPushButton("💾 保存角色设定")
        save_prompt_button.setObjectName("save-button")
        save_prompt_button.clicked.connect(self.save_prompt)
        if self.font_manager:
            self.font_manager.register_widget(save_prompt_button)
        WidgetEnhancer.enhance_button(save_prompt_button, 'secondary')
        personal_layout.addWidget(save_prompt_button)
        
        # 字体选择
        font_title = QLabel("🔤 字体设置")
        font_title.setObjectName("section-title")
        if self.font_manager:
            self.font_manager.register_widget(font_title)
        personal_layout.addWidget(font_title)
        
        self.select_font_ = QPushButton("🎨 选择字体")
        self.select_font_.setObjectName("font-select-button")
        self.select_font_.clicked.connect(self.select_font)
        if self.font_manager:
            self.font_manager.register_widget(self.select_font_)
        WidgetEnhancer.enhance_button(self.select_font_, 'accent')
        personal_layout.addWidget(self.select_font_)
        
        scroll_layout.addWidget(personal_group)
        
        # MCP配置卡片
        mcp_group = QWidget()
        mcp_group.setObjectName("mcp-config-card")
        mcp_layout = QVBoxLayout(mcp_group)
        mcp_layout.setSpacing(12)
        
        # MCP配置标题
        mcp_title = QLabel("🔌 MCP服务器配置")
        mcp_title.setObjectName("card-title")
        if self.font_manager:
            self.font_manager.register_widget(mcp_title)
        mcp_layout.addWidget(mcp_title)
        
        # 导入并添加MCP配置组件
        from lib.mcp_config_widget import MCPConfigWidget
        self.mcp_config_widget = MCPConfigWidget(font_manager=self.font_manager)
        self.mcp_config_widget.config_changed.connect(self.on_mcp_config_changed)
        mcp_layout.addWidget(self.mcp_config_widget)
        
        scroll_layout.addWidget(mcp_group)
        
        # 保持底部留白
        scroll_layout.addStretch()
        
        # 添加自定义样式
        self.add_custom_styles()
        
        # 设置滚动内容
        scroll_area.setWidget(scroll_content)
        
        # 将滚动区域添加到主布局
        main_layout.addWidget(scroll_area)

    def add_custom_styles(self):
        """添加自定义CSS样式 - 优化版本避免不支持的属性"""
        custom_styles = """
            /* 通用样式 */
            QLabel {
                color: #2F4F2F;
                font-size: 14px;
            }
            
            /* MCP配置相关样式 - 移除不支持的CSS3属性 */
            #mcp-config-card {
                background-color: #F8F8FF;
                border: 1px solid #E0E0E0;
                border-radius: 12px;
                padding: 20px;
                margin: 15px 10px;
            }
            
            #mcp-config-card QLabel {
                color: #191970;
                font-size: 14px;
            }
            
            #server-list {
                background-color: #FFFFFF;
                alternate-background-color: #F9F9FF;
                selection-background-color: #87CEEB;
                selection-color: #191970;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 8px;
                min-height: 120px;
            }
            #server-list::item {
                padding: 12px 16px;
                border-radius: 4px;
            }
            #server-list::item:selected {
                background-color: #87CEEB;
                color: #191970;
                font-weight: bold;
            }
            #server-list::item:hover {
                background-color: #F0F8FF;
            }
            
            /* 操作按钮样式 - 简化版本 */
            #add-server-button, #edit-server-button, #remove-server-button, #test-server-button {
                padding: 10px 20px;
                margin: 4px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }

            #add-server-button {
                background-color: #90EE90;
                border: 1px solid #2E8B57;
                color: white;
            }
            #add-server-button:hover {
                background-color: #77DD77;
                border: 1px solid #228B22;
            }

            #edit-server-button {
                background-color: #87CEEB;
                border: 1px solid #3A6D9C;
                color: white;
            }
            #edit-server-button:hover {
                background-color: #70C1D5;
                border: 1px solid #2E5A88;
            }

            #remove-server-button {
                background-color: #FFB6C1;
                border: 1px solid #CC3333;
                color: white;
            }
            #remove-server-button:hover {
                background-color: #FF9999;
                border: 1px solid #AA2222;
            }

            #test-server-button {
                background-color: #DDA0DD;
                border: 1px solid #993399;
                color: white;
            }
            #test-server-button:hover {
                background-color: #CC88CC;
                border: 1px solid #772277;
            }

            #add-server-button:disabled,
            #edit-server-button:disabled,
            #remove-server-button:disabled,
            #test-server-button:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            
            /* 工具信息区域 */
            #tools-info {
                background-color: #FFFFFF;
                padding: 16px;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                color: #2F4F2F;
                line-height: 1.5;
            }
            #refresh-tools-button {
                background-color: #98FB98;
                border: 1px solid #2E8B57;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                margin-top: 8px;
            }
            #refresh-tools-button:hover {
                background-color: #77DD77;
                border: 1px solid #228B22;
            }
            
            /* 输入控件样式 */
            QLineEdit, QSpinBox {
                padding: 8px 12px;
                border: 1px solid #B0E0E6;
                border-radius: 6px;
                background-color: #FFFFFF;
                selection-background-color: #98FB98;
                font-size: 14px;
            }
            QLineEdit:focus, QSpinBox:focus {
                border-color: #3CB371;
                background-color: #FFFFFF;
            }
            
            /* 标题样式 */
            #section-title {
                color: #228B22;
                font-size: 18px;
                font-weight: bold;
                margin: 15px 0 10px 0;
                border-bottom: 2px solid #98FB98;
                padding-bottom: 8px;
                text-align: center;
            }
        """
        self.setStyleSheet(self.styleSheet() + custom_styles)

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
                <li>现已支持MCP工具调用功能</li>
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
                <li>添加MCP工具调用功能</li>
                <li>我要让她更像人,啊啊啊啊</li>
            </ul>
        """)
        
        if self.font_manager:
            self.font_manager.register_widget(help_label)
            self.font_manager.register_widget(content_label)
            
        layout.addWidget(help_label)
        layout.addWidget(content_label)
        layout.addStretch()
        
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
    
    def on_mcp_config_changed(self):
        """MCP配置改变时的处理"""
        # 可以在这里添加重新初始化MCP连接的逻辑
        pass
        
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
        self.int_label.setText(f"当前亮度值：<b>{value}</b>")
        self.data_setting["luminance_img"] = value
        with open("demo_setting.json", "w", encoding="utf-8") as f:
            json.dump(self.data_setting, f, indent=4, ensure_ascii=False)
        # 发出亮度变化信号
        self.luminance_changed.emit(value)
        
        # 添加实时反馈动画
        self.animate_value_change(self.int_label)

    def on_value_changed_img(self, value):
        self.spin_label.setText(f"当前透明度值：<b>{value:.1f}</b>")
        self.transparency_img(value)
        # 发出透明度变化信号
        self.transparency_changed.emit(value)
        
        # 添加实时反馈动画
        self.animate_value_change(self.spin_label)

    def animate_value_change(self, label):
        """为数值变化添加动画效果"""
        from lib.theme_manager import AnimationManager
        # 颜色闪烁效果
        original_style = label.styleSheet()
        label.setStyleSheet(original_style + " background-color: #98FB98; ")
        
        # 1秒后恢复原样
        from PyQt6.QtCore import QTimer
        timer = QTimer()
        timer.timeout.connect(lambda: label.setStyleSheet(original_style))
        timer.setSingleShot(True)
        timer.start(1000)

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
    
    def get_luminance_img_value(self):
        try:
            return int(self.data_setting.get("luminance_img", 128))
        except (TypeError, ValueError):
            return 128

    def load_gif_folders(self):
        """加载gif文件夹下的所有子文件夹"""
        import os
        gif_path = "gif"
        self.gif_folder_combo.clear()
        
        if os.path.exists(gif_path) and os.path.isdir(gif_path):
            for item in os.listdir(gif_path):
                item_path = os.path.join(gif_path, item)
                if os.path.isdir(item_path):
                    self.gif_folder_combo.addItem(item, item)
        
        # 添加默认选项
        if self.gif_folder_combo.count() == 0:
            self.gif_folder_combo.addItem("未找到GIF文件夹", "")
        
        # 加载当前选择
        current_selection = self.data_setting.get("gif_folder", "蜡笔小新组")
        # 移除路径前缀，只保留文件夹名称
        if current_selection.startswith("gif/"):
            current_folder = current_selection[4:]  # 移除"gif/"前缀
        else:
            current_folder = current_selection
        
        # 查找匹配项并设置当前索引
        for i in range(self.gif_folder_combo.count()):
            if self.gif_folder_combo.itemData(i) == current_folder:
                self.gif_folder_combo.setCurrentIndex(i)
                break

    def save_gif_folder_selection(self):
        """保存GIF文件夹选择"""
        selected_folder = self.gif_folder_combo.currentData()
        if selected_folder:
            gif_folder_path = f"gif/{selected_folder}"
            
            # 读取现有设置
            try:
                with open("demo_setting.json", "r", encoding="utf-8") as f:
                    settings = json.load(f)
            except FileNotFoundError:
                settings = {}
            
            # 更新gif_folder设置
            settings["gif_folder"] = gif_folder_path
            
            # 保存设置
            with open("demo_setting.json", "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
            
            # 更新配置文件中的GIF文件夹设置
            # 注：GIF文件夹信息已保存到配置文件中
            
            QMessageBox.information(self, "保存成功", f"GIF文件夹已设置为: {gif_folder_path}")
        else:
            QMessageBox.warning(self, "保存失败", "请选择一个有效的GIF文件夹")

    def load_prompt(self):
        """从prompt.txt文件中加载当前AI角色设定"""
        try:
            with open("prompt.txt", "r", encoding="utf-8") as f:
                prompt = f.read()
            self.prompt_edit.setText(prompt)
        except FileNotFoundError:
            self.prompt_edit.setPlaceholderText("未找到prompt.txt文件，请输入...")
        except Exception as e:
            QMessageBox.warning(self, "加载失败", f"无法加载AI角色设定: {str(e)}")
            self.prompt_edit.setPlaceholderText("加载失败，请输入...")

    def save_prompt(self):
        """保存AI角色设定到prompt.txt文件"""
        new_prompt = self.prompt_edit.toPlainText().strip()
        if not new_prompt:
            QMessageBox.warning(self, "输入错误", "AI角色设定不能为空！")
            return

        try:
            # 保存到prompt.txt文件
            with open("prompt.txt", "w", encoding="utf-8") as f:
                f.write(new_prompt)

            # 保存到配置文件并重置对话
            # 注：AI角色设定已保存到prompt.txt文件

            QMessageBox.information(self, "保存成功", "AI角色设定已成功更新！\n请注意：修改角色设定后可能需要重启程序或开始新对话才能完全生效。")
        except Exception as e:
            QMessageBox.warning(self, "保存失败", f"无法保存AI角色设定: {str(e)}")

    def load_openai_config(self):
        """加载OpenAI接口配置"""
        try:
            # 从配置文件读取现有设置
            api_key = self.data_setting.get("openai_key", "")
            base_url = self.data_setting.get("openai_base_url", "https://api.openai.com/v1")
            model = self.data_setting.get("openai_model", "gpt-3.5-turbo")
            
            # 设置UI控件的值
            self.api_key_input.setText(api_key)
            self.base_url_input.setText(base_url)
            self.model_input.setText(model)
                
        except Exception as e:
            QMessageBox.warning(self, "加载失败", f"无法加载OpenAI配置: {str(e)}")

    def save_openai_config(self):
        """保存OpenAI接口配置"""
        api_key = self.api_key_input.text().strip()
        base_url = self.base_url_input.text().strip()
        model = self.model_input.text().strip()
        
        # 验证必填字段
        if not api_key:
            QMessageBox.warning(self, "配置错误", "API密钥不能为空！")
            return
            
        if not base_url:
            QMessageBox.warning(self, "配置错误", "基础URL不能为空！")
            return
            
        if not model:
            QMessageBox.warning(self, "配置错误", "请选择或输入模型名称！")
            return
        
        try:
            # 读取现有配置
            try:
                with open("demo_setting.json", "r", encoding="utf-8") as f:
                    settings = json.load(f)
            except FileNotFoundError:
                settings = {}
            
            # 更新OpenAI相关配置
            settings["openai_key"] = api_key
            settings["openai_base_url"] = base_url
            settings["openai_model"] = model
            
            # 保存配置文件
            with open("demo_setting.json", "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
            
            # 更新内存中的配置
            self.data_setting = settings
            
            QMessageBox.information(self, "保存成功", 
                                  f"OpenAI接口配置已保存！\n"
                                  f"API密钥: {'*' * len(api_key) if api_key else '未设置'}\n"
                                  f"基础URL: {base_url}\n"
                                  f"模型: {model}\n\n"
                                  f"请重启程序以使配置生效。")
                                  
        except Exception as e:
            QMessageBox.warning(self, "保存失败", f"无法保存OpenAI配置: {str(e)}")

    def open_prompt_file(self):
        """打开prompt.txt文件以便用户直接编辑"""
        import subprocess
        import os
        prompt_path = "prompt.txt"
        
        # 如果文件不存在，先创建一个带有默认内容的文件
        if not os.path.exists(prompt_path):
            default_prompt = "你叫丫丫，18岁女生，是个人,性格有趣且是否热情，回复要简短自然带点幽默"
            with open(prompt_path, "w", encoding="utf-8") as f:
                f.write(default_prompt)
        
        try:
            # 尝试使用系统默认编辑器打开文件
            if os.name == 'nt':  # Windows系统
                os.startfile(prompt_path)
            elif os.name == 'posix':  # macOS或Linux
                subprocess.call(('open' if sys.platform == 'darwin' else 'xdg-open', prompt_path))
            
            QMessageBox.information(self, "文件已打开", f"已在系统默认编辑器中打开 {prompt_path} \n编辑完成后记得保存文件。\n重启程序以应用更改。")
        except Exception as e:
            QMessageBox.warning(self, "打开失败", f"无法打开prompt.txt文件: {str(e)}\n您可以手动找到该文件进行编辑。")