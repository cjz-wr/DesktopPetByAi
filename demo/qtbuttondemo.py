import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QLabel, QGridLayout
)
from PyQt6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QPainterPath, QPalette

class GlassButton(QPushButton):
    """自定义玻璃效果按钮 - 点击后变色"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setFixedSize(150, 60)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 按钮状态和颜色
        self.is_clicked = False
        self.normal_bg = "rgba(255, 255, 255, 0.2)"
        self.clicked_bg = "rgba(100, 200, 255, 0.5)"  # 点击后的颜色 - 浅蓝色
        self.normal_border = "rgba(255, 255, 255, 0.4)"
        self.clicked_border = "rgba(100, 200, 255, 0.8)"
        
        # 设置初始样式
        self.update_style()
        
    def update_style(self):
        """更新按钮样式"""
        bg_color = self.clicked_bg if self.is_clicked else self.normal_bg
        border_color = self.clicked_border if self.is_clicked else self.normal_border
        
        style = f"""
            QPushButton {{
                background: {bg_color};
                border: 2px solid {border_color};
                border-radius: 30px;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 5px;
            }}
            QPushButton:hover {{
                background: {bg_color.replace('0.2', '0.3').replace('0.5', '0.6')};
                border: 2px solid {border_color.replace('0.4', '0.6').replace('0.8', '1.0')};
            }}
            QPushButton:pressed {{
                background: {bg_color.replace('0.2', '0.1').replace('0.5', '0.4')};
                border: 2px solid {border_color.replace('0.4', '0.8').replace('0.8', '1.0')};
            }}
        """
        self.setStyleSheet(style)
    
    def mousePressEvent(self, event):
        """鼠标按下事件 - 切换按钮状态"""
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 切换按钮状态并更新样式"""
        super().mouseReleaseEvent(event)
        self.is_clicked = not self.is_clicked
        self.update_style()

class AnimatedGlassButton(QPushButton):
    """带有颜色过渡动画的玻璃效果按钮"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setFixedSize(150, 60)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 按钮状态和颜色
        self.is_clicked = False
        
        # 定义颜色方案
        self.color_schemes = [
            {"bg": "rgba(100, 200, 255, 0.5)", "border": "rgba(100, 200, 255, 0.8)", "name": "蓝色"},
            {"bg": "rgba(255, 100, 150, 0.5)", "border": "rgba(255, 100, 150, 0.8)", "name": "粉色"},
            {"bg": "rgba(100, 255, 150, 0.5)", "border": "rgba(100, 255, 150, 0.8)", "name": "绿色"},
            {"bg": "rgba(255, 200, 100, 0.5)", "border": "rgba(255, 200, 100, 0.8)", "name": "橙色"},
            {"bg": "rgba(200, 100, 255, 0.5)", "border": "rgba(200, 100, 255, 0.8)", "name": "紫色"}
        ]
        
        self.current_color_index = 0
        self.normal_bg = "rgba(255, 255, 255, 0.2)"
        self.normal_border = "rgba(255, 255, 255, 0.4)"
        
        # 设置初始样式
        self.update_style()
        
    def update_style(self):
        """更新按钮样式"""
        if self.is_clicked:
            scheme = self.color_schemes[self.current_color_index]
            bg_color = scheme["bg"]
            border_color = scheme["border"]
        else:
            bg_color = self.normal_bg
            border_color = self.normal_border
        
        style = f"""
            QPushButton {{
                background: {bg_color};
                border: 2px solid {border_color};
                border-radius: 30px;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 5px;
                transition: background 0.3s, border 0.3s;
            }}
            QPushButton:hover {{
                background: {bg_color.replace('0.2', '0.3').replace('0.5', '0.6')};
                border: 2px solid {border_color.replace('0.4', '0.6').replace('0.8', '1.0')};
            }}
        """
        self.setStyleSheet(style)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 切换颜色方案"""
        super().mouseReleaseEvent(event)
        
        # 切换点击状态并循环颜色方案
        self.is_clicked = not self.is_clicked
        
        if self.is_clicked:
            self.current_color_index = (self.current_color_index + 1) % len(self.color_schemes)
        
        self.update_style()

