'''
lib.right_click_menu 的 Docstring
描述：
该模块实现了一个右键菜单，用于显示聊天对话框、打开设置窗口、显示帮助和关于信息。
右键菜单的显示和隐藏由鼠标点击事件触发，菜单项的点击事件由菜单项的点击事件触发。
右键菜单的布局使用QVBoxLayout，菜单项使用QAction。右键菜单的样式使用CSS样式表，菜单项的样式使用QSS样式表。
右键菜单的图标使用QIcon，菜单项的图标使用QIcon。右键菜单的图标和菜单项的图标都使用svg格式的图标
'''

import json
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QTextEdit, QFrame,
 QToolButton, QGridLayout
)
from PyQt6.QtGui import  QColor,  QPainter, QPixmap
from PyQt6.QtCore import Qt, QPoint,  pyqtSignal, QTimer
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QPainterPath
# from lib.food_manager import FoodVerification
from stegano import lsb
import lib.LogManager as LogManager
import logging


# 为了保持向后兼容，将旧的函数包装到新模块中
def create_default_recipes_if_not_exists():
    """保持向后兼容性的函数，不需要实际实现"""
    pass


class RecipeButton(QToolButton):
    def __init__(self, food_folder="outfood"):
        super().__init__()
        self.food_folder = food_folder
        self.recipe_popup = None
        self.setFixedSize(60, 60)
        self.setText("食谱")
        
        # 设置按钮样式
        self.setStyleSheet("""
            QToolButton {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                                  stop: 0 #ffffff, stop: 1 #f0f0f0);
                border-radius: 30px;
                border: 2px solid #4CAF50;
                color: #333;
                font-weight: bold;
                font-size: 11px;
                text-align: center;
            }
            QToolButton:hover {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                                  stop: 0 #f0f0f0, stop: 1 #e0e0e0);
                border: 2px solid #45a049;
            }
            QToolButton:pressed {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                                  stop: 0 #e0e0e0, stop: 1 #d0d0d0);
            }
        """)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setXOffset(0)
        shadow.setYOffset(3)
        self.setGraphicsEffect(shadow)
        
        self.setMouseTracking(True)
        
    def enterEvent(self, event):
        """鼠标进入按钮时显示食谱弹窗"""
        if not self.recipe_popup:
            self.recipe_popup = RecipePopup(self.food_folder)
        
        # 计算弹窗位置，显示在按钮旁边
        pos = self.mapToGlobal(QPoint(0, 0))
        # 尝试显示在右侧，如果超出屏幕则显示在左侧
        from PyQt6.QtWidgets import QApplication
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        popup_right_edge = pos.x() + self.width() + self.recipe_popup.width()
        
        if popup_right_edge > screen_geometry.right():
            # 弹窗显示在按钮左侧
            popup_x = pos.x() - self.recipe_popup.width()
        else:
            # 弹窗显示在按钮右侧
            popup_x = pos.x() + self.width()
            
        # 确保弹窗垂直位置与按钮对齐
        popup_y = pos.y()
        
        # 确保弹窗不会超出屏幕顶部
        if popup_y < 0:
            popup_y = 0
            
        self.recipe_popup.move(popup_x, popup_y)
        self.recipe_popup.show()
        
    def mousePressEvent(self, event):
        """处理鼠标点击事件，隐藏弹窗"""
        if self.recipe_popup:
            if self.recipe_popup.isVisible():
                self.recipe_popup.hide()
            else:
                # 如果弹窗被隐藏了，重新显示它
                pos = self.mapToGlobal(QPoint(0, 0))
                # 重新计算位置
                from PyQt6.QtWidgets import QApplication
                screen_geometry = QApplication.primaryScreen().availableGeometry()
                popup_right_edge = pos.x() + self.width() + self.recipe_popup.width()
                
                if popup_right_edge > screen_geometry.right():
                    # 弹窗显示在按钮左侧
                    popup_x = pos.x() - self.recipe_popup.width()
                else:
                    # 弹窗显示在按钮右侧
                    popup_x = pos.x() + self.width()
                    
                popup_y = pos.y()
                
                if popup_y < 0:
                    popup_y = 0
                    
                self.recipe_popup.move(popup_x, popup_y)
                self.recipe_popup.show()
        # 调用父类的事件处理
        super().mousePressEvent(event)


