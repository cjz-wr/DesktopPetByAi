from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt6.QtCore import QTimer, QPropertyAnimation, QAbstractAnimation
from PyQt6.QtCore import Qt


class TempMessageBox(QWidget):
    """
    临时消息框，会在一段时间后自动消失，并带有逐渐透明的效果
    """
    def __init__(self, message, duration=2000, fade_duration=1000, parent=None):
        super().__init__(parent)
        
        # 设置基本窗口属性
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        
        # 设置初始透明度
        self.setWindowOpacity(1.0)
        
        # 创建主标签
        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                background-color: rgb(70, 70, 70);
                color: white;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        
        # 创建布局
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.setContentsMargins(2, 2, 2, 2)  # 小的边距
        self.setLayout(layout)
        
        # 保存参数
        self.duration = duration  # 消息显示时长
        self.fade_duration = fade_duration  # 淡出时长
        
        # 调整窗口大小以适应内容
        self.adjustSize()
        
        # 启动计时器开始消失过程
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.start_fade_out)
        self.timer.start(duration)
        
        # 创建透明度动画
        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation.setDuration(fade_duration)
        self.opacity_animation.setStartValue(1.0)
        self.opacity_animation.setEndValue(0.0)
        self.opacity_animation.finished.connect(self.close)

    def start_fade_out(self):
        """
        开始淡出效果
        """
        self.timer.stop()
        self.opacity_animation.start()

    def show_at(self, x, y):
        """
        在指定位置显示消息框
        """
        self.move(int(x), int(y))
        self.show()
        # 确保消息框在最前面
        self.raise_()
        self.activateWindow()


def show_temp_message(parent, message, duration=1500, fade_duration=1000):
    """
    在父窗口附近显示临时消息
    duration: 消失时间
    fade_duration: 淡出时间
    """
    msg_box = TempMessageBox(message, duration, fade_duration, parent)
    
    # 计算显示位置 - 显示在父窗口中心偏上的位置
    if parent:
        parent_geo = parent.geometry()
        msg_x = parent_geo.x() + (parent_geo.width() - msg_box.width()) // 2
        msg_y = parent_geo.y() + (parent_geo.height() - msg_box.height()) // 3
    else:
        # 如果没有父窗口，居中显示
        screen = QApplication.primaryScreen().availableGeometry()
        msg_x = screen.center().x() - msg_box.width() // 2
        msg_y = screen.center().y() - msg_box.height() // 2
    
    msg_box.show_at(msg_x, msg_y)
    return msg_box