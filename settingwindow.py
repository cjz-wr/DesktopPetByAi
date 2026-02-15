import sys
import json, os
from PyQt6.QtWidgets import (QApplication, QStackedWidget, QDialog, QFontDialog, QStyle, QButtonGroup, 
                            QFrame, QVBoxLayout, QDoubleSpinBox, QSpinBox, QFileDialog, QTabBar, 
                            QHBoxLayout, QLabel, QPushButton, QWidget, QTabWidget, QScrollArea,
                            QTextEdit, QDialogButtonBox, QMessageBox, QSplitter, QMenu, QSystemTrayIcon, QComboBox, QLineEdit)

import zhipu as zhipu


# 导入拆分后的模块
from lib.chat_widget import ChatWidget, AIWorker
from lib.font_manager import FontManager
from lib.vertical_tab_widget import VerticalTabBar, VerticalTabWidget
from lib.custom_dialog import CustomDialog

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("主窗口")
        self.resize(350, 300)
        
        # 创建全局字体管理器
        self.font_manager = FontManager()
        
        layout = QVBoxLayout(self)
        btn = QPushButton("打开自定义弹窗")
        btn.clicked.connect(self.show_custom_dialog)
        
        # 注册按钮到字体管理器
        self.font_manager.register_widget(btn)
        
        layout.addWidget(btn)
        
        # 添加说明标签
        info_label = QLabel("点击按钮打开设置窗口，在设置标签页中调整图片透明度和亮度可实时预览效果")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

    def show_custom_dialog(self):
        # 将字体管理器传递给对话框
        dialog = CustomDialog(font_manager=self.font_manager)
        dialog.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())