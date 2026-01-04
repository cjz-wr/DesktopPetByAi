"""
将玻璃按钮集成到现有项目中
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QTextEdit, QMenuBar, QStatusBar
)
from PyQt6.QtCore import Qt


try:
    from lib.glass_button_lib import GlassButton, ToggleGlassButton
except ImportError:
    # 如果上述导入失败，尝试添加项目路径到sys.path后导入
    import os
    import sys
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # 假设lib目录在项目根目录下,即获取上级目录
    sys.path.insert(0, project_root) # 添加项目路径到sys.path
    from lib.glass_button_lib import GlassButton, ToggleGlassButton


class CustomApplication(QMainWindow):
    """自定义应用程序，集成了玻璃按钮"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("我的应用 - 玻璃按钮集成")
        self.setGeometry(100, 100, 900, 600)
        
        # 设置应用样式
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2c3e50,
                    stop:1 #34495e);
            }
        """)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 1. 顶部工具栏
        toolbar = self.create_toolbar()
        main_layout.addWidget(toolbar)
        
        # 2. 内容区域
        content_area = self.create_content_area()
        main_layout.addWidget(content_area, 1)  # 1表示拉伸因子
        
        # 3. 底部状态栏
        self.create_status_bar()
        
        # 连接信号
        self.connect_signals()
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background: rgba(44, 62, 80, 0.9);
                color: white;
                padding: 5px;
            }
            QMenuBar::item:selected {
                background: rgba(52, 152, 219, 0.7);
            }
            QMenu {
                background: rgba(44, 62, 80, 0.95);
                color: white;
                border: 1px solid #7f8c8d;
            }
            QMenu::item:selected {
                background: rgba(52, 152, 219, 0.5);
            }
        """)
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        file_menu.addAction("新建")
        file_menu.addAction("打开")
        file_menu.addSeparator()
        file_menu.addAction("退出").triggered.connect(self.close)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")
        edit_menu.addAction("撤销")
        edit_menu.addAction("重做")
        
        # 视图菜单
        view_menu = menubar.addMenu("视图")
        view_menu.addAction("工具栏")
        view_menu.addAction("状态栏")
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        help_menu.addAction("关于")
    
    def create_toolbar(self):
        """创建工具栏（使用玻璃按钮）"""
        toolbar = QWidget()
        toolbar.setStyleSheet("background: rgba(0, 0, 0, 0.1); border-radius: 10px; padding: 10px;")
        
        layout = QHBoxLayout(toolbar)
        layout.setSpacing(10)
        
        # 创建各种工具按钮
        new_btn = GlassButton(
            text="新建",
            size=(80, 40),
            clicked_color="rgba(46, 204, 113, 0.6)"
        )
        new_btn.clicked.connect(self.on_new)
        
        open_btn = GlassButton(
            text="打开",
            size=(80, 40),
            clicked_color="rgba(52, 152, 219, 0.6)"
        )
        open_btn.clicked.connect(self.on_open)
        
        save_btn = GlassButton(
            text="保存",
            size=(80, 40),
            clicked_color="rgba(155, 89, 182, 0.6)"
        )
        save_btn.clicked.connect(self.on_save)
        
        # 切换按钮作为工具开关
        auto_save_toggle = ToggleGlassButton(
            text="自动保存",
            size=(120, 40),
            selected_color="rgba(241, 196, 15, 0.6)"
        )
        auto_save_toggle.stateChanged.connect(self.on_auto_save_changed)
        
        layout.addWidget(new_btn)
        layout.addWidget(open_btn)
        layout.addWidget(save_btn)
        layout.addStretch()
        layout.addWidget(auto_save_toggle)
        
        return toolbar
    
    def create_content_area(self):
        """创建内容区域"""
        content = QWidget()
        
        layout = QVBoxLayout(content)
        layout.setSpacing(15)
        
        # 标题
        title = QLabel("文档编辑器")
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 文本编辑器
        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 0.9);
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 10px;
                font-size: 14px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.text_edit, 1)  # 1表示拉伸因子
        
        # 格式控制按钮
        format_controls = self.create_format_controls()
        layout.addWidget(format_controls)
        
        return content
    
    def create_format_controls(self):
        """创建格式控制按钮"""
        controls = QWidget()
        
        layout = QHBoxLayout(controls)
        layout.setSpacing(10)
        
        # 字体控制
        font_group = QWidget()
        font_layout = QHBoxLayout(font_group)
        
        bold_toggle = ToggleGlassButton(
            text="粗体",
            size=(80, 35),
            selected_color="rgba(52, 73, 94, 0.6)"
        )
        bold_toggle.stateChanged.connect(self.on_bold_changed)
        
        italic_toggle = ToggleGlassButton(
            text="斜体",
            size=(80, 35),
            selected_color="rgba(52, 73, 94, 0.6)"
        )
        italic_toggle.stateChanged.connect(self.on_italic_changed)
        
        underline_toggle = ToggleGlassButton(
            text="下划线",
            size=(80, 35),
            selected_color="rgba(52, 73, 94, 0.6)"
        )
        underline_toggle.stateChanged.connect(self.on_underline_changed)
        
        font_layout.addWidget(bold_toggle)
        font_layout.addWidget(italic_toggle)
        font_layout.addWidget(underline_toggle)
        
        # 对齐控制
        align_group = QWidget()
        align_layout = QHBoxLayout(align_group)
        
        left_align = GlassButton("左", size=(50, 35))
        left_align.clicked.connect(lambda: self.set_alignment(Qt.AlignmentFlag.AlignLeft))
        
        center_align = GlassButton("中", size=(50, 35))
        center_align.clicked.connect(lambda: self.set_alignment(Qt.AlignmentFlag.AlignCenter))
        
        right_align = GlassButton("右", size=(50, 35))
        right_align.clicked.connect(lambda: self.set_alignment(Qt.AlignmentFlag.AlignRight))
        
        align_layout.addWidget(left_align)
        align_layout.addWidget(center_align)
        align_layout.addWidget(right_align)
        
        layout.addWidget(font_group)
        layout.addStretch()
        layout.addWidget(align_group)
        
        return controls
    
    def create_status_bar(self):
        """创建状态栏"""
        status_bar = QStatusBar()
        status_bar.setStyleSheet("""
            QStatusBar {
                background: rgba(44, 62, 80, 0.9);
                color: white;
                border-top: 1px solid #7f8c8d;
            }
        """)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #bdc3c7; padding: 5px;")
        status_bar.addWidget(self.status_label)
        
        # 字数统计
        self.word_count_label = QLabel("字数: 0")
        self.word_count_label.setStyleSheet("color: #bdc3c7; padding: 5px;")
        status_bar.addPermanentWidget(self.word_count_label)
        
        self.setStatusBar(status_bar)
    
    def connect_signals(self):
        """连接信号"""
        # 文本变化时更新字数统计
        self.text_edit.textChanged.connect(self.update_word_count)
    
    def update_word_count(self):
        """更新字数统计"""
        text = self.text_edit.toPlainText()
        word_count = len(text.split())
        self.word_count_label.setText(f"字数: {word_count}")
    
    def on_new(self):
        """新建文档"""
        self.text_edit.clear()
        self.status_label.setText("已创建新文档")
        print("新建文档")
    
    def on_open(self):
        """打开文档"""
        # 这里简化处理，实际应用中应该有文件对话框
        self.status_label.setText("打开文档...")
        print("打开文档")
    
    def on_save(self):
        """保存文档"""
        text = self.text_edit.toPlainText()
        if text:
            self.status_label.setText("文档已保存")
            print("保存文档")
        else:
            self.status_label.setText("文档为空，无需保存")
    
    def on_auto_save_changed(self, enabled):
        """自动保存开关变化"""
        status = "启用" if enabled else "禁用"
        self.status_label.setText(f"自动保存已{status}")
        print(f"自动保存: {status}")
    
    def on_bold_changed(self, enabled):
        """粗体切换"""
        cursor = self.text_edit.textCursor()
        format = cursor.charFormat()
        format.setFontWeight(75 if enabled else 50)  # 75=粗体，50=正常
        cursor.setCharFormat(format)
        self.text_edit.setTextCursor(cursor)
        print(f"粗体: {enabled}")
    
    def on_italic_changed(self, enabled):
        """斜体切换"""
        cursor = self.text_edit.textCursor()
        format = cursor.charFormat()
        format.setFontItalic(enabled)
        cursor.setCharFormat(format)
        self.text_edit.setTextCursor(cursor)
        print(f"斜体: {enabled}")
    
    def on_underline_changed(self, enabled):
        """下划线切换"""
        cursor = self.text_edit.textCursor()
        format = cursor.charFormat()
        format.setFontUnderline(enabled)
        cursor.setCharFormat(format)
        self.text_edit.setTextCursor(cursor)
        print(f"下划线: {enabled}")
    
    def set_alignment(self, alignment):
        """设置对齐方式"""
        self.text_edit.setAlignment(alignment)
        align_names = {
            Qt.AlignmentFlag.AlignLeft: "左对齐",
            Qt.AlignmentFlag.AlignCenter: "居中对齐",
            Qt.AlignmentFlag.AlignRight: "右对齐"
        }
        self.status_label.setText(f"已设置为{align_names.get(alignment, '未知')}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CustomApplication()
    window.show()
    sys.exit(app.exec())