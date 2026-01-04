import sys
import json, os
from PyQt6.QtWidgets import (QApplication, QStackedWidget, QDialog, QFontDialog, QStyle, QButtonGroup, 
                            QFrame, QVBoxLayout, QDoubleSpinBox, QSpinBox, QFileDialog, QTabBar, 
                            QHBoxLayout, QLabel, QPushButton, QWidget, QTabWidget, QScrollArea,
                            QTextEdit, QDialogButtonBox, QMessageBox, QSplitter, QMenu, QSystemTrayIcon, QComboBox, QLineEdit)
from PyQt6.QtCore import Qt, QPoint, QSize, QRectF, pyqtSignal, QObject, QRect, QThread
from PyQt6.QtGui import (QIcon, QMouseEvent, QPainter, QImage, QPixmap, QFontMetrics, QPen, QColor, 
                         QPainterPath, QFont, QTextCursor, QTextCharFormat, QMovie)

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
        from lib.vertical_tab_widget import VerticalTabWidget
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