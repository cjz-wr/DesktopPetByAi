import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QProgressBar, QLCDNumber, QBoxLayout, QPushButton
)
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtCore import Qt, QTimer, QDateTime
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from datetime import datetime, timedelta


class StatBarWindow(QWidget):
    """显示宠物饥饿度和水量的进度条窗口"""
    def __init__(self, hunger=50, water=50, eating_state=None, parent=None):
        super().__init__(parent)
        # 修改窗口标志，移除可能引起问题的标志
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)  # 修改为False避免Windows上的问题
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)  # 添加此属性
        self.setFixedSize(260, 250)  # 增加窗口高度以容纳中断按钮
        
        # 创建容器widget来承载内容
        container = QWidget(self)
        container.setGeometry(0, 0, 260, 250) # 设置容器大小
        container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                          stop: 0 #ffffff, stop: 1 #f5f5f5);
                border-radius: 20px; /* 增加圆角半径 */
                border: 1px solid #e0e0e0;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setSpacing(5)  # 调整间距
        layout.setContentsMargins(10, 10, 10, 10)  # 增加边距
        
        # 饥饿度进度条
        hunger_container = QWidget()
        hunger_container_layout = QVBoxLayout(hunger_container)
        hunger_container_layout.setContentsMargins(0, 0, 0, 0) # 设置内边距为0
        
        hunger_label = QLabel(" 🐾 饥饿度")
        hunger_label.setStyleSheet("""
            color: #e53935;
            font-weight: bold;
            font-size: 15px;  /* 稍微增大字体 */
            padding: 6px; /* 增加内边距 */
            border-bottom: 2px solid #ffcdd2;
        """)
        
        self.hunger_bar = QProgressBar()
        self.hunger_bar.setRange(0, 1000)  # 修改范围到0-1000，表示0.0-100.0
        self.hunger_bar.setValue(int(hunger * 10))  # 饥饿度乘以10
        self.hunger_bar.setTextVisible(True)
        self.hunger_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hunger_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                background-color: #f5f5f5;
                height: 10px;  /* 减小了进度条高度 */
                text-align: center;
                font-weight: bold;
                color: #333;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, 
                                                 stop: 0 #ff7675, stop: 1 #e53935);
                border-radius: 8px;
            }
        """)
        
        hunger_container_layout.addWidget(hunger_label)
        hunger_container_layout.addWidget(self.hunger_bar)
        
        # 水量进度条
        water_container = QWidget()
        water_container_layout = QVBoxLayout(water_container)
        water_container_layout.setContentsMargins(0, 0, 0, 0)
        
        water_label = QLabel(" 💧 水量")
        water_label.setStyleSheet("""
            color: #1e88e5;
            font-weight: bold;
            font-size: 15px;  /* 稍微增大字体 */
            padding: 6px;
            border-bottom: 2px solid #bbdefb; /* 增加下边框 */
        """)
        
        self.water_bar = QProgressBar()
        self.water_bar.setRange(0, 1000)  # 修改范围到0-1000，表示0.0-100.0
        self.water_bar.setValue(int(water * 10))  # 水量乘以10
        self.water_bar.setTextVisible(True)
        self.water_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.water_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                background-color: #f5f5f5;
                height: 10px;  /* 减小了进度条高度 */
                text-align: center;
                font-weight: bold;
                color: #333;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, 
                                                 stop: 0 #64b5f6, stop: 1 #1e88e5);
                border-radius: 8px;
            }
        """)
        
        water_container_layout.addWidget(water_label)
        water_container_layout.addWidget(self.water_bar)
        
        layout.addWidget(hunger_container)
        layout.addWidget(water_container)
        
        # 添加进食倒计时显示
        eating_container = QWidget()
        eating_container_layout = QVBoxLayout(eating_container)
        eating_container_layout.setContentsMargins(0, 0, 0, 0)
        
        eating_label = QLabel(" 🍽️ 未进食")
        eating_label.setStyleSheet("""
            color: #43a047;
            font-weight: bold;
            font-size: 15px;
            padding: 6px;
            border-bottom: 2px solid #c8e6c9;
        """)
        self.eating_lcd = QLCDNumber()
        self.eating_lcd.setDigitCount(8)
        self.eating_lcd.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        self.eating_lcd.setStyleSheet("""
            QLCDNumber {
                background-color: #f5f5f5;
                color: #43a047;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 5px;
            }
        """)
        self.eating_lcd.display("--:--:--")
        self.eating_lcd.hide()  # 默认隐藏，只有在进食时才显示
        
        # 创建中断进食按钮
        self.interrupt_button = QPushButton("中断进食")
        self.interrupt_button.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                                 stop: 0 #f44336, stop: 1 #d32f2f);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                                 stop: 0 #e57373, stop: 1 #b71c1c);
            }
            QPushButton:pressed {
                background-color: #d32f2f;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.interrupt_button.clicked.connect(self.interrupt_feeding)
        self.interrupt_button.hide()  # 默认隐藏，只有在进食时才显示
        
        eating_container_layout.addWidget(eating_label)
        eating_container_layout.addWidget(self.eating_lcd)
        eating_container_layout.addWidget(self.interrupt_button)
        layout.addWidget(eating_container)
        
        # 设置进食状态
        if eating_state:
            self.set_eating_state(eating_state)
        else:
            self.set_eating_state(None)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        self.setGraphicsEffect(shadow)

    def update_values(self, hunger, water):
        """更新进度条数值"""
        self.hunger_bar.setValue(int(hunger * 10))  # 饥饿度乘以10
        self.water_bar.setValue(int(water * 10))   # 水量乘以10
    
    def set_eating_state(self, eating_state):
        """设置进食状态显示"""
        if eating_state and eating_state.get('remaining_time', 0) > 0:
            self.eating_lcd.display(format_time(eating_state['remaining_time']))
            self.eating_lcd.show()
            self.interrupt_button.show()
        else:
            self.eating_lcd.hide()
            self.interrupt_button.hide()
    
    def update_eating_timer(self, remaining_time):
        """更新进食倒计时显示"""
        if remaining_time > 0:
            self.eating_lcd.display(format_time(remaining_time))
            self.eating_lcd.show()
            self.interrupt_button.show()
        else:
            self.eating_lcd.hide()
            self.interrupt_button.hide()
    
    def interrupt_feeding(self):
        """中断进食"""
        if self.parent():
            # 调用父窗口的中断进食方法
            self.parent().interrupt_feeding()
    
    def paintEvent(self, event):
        """重绘事件，确保背景透明"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)


def format_time(seconds):
    """格式化时间显示"""
    if seconds < 0:
        return "--:--:--"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"