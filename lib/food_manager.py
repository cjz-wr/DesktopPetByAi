'''
食物管理模块
该模块实现了食物信息的嵌入/提取、食物图片展示以及食物对宠物状态的影响等功能
'''


from PyQt6.QtGui import  QColor, QPainter, QPixmap
from PyQt6.QtCore import Qt, QPoint,  pyqtSignal,  QTimer
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QPainterPath
import os  # 添加os模块导入
import re  # 添加正则表达式导入
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QTextEdit, QFrame,
    QHBoxLayout, QToolButton, QGridLayout
)
from stegano import lsb
import json

import lib.LogManager as LogManager
import logging

# 预编译正则表达式以提高性能
TIME_FORMAT_PATTERN = re.compile(r'^(\d+[smhd])+$')
TIME_UNIT_PATTERN = re.compile(r'(\d+)([smhd])')

class FoodVerification:
    '''
    食物信息验证类
    用于给食物图片写入信息和读取信息
    '''
    
    @staticmethod
    def embed_food_info(image_path, food_name, food_description, food_calories, food_water, food_time, output_path, food_type=None):
        """
        将食物信息嵌入到图片中
        :param image_path: 原始图片路径
        :param food_name: 食物名称
        :param food_description: 食物描述
        :param food_calories: 食物热量
        :param food_water: 食物水分
        :param food_time: 食用时间（格式：30s, 10m, 2h, 1d）
        :param output_path: 输出图片路径
        :param food_type: 食物类型
        """
        data = {
            "FoodName": food_name,
            "FoodDescription": food_description,
            "FoodCalories": food_calories,
            "FoodWater": food_water,
            "FoodTime": food_time,
            "FoodType": food_type if food_type is not None else "未知类型"
        }
        
        try:
            # 将数据写入图片
            lsb.hide(image_path, json.dumps(data)).save(output_path)
            return True, "食物信息嵌入成功"
        except Exception as e:
            return False, f"食物信息嵌入失败: {str(e)}"
    
    @staticmethod
    def extract_food_info(image_path):
        """
        从图片中提取食物信息
        :param image_path: 图片路径
        :return: (success, data dict)
        """
        try:
            data_str = lsb.reveal(image_path)
            if data_str:
                data = json.loads(data_str)
                # 确保返回的数据包含FoodType字段
                if "FoodType" not in data:
                    data["FoodType"] = "未知类型"
                return True, data
            else:
                return False, {"error": "未找到嵌入的食物信息"}
        except IndexError:
            return False, {"error": "未找到嵌入的食物信息"}
        except Exception as e:
            return False, {"error": f"读取食物信息失败: {str(e)}"}
    
    @staticmethod
    def create_default_food_info_if_missing(image_path, output_path):
        """
        如果图片中没有食物信息，则创建默认的食物信息
        :param image_path: 原始图片路径
        :param output_path: 输出图片路径
        :return: (success, message)
        """
        # 首先尝试提取食物信息
        success, data = FoodVerification.extract_food_info(image_path)
        
        if success:
            # 如果已经存在食物信息，则不需要创建默认值
            return False, "图片中已有食物信息，无需创建默认值"
        else:
            # 图片中没有食物信息，创建默认值
            default_data = {
                "FoodName": "未命名食物",
                "FoodDescription": "这是一个未命名的食物",
                "FoodCalories": 100,
                "FoodWater": 50,
                "FoodTime": "10m",
                "FoodType": "未知类型"
            }
            
            try:
                # 将默认数据写入图片
                lsb.hide(image_path, json.dumps(default_data)).save(output_path)
                return True, "已创建默认食物信息"
            except Exception as e:
                return False, f"创建默认食物信息失败: {str(e)}"
    
    @staticmethod
    def validate_food_time_format(food_time):
        """
        验证食用时间格式是否正确 (s-秒, m-分, h-时, d-天)
        支持格式：30s, 10m, 2h, 1d, 1m30s, 2h15m, 1d12h等复合格式
        :param food_time: 食用时间字符串，例如 "30s", "10m", "2h", "1d", "1m30s", "2h15m"
        :return: (is_valid, error_message)
        """
        if not food_time:
            return True, "食用时间为可选字段"
        
        if not isinstance(food_time, str):
            return False, "食用时间必须是字符串"
        
        # 使用预编译的正则表达式验证格式
        if not TIME_FORMAT_PATTERN.match(food_time):
            return False, "食用时间格式不正确，支持格式如: 30s, 10m, 2h, 1d, 1m30s, 2h15m, 1d12h等"
        
        # 检查单位是否重复（如 1m30m 是不允许的）
        units = set(re.findall(r'[smhd]', food_time))  # 使用set去重
        if len(units) != len(re.findall(r'[smhd]', food_time)):
            return False, "食用时间单位不能重复，例如不能同时有多个s、m、h或d"
        
        # 检查每个数值部分
        numbers = re.findall(r'\d+', food_time)
        for num_str in numbers:
            try:
                value = int(num_str)
                if value <= 0:
                    return False, "食用时间数值必须大于0"
            except ValueError:
                return False, "食用时间格式不正确，应为数字加单位(s/m/h/d)的组合"
        
        return True, ""
    
    @staticmethod
    def parse_food_time_to_seconds(food_time):
        """
        将食用时间字符串转换为秒数
        支持格式：30s, 10m, 2h, 1d, 1m30s, 2h15m, 1d12h等复合格式
        :param food_time: 食用时间字符串，例如 "30s", "10m", "2h", "1d", "1m30s", "2h15m"
        :return: 秒数
        """
        if not food_time:
            return 0
        
        total_seconds = 0
        
        # 使用预编译的正则表达式提取数字和单位对
        matches = TIME_UNIT_PATTERN.findall(food_time)
        
        for value_str, unit in matches:
            value = int(value_str)
            if unit == 's':
                total_seconds += value
            elif unit == 'm':
                total_seconds += value * 60
            elif unit == 'h':
                total_seconds += value * 3600
            elif unit == 'd':
                total_seconds += value * 86400
        
        return total_seconds


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

        LogManager.init_logging()
        self.logger = logging.getLogger(__name__)

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
        
        # 创建一个水平布局来容纳标题和按钮
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)
        
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
        title_layout.addWidget(title_label)
        
        # 打开文件夹按钮
        folder_button = QToolButton()
        folder_button.setText("🍽️")
        folder_button.setToolTip("打开outfood文件夹")
        folder_button.setStyleSheet("""
            QToolButton {
                font-size: 16px;
                border: 1px solid #4CAF50;
                border-radius: 10px;
                padding: 5px;
                background-color: #f0f0f0;
            }
            QToolButton:hover {
                background-color: #e0f0e0;
            }
        """)
        folder_button.clicked.connect(self.open_food_folder)
        title_layout.addWidget(folder_button)
        
        container_layout.addLayout(title_layout)
        
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

    def open_food_folder(self):
        """打开outfood文件夹"""
        import subprocess
        import platform
        
        # 确保文件夹存在
        if not os.path.exists(self.food_folder):
            # 如果不存在，创建文件夹
            try:
                os.makedirs(self.food_folder, exist_ok=True)
            except OSError as e:
                self.logger.error(f"创建文件夹失败: {e}")
                return
        
        # 根据操作系统打开文件夹
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(self.food_folder)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", self.food_folder])
            else:  # Linux
                subprocess.run(["xdg-open", self.food_folder])
        except Exception as e:
            self.logger.error(f"打开文件夹失败: {e}")

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
        # 加载食物信息
        success, data = FoodVerification.extract_food_info(image_path)
        if not success:
            data = {
                "FoodName": "未知食物",
                "FoodDescription": "无描述",
                "FoodCalories": 0,
                "FoodWater": 0,
                "FoodTime": "无"
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
        detail_text.setReadOnly(True)
        detail_text.setPlainText(
            f"食物外观: {data['FoodDescription']}\n"
            f"食物热量: {data['FoodCalories']}\n"
            f"食物水分: {data['FoodWater']}\n"
            f"食用时间: {data.get('FoodTime', '无')}"
        )
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





def feed_pet_with_food(desktop_pet, food_image_path):
    """
    用食物喂养宠物，更新宠物状态
    :param desktop_pet: 桌面宠物对象
    :param food_image_path: 食物图片路径
    :return: (success, message, food_time_in_seconds)
    """

    LogManager.init_logging()
    logger = logging.getLogger(__name__)

    # 检查是否正在进食
    if hasattr(desktop_pet, 'eating_timer') and desktop_pet.eating_timer.is_feeding():
        warning_msg = "宠物正在进食，请等待当前食物吃完后再喂食！"
        logger.debug(warning_msg)
        from lib.temp_message_box import show_temp_message
        show_temp_message(desktop_pet, warning_msg)
        return False, warning_msg, 0
    
    success, food_data = FoodVerification.extract_food_info(food_image_path)
    
    if success:
        # 获取食物类型
        food_type = food_data.get("FoodType", "未知类型")
        calories = int(food_data.get("FoodCalories", 0))
        water = int(food_data.get("FoodWater", 0))
        food_time = food_data.get("FoodTime", "")
        
        # 如果是饮品类型，即使热量已满也可以增加水分
        if food_type == "饮品":
            if desktop_pet.pet_stats_manager.pet_hunger >= 100 and desktop_pet.pet_stats_manager.pet_water >= 100:
                warning_msg = "宠物的饥饿度和水分都已经满了，不能再喝了！"
                logger.debug(warning_msg)
                from lib.temp_message_box import show_temp_message
                show_temp_message(desktop_pet, warning_msg)
                return False, warning_msg, 0
        else:
            # 对于非饮品类食物，检查饥饿度是否已经为100
            if hasattr(desktop_pet.pet_stats_manager, 'pet_hunger') and desktop_pet.pet_stats_manager.pet_hunger >= 100:
                warning_msg = "宠物已经很饱了，不能再吃啦！"
                logger.debug(warning_msg)
                from lib.temp_message_box import show_temp_message
                show_temp_message(desktop_pet, warning_msg)
                return False, warning_msg, 0
        
        # 保存食物的营养信息，以便中断进食时使用
        desktop_pet.current_food_calories = calories
        desktop_pet.current_food_water = water
        
        # 不立即更新宠物状态，而是等到进食完成时再更新
        # desktop_pet.update_pet_stats(calories, water)
        
        # 将食用时间转换为秒数
        food_time_seconds = FoodVerification.parse_food_time_to_seconds(food_time)
        
        message = f"开始进食！总共增加{calories}点饥饿度和{water}点水分"

       

        if food_time:
            message += f"，食用时间：{food_time}"
            
        # 显示临时消息
        from lib.temp_message_box import show_temp_message
        show_temp_message(desktop_pet, message)
        
        # 如果食物有进食时间，则启动倒计时，传递食物营养信息
        if food_time_seconds > 0:
            desktop_pet.eating_timer.start_feeding(food_time_seconds, calories, water)
        
        return True, message, food_time_seconds
    else:
        error_msg = "无法识别食物信息"
        # 显示错误消息
        from lib.temp_message_box import show_temp_message
        show_temp_message(desktop_pet, error_msg)
        return False, error_msg, 0