class RecipePopup(QWidget):
    def __init__(self, food_folder="outfood", parent=None):
        super().__init__(parent)
        self.food_folder = food_folder # 设置默认的图片文件夹
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(300, 400)
        self.setMaximumSize(300, 500)
        
        # 创建一个定时器，用于在没有鼠标活动时自动隐藏窗口
        self.auto_hide_timer = QTimer()
        self.auto_hide_timer.setSingleShot(True)
        self.auto_hide_timer.timeout.connect(self.hide)
        
        self.setup_ui()
        self.hide()  # 初始化时隐藏窗口
    
    def show(self):
        """重写show方法，添加定时器逻辑"""
        if not self.isVisible():  # 只有在不可见时才显示
            super().show()
            # 启动定时器，2秒后自动隐藏
            self.auto_hide_timer.start(2000)
        
    def enterEvent(self, event):
        """鼠标进入窗口时停止定时器"""
        super().enterEvent(event)
        if self.auto_hide_timer.isActive():
            self.auto_hide_timer.stop()
        
    def leaveEvent(self, event):
        """鼠标离开窗口时启动定时器"""
        super().leaveEvent(event)
        self.auto_hide_timer.start(2000)
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # 圆角矩形窗口容器
        container = QWidget()
        container.setObjectName("container")
        container.setStyleSheet("""
            QWidget#container {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                                  stop: 0 #ffffff, stop: 1 #f8f8f8);
                border-radius: 20px;
                border: 2px solid #4CAF50;
            }
        """)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(15, 15, 15, 15)
        container_layout.setSpacing(10)
        
        # 标题
        title_label = QLabel("美食图片")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2e7d32;
                margin-bottom: 10px;
                border-bottom: 2px solid #e0e0e0;
                padding-bottom: 8px;
            }
        """)
        container_layout.addWidget(title_label)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
                border-radius: 10px;
            }
            QScrollBar:vertical {
                width: 10px;
                background-color: transparent;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #c5e1a5;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a5d6a7;
            }
        """)
        container_layout.addWidget(scroll_area)
        
        # 图片内容容器
        content_widget = QWidget()
        content_layout = QGridLayout(content_widget)
        content_layout.setContentsMargins(5, 5, 5, 5)
        content_layout.setSpacing(10)
        content_widget.setStyleSheet("background-color: transparent;")
        
        # 加载food文件夹中的图片
        self.load_food_images(content_layout)
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(container)
        self.setLayout(layout)
    
    def load_food_images(self, layout):
        """从food文件夹加载并显示图片"""
        if not os.path.exists(self.food_folder):
            # 如果outfood文件夹不存在，显示提示信息
            label = QLabel(f"文件夹 '{self.food_folder}' 不存在")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    color: #e53935;
                    padding: 20px;
                }
            """)
            layout.addWidget(label)
            return
        
        # 获取food文件夹中的所有图片文件
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
        image_files = []
        
        for file in os.listdir(self.food_folder):
            file_ext = os.path.splitext(file)[1].lower()
            if file_ext in image_extensions:
                image_files.append(os.path.join(self.food_folder, file))
        
        if not image_files:
            # 如果没有找到图片，显示提示信息
            label = QLabel(f"在 '{self.food_folder}' 文件夹中未找到图片文件")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    color: #e53935;
                    padding: 20px;
                }
            """)
            layout.addWidget(label)
            return
        
        # 按单列布局添加图片
        row = 0
        for image_path in image_files:
            # 创建可点击的图片标签
            image_label = ClickableLabel()
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            image_label.setScaledContents(True)
            image_label.setFixedSize(180, 150)  # 设置固定大小，适合单列显示，尺寸更小
            image_label.setStyleSheet("""
                QLabel {
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    background-color: #f9f9f9;
                    padding: 5px;
                }
            """)
            
            # 加载并缩放图片
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    180, 150, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                image_label.setPixmap(scaled_pixmap)
            else:
                # 如果图片加载失败，显示错误信息
                image_label.setText("图片加载失败")
                image_label.setStyleSheet("""
                    QLabel {
                        border: 1px solid #ddd;
                        border-radius: 8px;
                        background-color: #f9f9f9;
                        padding: 5px;
                        color: #e53935;
                        font-size: 12px;
                    }
                """)
            
            # 连接点击事件
            image_label.clicked.connect(lambda path=image_path: self.show_image_detail(path))
            
            # 添加到布局
            layout.addWidget(image_label, row, 0)  # 单列布局，列索引始终为0
            
            # 更新行索引
            row += 1
    
    def show_image_detail(self, image_path):
        """显示图片详情窗口"""
        # 检查是否已经有详情窗口打开
        for child in self.children():
            if isinstance(child, ImageDetailWindow):
                child.close()
        
        # 创建新的详情窗口
        detail_window = ImageDetailWindow(image_path, self)
        
        # 计算窗口位置，使其出现在主窗口旁边
        parent_pos = self.pos()
        detail_window.move(parent_pos.x() + self.width() + 10, parent_pos.y())
        
        detail_window.show()

    def paintEvent(self, event):
        """重写绘制事件以创建圆角矩形窗口"""
        # 创建圆角矩形路径
        path = QPainterPath()
        rect = self.rect().adjusted(10, 10, -10, -10)
        # path.addRoundedRect(rect, 20, 20)  # 使用较小半径创建圆角矩形
        
        # 创建画家并启用抗锯齿
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 设置裁剪路径，确保所有子控件都在圆角区域内显示
        painter.setClipPath(path)
        
        # 绘制背景
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)


