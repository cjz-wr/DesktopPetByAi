import sys
import json, os
from PyQt6.QtWidgets import (QApplication, QStackedWidget, QDialog, QFontDialog, QStyle, QButtonGroup, 
                            QFrame, QVBoxLayout, QDoubleSpinBox, QSpinBox, QFileDialog, QTabBar, 
                            QHBoxLayout, QLabel, QPushButton, QWidget, QTabWidget, QScrollArea,
                            QTextEdit, QDialogButtonBox, QMessageBox, QSplitter, QMenu, QSystemTrayIcon, QComboBox, QLineEdit)
from PyQt6.QtCore import Qt, QPoint, QSize, QRectF, pyqtSignal, QObject, QRect, QThread
from PyQt6.QtGui import (QIcon, QMouseEvent, QPainter, QImage, QPixmap, QFontMetrics, QPen, QColor, 
                         QPainterPath, QFont, QTextCursor, QTextCharFormat, QMovie)

class FontManager(QObject):
    font_changed_signal = pyqtSignal(QFont)

    def __init__(self):
        super().__init__()
        self.font = QFont("SimSun", 12)  # 默认字体
        self.widgets = []  # 存储需要同步字体的所有控件

    def register_widget(self, widget):
        """注册一个需要同步字体的控件"""
        if widget not in self.widgets:
            self.widgets.append(widget)
            widget.setFont(self.font)  # 初始化字体
            return True
        return False

    def change_font(self, font):
        """更改字体并通知所有注册的控件"""
        self.font = font
        self.font_changed_signal.emit(font)

    def load_from_dict(self, font_dict):
        """从字典恢复字体"""
        font = QFont()
        font.setFamily(font_dict.get("family", "SimSun"))
        point_size = font_dict.get("pointSize")
        if point_size and point_size > 0:
            font.setPointSize(point_size)
        else:
            font.setPointSize(12)  # 默认字体大小
        font.setBold(font_dict.get("bold", False))
        font.setItalic(font_dict.get("italic", False))
        font.setUnderline(font_dict.get("underline", False))
        weight = font_dict.get("weight", QFont.Weight.Normal)
        font.setWeight(weight)
        self.change_font(font)

    def to_dict(self):
        """将当前字体转为字典用于保存"""
        point_size = self.font.pointSize()
        # 确保pointSize是正数，如果是负数则使用默认值12
        if point_size <= 0:
            point_size = 12
        return {
            "family": self.font.family(),
            "pointSize": point_size,
            "bold": self.font.bold(),
            "italic": self.font.italic(),
            "underline": self.font.underline(),
            "weight": self.font.weight(),
        }

    def update_registered_widgets(self, new_font):
        """更新所有已注册控件的字体"""
        for widget in self.widgets:
            widget.setFont(new_font)