class ToggleGlassButton(QPushButton):
    """切换式玻璃按钮 - 保持点击后的状态"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setFixedSize(150, 60)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 初始状态为未选中
        self.is_selected = False
        
        # 设置初始样式
        self.update_style()
        
    def update_style(self):
        """更新按钮样式"""
        if self.is_selected:
            # 选中状态 - 绿色
            bg_color = "rgba(100, 255, 150, 0.5)"
            border_color = "rgba(100, 255, 150, 0.8)"
            text_color = "white"
        else:
            # 未选中状态
            bg_color = "rgba(255, 255, 255, 0.2)"
            border_color = "rgba(255, 255, 255, 0.4)"
            text_color = "white"
        
        style = f"""
            QPushButton {{
                background: {bg_color};
                border: 2px solid {border_color};
                border-radius: 30px;
                color: {text_color};
                font-size: 16px;
                font-weight: bold;
                padding: 5px;
            }}
            QPushButton:hover {{
                background: {bg_color.replace('0.2', '0.3').replace('0.5', '0.6')};
                border: 2px solid {border_color.replace('0.4', '0.6').replace('0.8', '1.0')};
            }}
        """
        self.setStyleSheet(style)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 切换选中状态"""
        super().mouseReleaseEvent(event)
        self.is_selected = not self.is_selected
        self.update_style()
        
        # 更新按钮文本以显示状态
        if self.is_selected:
            self.setText(f"{self.text()} ✓")
        else:
            self.setText(self.text().replace(" ✓", ""))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("透明玻璃按钮 - 点击变色效果")
        self.setGeometry(100, 100, 800, 600)
        
        # 设置窗口透明和无边框
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # 创建中心部件
        central_widget = QWidget()
        central_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #1a2980, 
                    stop:1 #26d0ce);
                border-radius: 20px;
            }
        """)
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)
        
        # 标题
        title = QLabel("透明玻璃按钮 - 点击变色效果")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 32px;
                font-weight: bold;
                padding: 20px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                border: 2px solid rgba(255, 255, 255, 0.2);
            }
        """)
        main_layout.addWidget(title)
        
        # 创建网格布局用于放置不同类型的按钮
        grid_layout = QGridLayout()
        grid_layout.setSpacing(30)
        grid_layout.setContentsMargins(20, 20, 20, 20)
        
        # 类型1: 简单变色按钮
        type1_label = QLabel("类型1: 点击切换颜色")
        type1_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        grid_layout.addWidget(type1_label, 0, 0, 1, 2)
        
        self.btn1 = GlassButton("按钮一")
        self.btn2 = GlassButton("按钮二")
        self.btn3 = GlassButton("按钮三")
        
        grid_layout.addWidget(self.btn1, 1, 0)
        grid_layout.addWidget(self.btn2, 1, 1)
        grid_layout.addWidget(self.btn3, 2, 0, 1, 2)
        
        # 类型2: 多种颜色循环按钮
        type2_label = QLabel("类型2: 点击循环多种颜色")
        type2_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        grid_layout.addWidget(type2_label, 0, 2, 1, 2)
        
        self.btn4 = AnimatedGlassButton("多彩按钮一")
        self.btn5 = AnimatedGlassButton("多彩按钮二")
        self.btn6 = AnimatedGlassButton("多彩按钮三")
        
        grid_layout.addWidget(self.btn4, 1, 2)
        grid_layout.addWidget(self.btn5, 1, 3)
        grid_layout.addWidget(self.btn6, 2, 2, 1, 2)
        
        # 类型3: 切换式按钮（保持状态）
        type3_label = QLabel("类型3: 切换式按钮（保持状态）")
        type3_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        grid_layout.addWidget(type3_label, 3, 0, 1, 4)
        
        self.toggle_btn1 = ToggleGlassButton("选项一")
        self.toggle_btn2 = ToggleGlassButton("选项二")
        self.toggle_btn3 = ToggleGlassButton("选项三")
        self.toggle_btn4 = ToggleGlassButton("选项四")
        
        grid_layout.addWidget(self.toggle_btn1, 4, 0)
        grid_layout.addWidget(self.toggle_btn2, 4, 1)
        grid_layout.addWidget(self.toggle_btn3, 4, 2)
        grid_layout.addWidget(self.toggle_btn4, 4, 3)
        
        main_layout.addLayout(grid_layout)
        
        # 状态显示区域
        status_container = QWidget()
        status_container.setStyleSheet("""
            QWidget {
                background: rgba(0, 0, 0, 0.2);
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        status_layout = QVBoxLayout(status_container)
        
        self.status_label = QLabel("点击任意按钮查看效果")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                padding: 20px;
            }
        """)
        
        # 重置按钮
        reset_btn = QPushButton("重置所有按钮状态")
        reset_btn.setFixedSize(200, 50)
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 100, 100, 0.5);
                border: 2px solid rgba(255, 100, 100, 0.8);
                border-radius: 25px;
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 100, 100, 0.7);
                border: 2px solid rgba(255, 150, 150, 0.9);
            }
        """)
        reset_btn.clicked.connect(self.reset_all_buttons)
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(reset_btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        main_layout.addWidget(status_container)
        
        # 控制按钮容器
        control_container = QWidget()
        control_layout = QHBoxLayout(control_container)
        
        # 添加窗口控制按钮
        minimize_btn = QPushButton("最小化")
        minimize_btn.setFixedSize(120, 40)
        minimize_btn.setStyleSheet("""
            QPushButton {
                background: rgba(100, 100, 255, 0.5);
                border: 2px solid rgba(100, 100, 255, 0.8);
                border-radius: 20px;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(100, 100, 255, 0.7);
            }
        """)
        minimize_btn.clicked.connect(self.showMinimized)
        minimize_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        close_btn = QPushButton("关闭窗口")
        close_btn.setFixedSize(120, 40)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 100, 100, 0.5);
                border: 2px solid rgba(255, 100, 100, 0.8);
                border-radius: 20px;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 100, 100, 0.7);
            }
        """)
        close_btn.clicked.connect(self.close)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        control_layout.addStretch()
        control_layout.addWidget(minimize_btn)
        control_layout.addWidget(close_btn)
        
        main_layout.addWidget(control_container)
        
        # 连接所有按钮的点击事件
        self.connect_button_events()
        
        # 用于窗口拖动的变量
        self.dragging = False
        self.offset = QPoint()

    def connect_button_events(self):
        """连接所有按钮的点击事件"""
        # 类型1按钮
        self.btn1.clicked.connect(lambda: self.on_button_click("按钮一"))
        self.btn2.clicked.connect(lambda: self.on_button_click("按钮二"))
        self.btn3.clicked.connect(lambda: self.on_button_click("按钮三"))
        
        # 类型2按钮
        self.btn4.clicked.connect(lambda: self.on_button_click("多彩按钮一"))
        self.btn5.clicked.connect(lambda: self.on_button_click("多彩按钮二"))
        self.btn6.clicked.connect(lambda: self.on_button_click("多彩按钮三"))
        
        # 类型3按钮
        self.toggle_btn1.clicked.connect(lambda: self.on_toggle_button_click("选项一", self.toggle_btn1))
        self.toggle_btn2.clicked.connect(lambda: self.on_toggle_button_click("选项二", self.toggle_btn2))
        self.toggle_btn3.clicked.connect(lambda: self.on_toggle_button_click("选项三", self.toggle_btn3))
        self.toggle_btn4.clicked.connect(lambda: self.on_toggle_button_click("选项四", self.toggle_btn4))

    def on_button_click(self, button_name):
        """按钮点击事件处理"""
        self.status_label.setText(f"您点击了: {button_name}")

    def on_toggle_button_click(self, button_name, button):
        """切换按钮点击事件处理"""
        status = "选中" if button.is_selected else "取消选中"
        self.status_label.setText(f"{button_name}: {status}")

    def reset_all_buttons(self):
        """重置所有按钮状态"""
        # 重置类型1按钮
        self.btn1.is_clicked = False
        self.btn1.update_style()
        self.btn2.is_clicked = False
        self.btn2.update_style()
        self.btn3.is_clicked = False
        self.btn3.update_style()
        
        # 重置类型2按钮
        self.btn4.is_clicked = False
        self.btn4.update_style()
        self.btn5.is_clicked = False
        self.btn5.update_style()
        self.btn6.is_clicked = False
        self.btn6.update_style()
        
        # 重置类型3按钮
        self.toggle_btn1.is_selected = False
        self.toggle_btn1.setText("选项一")
        self.toggle_btn1.update_style()
        self.toggle_btn2.is_selected = False
        self.toggle_btn2.setText("选项二")
        self.toggle_btn2.update_style()
        self.toggle_btn3.is_selected = False
        self.toggle_btn3.setText("选项三")
        self.toggle_btn3.update_style()
        self.toggle_btn4.is_selected = False
        self.toggle_btn4.setText("选项四")
        self.toggle_btn4.update_style()
        
        self.status_label.setText("已重置所有按钮状态")

    def mousePressEvent(self, event):
        """鼠标按下事件，用于窗口拖动"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        """鼠标移动事件，用于窗口拖动"""
        if self.dragging:
            self.move(self.pos() + event.pos() - self.offset)

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # 使用Fusion风格以获得更好的视觉效果
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())