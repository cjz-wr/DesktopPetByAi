"""
Glass Button Library - 透明玻璃按钮库
提供多种玻璃效果的按钮组件
"""

import sys
from PyQt6.QtWidgets import (
    QPushButton, QApplication, QMainWindow, QWidget, 
    QVBoxLayout, QHBoxLayout, QLabel, QGridLayout
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QPoint, pyqtSignal
from PyQt6.QtGui import QColor


class GlassButton(QPushButton):
    """
    单色变换玻璃按钮
    
    参数:
        text (str): 按钮文本
        parent (QWidget): 父组件
        size (tuple): 按钮尺寸 (宽度, 高度)，默认(150, 60)
        normal_color (str): 正常状态颜色，默认rgba(255, 255, 255, 0.2)
        clicked_color (str): 点击状态颜色，默认rgba(100, 200, 255, 0.5)
        border_radius (int): 圆角半径，默认30
        enable_animation (bool): 是否启用动画，默认True
    """
    
    # 定义状态改变信号
    stateChanged = pyqtSignal(bool)
    
    def __init__(self, text="", parent=None, size=(150, 60), 
                 normal_color="rgba(255, 255, 255, 0.2)", 
                 clicked_color="rgba(100, 200, 255, 0.5)",
                 border_radius=30,
                 enable_animation=True):
        super().__init__(text, parent)
        
        # 按钮配置
        self._text = text
        self._size = size
        self._normal_color = normal_color
        self._clicked_color = clicked_color
        self._border_radius = border_radius
        self._enable_animation = enable_animation
        
        # 按钮状态
        self._is_clicked = False
        
        # 动画相关
        self._animation = None
        self._opacity = 1.0
        
        # 初始化按钮
        self._init_button()
    
    def _init_button(self):
        """初始化按钮样式和属性"""
        self.setFixedSize(self._size[0], self._size[1])
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 解析颜色值
        self._normal_rgba = self._parse_color(self._normal_color)
        self._clicked_rgba = self._parse_color(self._clicked_color)
        
        # 计算边框颜色
        self._normal_border = self._get_border_color(self._normal_rgba)
        self._clicked_border = self._get_border_color(self._clicked_rgba)
        
        # 设置初始样式
        self._update_style()
        
        # 如果启用动画，设置动画
        if self._enable_animation:
            self._setup_animation()
    
    def _parse_color(self, color_str):
        """解析颜色字符串为RGBA值"""
        if color_str.startswith('rgba'):
            # 提取rgba值
            values = color_str[5:-1].split(',')
            return tuple(int(v.strip()) for v in values[:3]) + (float(values[3].strip()),)
        elif color_str.startswith('rgb'):
            # 提取rgb值
            values = color_str[4:-1].split(',')
            return tuple(int(v.strip()) for v in values) + (1.0,)
        else:
            # 默认白色半透明
            return (255, 255, 255, 0.2)
    
    def _get_border_color(self, rgba):
        """根据背景色计算边框颜色"""
        r, g, b, a = rgba
        # 边框颜色更不透明一些
        return f"rgba({r}, {g}, {b}, {min(a + 0.2, 1.0)})"
    
    def _rgba_to_str(self, rgba):
        """将RGBA元组转换为字符串"""
        r, g, b, a = rgba
        return f"rgba({r}, {g}, {b}, {a})"
    
    def _setup_animation(self):
        """设置按钮动画"""
        self._animation = QPropertyAnimation(self, b"opacity")
        self._animation.setDuration(200)  # 200ms动画
        self._animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
    
    def _update_style(self):
        """更新按钮样式"""
        if self._is_clicked:
            bg_color = self._rgba_to_str(self._clicked_rgba)
            border_color = self._clicked_border
        else:
            bg_color = self._rgba_to_str(self._normal_rgba)
            border_color = self._normal_border
        
        # 创建悬停状态的颜色
        hover_bg = bg_color.replace(str(self._normal_rgba[3]), str(min(self._normal_rgba[3] + 0.1, 1.0))) if not self._is_clicked else \
                  bg_color.replace(str(self._clicked_rgba[3]), str(min(self._clicked_rgba[3] + 0.1, 1.0)))
        
        style = f"""
            QPushButton {{
                background: {bg_color};
                border: 2px solid {border_color};
                border-radius: {self._border_radius}px;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 5px;
            }}
            QPushButton:hover {{
                background: {hover_bg};
                border: 2px solid {border_color.replace(str(self._normal_rgba[3]), str(min(self._normal_rgba[3] + 0.2, 1.0))) if not self._is_clicked else border_color.replace(str(self._clicked_rgba[3]), str(min(self._clicked_rgba[3] + 0.2, 1.0)))};
            }}
            QPushButton:pressed {{
                background: {bg_color.replace(str(self._normal_rgba[3]), str(max(self._normal_rgba[3] - 0.1, 0.1))) if not self._is_clicked else bg_color.replace(str(self._clicked_rgba[3]), str(max(self._clicked_rgba[3] - 0.1, 0.1)))};
                border: 2px solid {border_color.replace(str(self._normal_rgba[3]), str(min(self._normal_rgba[3] + 0.3, 1.0))) if not self._is_clicked else border_color.replace(str(self._clicked_rgba[3]), str(min(self._clicked_rgba[3] + 0.3, 1.0)))};
            }}
        """
        self.setStyleSheet(style)
    
    @pyqtProperty(float)
    def opacity(self):
        """获取按钮透明度"""
        return self._opacity
    
    @opacity.setter
    def opacity(self, value):
        """设置按钮透明度"""
        self._opacity = value
        self.update()
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if self._enable_animation and self._animation:
            self._animation.setStartValue(1.0)
            self._animation.setEndValue(0.7)
            self._animation.start()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if self._enable_animation and self._animation:
            self._animation.setStartValue(0.7)
            self._animation.setEndValue(1.0)
            self._animation.start()
        
        # 切换点击状态
        self._is_clicked = not self._is_clicked
        self._update_style()
        
        # 发出状态改变信号
        self.stateChanged.emit(self._is_clicked)
        
        super().mouseReleaseEvent(event)
    
    def setNormalColor(self, color):
        """设置正常状态颜色"""
        self._normal_color = color
        self._normal_rgba = self._parse_color(color)
        self._normal_border = self._get_border_color(self._normal_rgba)
        self._update_style()
    
    def setClickedColor(self, color):
        """设置点击状态颜色"""
        self._clicked_color = color
        self._clicked_rgba = self._parse_color(color)
        self._clicked_border = self._get_border_color(self._clicked_rgba)
        self._update_style()
    
    def setSize(self, width, height):
        """设置按钮尺寸"""
        self._size = (width, height)
        self.setFixedSize(width, height)
    
    def setBorderRadius(self, radius):
        """设置圆角半径"""
        self._border_radius = radius
        self._update_style()
    
    def setAnimationEnabled(self, enabled):
        """启用或禁用动画"""
        self._enable_animation = enabled
        if enabled and not self._animation:
            self._setup_animation()
    
    def isClicked(self):
        """获取按钮当前状态"""
        return self._is_clicked
    
    def setClicked(self, clicked):
        """设置按钮状态"""
        if self._is_clicked != clicked:
            self._is_clicked = clicked
            self._update_style()
    
    def reset(self):
        """重置按钮状态"""
        self._is_clicked = False
        self._update_style()


class ToggleGlassButton(GlassButton):
    """
    切换式玻璃按钮（保持选中状态）
    
    参数:
        text (str): 按钮文本
        parent (QWidget): 父组件
        size (tuple): 按钮尺寸 (宽度, 高度)，默认(150, 60)
        normal_color (str): 正常状态颜色，默认rgba(255, 255, 255, 0.2)
        selected_color (str): 选中状态颜色，默认rgba(100, 255, 150, 0.5)
        show_checkmark (bool): 是否显示选中标记，默认True
    """
    
    def __init__(self, text="", parent=None, size=(150, 60), 
                 normal_color="rgba(255, 255, 255, 0.2)", 
                 selected_color="rgba(100, 255, 150, 0.5)",
                 show_checkmark=True):
        super().__init__(text, parent, size, normal_color, selected_color)
        
        # 切换按钮特定属性
        self._show_checkmark = show_checkmark
        self._selected_color = selected_color
        self._selected_rgba = self._parse_color(selected_color)
        
        # 初始状态为未选中
        self._is_selected = False
        self._original_text = text
        
        # 更新样式
        self._update_toggle_style()
    
    def _update_toggle_style(self):
        """更新切换按钮样式"""
        if self._is_selected:
            bg_color = self._rgba_to_str(self._selected_rgba)
            border_color = self._get_border_color(self._selected_rgba)
        else:
            bg_color = self._rgba_to_str(self._normal_rgba)
            border_color = self._normal_border
        
        # 更新文本
        if self._show_checkmark:
            if self._is_selected:
                self.setText(f"{self._original_text} ✓")
            else:
                self.setText(self._original_text)
        
        # 悬停颜色
        hover_bg = bg_color.replace(str(self._normal_rgba[3]), str(min(self._normal_rgba[3] + 0.1, 1.0))) if not self._is_selected else \
                  bg_color.replace(str(self._selected_rgba[3]), str(min(self._selected_rgba[3] + 0.1, 1.0)))
        
        style = f"""
            QPushButton {{
                background: {bg_color};
                border: 2px solid {border_color};
                border-radius: {self._border_radius}px;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 5px;
            }}
            QPushButton:hover {{
                background: {hover_bg};
                border: 2px solid {border_color.replace(str(self._normal_rgba[3]), str(min(self._normal_rgba[3] + 0.2, 1.0))) if not self._is_selected else border_color.replace(str(self._selected_rgba[3]), str(min(self._selected_rgba[3] + 0.2, 1.0)))};
            }}
        """
        self.setStyleSheet(style)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 切换选中状态"""
        # 切换选中状态
        self._is_selected = not self._is_selected
        
        # 更新样式
        self._update_toggle_style()
        
        # 发出状态改变信号
        self.stateChanged.emit(self._is_selected)
        
        super().mouseReleaseEvent(event)
    
    def isSelected(self):
        """获取选中状态"""
        return self._is_selected
    
    def setSelected(self, selected):
        """设置选中状态"""
        if self._is_selected != selected:
            self._is_selected = selected
            self._update_toggle_style()
    
    def setShowCheckmark(self, show):
        """设置是否显示选中标记"""
        self._show_checkmark = show
        self._update_toggle_style()
    
    def setSelectedColor(self, color):
        """设置选中状态颜色"""
        self._selected_color = color
        self._selected_rgba = self._parse_color(color)
        self._update_toggle_style()
    
    def reset(self):
        """重置按钮状态"""
        self._is_selected = False
        self._update_toggle_style()


# ==============================
# 示例窗口类
# ==============================

class ExampleWindow(QMainWindow):
    """示例窗口，展示玻璃按钮的用法"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("玻璃按钮库 - 示例")
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
        title = QLabel("玻璃按钮库示例")
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
        
        # 创建网格布局
        grid_layout = QGridLayout()
        grid_layout.setSpacing(30)
        grid_layout.setContentsMargins(20, 20, 20, 20)
        
        # 示例1: 基本按钮
        basic_label = QLabel("基本按钮示例")
        basic_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        grid_layout.addWidget(basic_label, 0, 0, 1, 2)
        
        # 创建不同颜色的按钮
        self.btn1 = GlassButton("蓝色按钮")
        
        self.btn2 = GlassButton(
            text="粉色按钮",
            clicked_color="rgba(255, 100, 150, 0.5)"
        )
        
        self.btn3 = GlassButton(
            text="绿色按钮",
            clicked_color="rgba(100, 255, 150, 0.5)"
        )
        
        self.btn4 = GlassButton(
            text="橙色按钮",
            clicked_color="rgba(255, 200, 100, 0.5)"
        )
        
        grid_layout.addWidget(self.btn1, 1, 0)
        grid_layout.addWidget(self.btn2, 1, 1)
        grid_layout.addWidget(self.btn3, 2, 0)
        grid_layout.addWidget(self.btn4, 2, 1)
        
        # 示例2: 切换按钮
        toggle_label = QLabel("切换按钮示例")
        toggle_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        grid_layout.addWidget(toggle_label, 0, 2, 1, 2)
        
        self.toggle1 = ToggleGlassButton("选项一")
        self.toggle2 = ToggleGlassButton(
            text="选项二",
            selected_color="rgba(255, 100, 255, 0.5)"
        )
        self.toggle3 = ToggleGlassButton("选项三")
        self.toggle4 = ToggleGlassButton(
            text="选项四",
            selected_color="rgba(255, 200, 100, 0.5)"
        )
        
        grid_layout.addWidget(self.toggle1, 1, 2)
        grid_layout.addWidget(self.toggle2, 1, 3)
        grid_layout.addWidget(self.toggle3, 2, 2)
        grid_layout.addWidget(self.toggle4, 2, 3)
        
        main_layout.addLayout(grid_layout)
        
        # 控制区域
        control_container = QWidget()
        control_container.setStyleSheet("""
            QWidget {
                background: rgba(0, 0, 0, 0.2);
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        control_layout = QVBoxLayout(control_container)
        
        # 状态显示
        self.status_label = QLabel("点击按钮查看效果")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                padding: 20px;
            }
        """)
        
        # 控制按钮
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        
        reset_btn = GlassButton(
            text="重置所有",
            size=(150, 50),
            clicked_color="rgba(255, 100, 100, 0.5)"
        )
        reset_btn.clicked.connect(self.reset_all)
        
        btn_layout.addStretch()
        btn_layout.addWidget(reset_btn)
        btn_layout.addStretch()
        
        control_layout.addWidget(self.status_label)
        control_layout.addWidget(btn_container)
        
        main_layout.addWidget(control_container)
        
        # 窗口控制按钮
        window_control = QWidget()
        window_layout = QHBoxLayout(window_control)
        
        minimize_btn = GlassButton(
            text="最小化",
            size=(120, 40),
            clicked_color="rgba(100, 100, 255, 0.5)"
        )
        minimize_btn.clicked.connect(self.showMinimized)
        
        close_btn = GlassButton(
            text="关闭",
            size=(120, 40),
            clicked_color="rgba(255, 100, 100, 0.5)"
        )
        close_btn.clicked.connect(self.close)
        
        window_layout.addStretch()
        window_layout.addWidget(minimize_btn)
        window_layout.addWidget(close_btn)
        
        main_layout.addWidget(window_control)
        
        # 连接按钮事件
        self.connect_buttons()
        
        # 用于窗口拖动的变量
        self.dragging = False
        self.offset = QPoint()
    
    def connect_buttons(self):
        """连接按钮事件"""
        # 基本按钮
        self.btn1.stateChanged.connect(lambda state: self.update_status("蓝色按钮", state))
        self.btn2.stateChanged.connect(lambda state: self.update_status("粉色按钮", state))
        self.btn3.stateChanged.connect(lambda state: self.update_status("绿色按钮", state))
        self.btn4.stateChanged.connect(lambda state: self.update_status("橙色按钮", state))
        
        # 切换按钮
        self.toggle1.stateChanged.connect(lambda state: self.update_status("选项一", state, True))
        self.toggle2.stateChanged.connect(lambda state: self.update_status("选项二", state, True))
        self.toggle3.stateChanged.connect(lambda state: self.update_status("选项三", state, True))
        self.toggle4.stateChanged.connect(lambda state: self.update_status("选项四", state, True))
    
    def update_status(self, name, state, is_toggle=False):
        """更新状态显示"""
        if is_toggle:
            status = "选中" if state else "取消选中"
        else:
            status = "点击" if state else "释放"
        self.status_label.setText(f"{name}: {status}")
    
    def reset_all(self):
        """重置所有按钮"""
        # 重置基本按钮
        self.btn1.reset()
        self.btn2.reset()
        self.btn3.reset()
        self.btn4.reset()
        
        # 重置切换按钮
        self.toggle1.reset()
        self.toggle2.reset()
        self.toggle3.reset()
        self.toggle4.reset()
        
        self.status_label.setText("已重置所有按钮")
    
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


class QuickStartDemo(QWidget):
    """快速开始示例"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("快速开始 - 玻璃按钮")
        self.setGeometry(300, 300, 400, 300)
        self.setStyleSheet("background: #2c3e50;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # 创建简单的玻璃按钮
        btn1 = GlassButton("点击我")
        btn1.stateChanged.connect(self.on_button_state_changed)
        
        # 创建自定义颜色的按钮
        btn2 = GlassButton(
            text="自定义颜色",
            clicked_color="rgba(255, 100, 150, 0.6)",
            size=(180, 50)
        )
        btn2.stateChanged.connect(self.on_button_state_changed)
        
        # 创建切换按钮
        toggle_btn = ToggleGlassButton("切换选项")
        toggle_btn.stateChanged.connect(self.on_toggle_state_changed)
        
        layout.addWidget(btn1)
        layout.addWidget(btn2)
        layout.addWidget(toggle_btn)
        
    def on_button_state_changed(self, state):
        print(f"按钮状态: {'点击' if state else '释放'}")
    
    def on_toggle_state_changed(self, state):
        print(f"切换状态: {'选中' if state else '取消选中'}")


# ==============================
# 库函数
# ==============================

def show_example():
    """显示完整示例窗口"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = ExampleWindow()
    window.show()
    app.exec()

def show_quick_start():
    """显示快速开始示例"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    demo = QuickStartDemo()
    demo.show()
    app.exec()

def create_button_demo(parent=None):
    """
    创建一个按钮演示面板
    
    参数:
        parent: 父组件
    
    返回:
        QWidget: 包含按钮演示的面板
    """
    demo_panel = QWidget(parent)
    layout = QVBoxLayout(demo_panel)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(15)
    
    # 标题
    title = QLabel("玻璃按钮演示面板")
    title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(title)
    
    # 按钮示例
    btn1 = GlassButton("示例按钮1")
    btn2 = GlassButton(
        text="示例按钮2",
        clicked_color="rgba(255, 100, 150, 0.5)"
    )
    btn3 = ToggleGlassButton("切换按钮示例")
    
    layout.addWidget(btn1)
    layout.addWidget(btn2)
    layout.addWidget(btn3)
    layout.addStretch()
    
    return demo_panel

# ==============================
# 库信息
# ==============================

def library_info():
    """显示库信息"""
    info = {
        "name": "Glass Button Library",
        "version": "1.0.0",
        "description": "透明玻璃效果按钮库",
        "author": "Your Name",
        "classes": ["GlassButton", "ToggleGlassButton"],
        "functions": ["show_example", "show_quick_start", "create_button_demo", "library_info"]
    }
    return info

def print_library_info():
    """打印库信息到控制台"""
    info = library_info()
    print("=" * 50)
    print(f"库名称: {info['name']}")
    print(f"版本: {info['version']}")
    print(f"描述: {info['description']}")
    print(f"作者: {info['author']}")
    print(f"可用类: {', '.join(info['classes'])}")
    print(f"可用函数: {', '.join(info['functions'])}")
    print("=" * 50)
    print("使用方法:")
    print("  from glass_button_lib import GlassButton, ToggleGlassButton")
    print("  from glass_button_lib import show_example  # 显示示例窗口")
    print("  show_example()  # 运行示例")


# ==============================
# 直接运行库时的示例
# ==============================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="玻璃按钮库示例")
    parser.add_argument("--example", action="store_true", help="运行完整示例")
    parser.add_argument("--quick", action="store_true", help="运行快速开始示例")
    parser.add_argument("--info", action="store_true", help="显示库信息")
    
    args = parser.parse_args()
    
    if args.info:
        print_library_info()
    elif args.quick:
        show_quick_start()
    else:
        # 默认运行完整示例
        show_example()