class ImageDetailWindow(QWidget):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)

        LogManager.init_logging()
        self.logger = logging.getLogger(__name__)

        self.image_path = image_path
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowTitleHint)
        self.setWindowTitle("食物详情")
        self.setFixedSize(400, 500)
        
        # 设置窗口样式
        self.setStyleSheet("""
            QWidget {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                                                 stop: 0 #ffffff, stop: 1 #f0f0f0);
                border-radius: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        

        # 图片名称
        image_name = os.path.basename(image_path)
        #加载食物
        try:
            data = lsb.reveal(f"./{image_path}")
            data = json.loads(data)
        except IndexError:
            data = {
                "FoodName":"未知食物", #食物名称
                "FoodDescription":"无描述", #食物描述
                "FoodCalories":0, #食物热量
                "FoodWater":0, #食物水分
            }

        name_label = QLabel(f"食物名称: {data['FoodName']}")
        name_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2e7d32;
                padding: 5px;
            }
        """)
        layout.addWidget(name_label)
        
        # 图片预览
        image_preview = QLabel()
        image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_preview.setFixedSize(300, 200)
        image_preview.setStyleSheet("""
            QLabel {
                border: 1px solid #ddd;
                background-color: white;
                border-radius: 8px;
                padding: 5px;
            }
        """)
        
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                300, 200, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            image_preview.setPixmap(scaled_pixmap)
        else:
            image_preview.setText("食物加载失败")
        layout.addWidget(image_preview)
        
        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #ccc;")
        layout.addWidget(line)
        
        # 详细信息标签
        info_label = QLabel("食物详细信息:")
        info_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #555;
                padding: 5px;
            }
        """)
        layout.addWidget(info_label)
        
        # 详细信息内容
        detail_text = QTextEdit()
        # print(image_path)
        self.logger.debug(image_path)
        
        detail_text.setReadOnly(True)
        detail_text.setPlainText(f"食物外观:{data['FoodDescription']}"+"\n"+f"食物热量:{data['FoodCalories']}"+f"\n食物水分:{data['FoodWater']}")  # 用xxxx代替详细信息
        detail_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                background-color: white;
                font-size: 13px;
                color: black;
            }
        """)
        layout.addWidget(detail_text)
        
        self.setLayout(layout)


class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

