from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import sys

class AdvancedChatWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # 创建文本编辑框
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)  # 设为只读，类似聊天记录
        
        # 输入区域
        self.input_edit = QTextEdit()
        self.input_edit.setMaximumHeight(100)
        
        # 按钮
        btn_send = QPushButton("发送")
        btn_send.clicked.connect(self.send_message)
        
        btn_add_image = QPushButton("添加图片")
        btn_add_image.clicked.connect(self.insert_image_to_input)
        
        # 布局
        layout.addWidget(QLabel("聊天记录:"))
        layout.addWidget(self.text_edit)
        layout.addWidget(QLabel("输入消息:"))
        layout.addWidget(self.input_edit)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(btn_add_image)
        button_layout.addWidget(btn_send)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.setWindowTitle("高级聊天窗口")
        self.setGeometry(300, 300, 600, 500)
    
    def insert_image_to_input(self):
        """在输入框中插入图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            # 使用HTML方式插入图片
            cursor = self.input_edit.textCursor()
            cursor.insertHtml(f'<img src="{file_path}" width="100">')
    
    def send_message(self):
        """发送消息到聊天窗口"""
        # 获取输入内容
        cursor = self.input_edit.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        html_content = cursor.selection().toHtml()
        
        # 添加时间戳和格式
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        formatted_message = f"""
        <div style='background-color: #E8F5E8; border-radius: 10px; padding: 8px; margin: 5px;'>
            <div style='font-weight: bold; color: #2E8B57;'>
                我 ({timestamp}):
            </div>
            <div style='color: #000000;'>
                {html_content}
            </div>
        </div>
        """
        
        # 添加到聊天记录
        self.text_edit.append(formatted_message)
        
        # 清空输入框
        self.input_edit.clear()
        
        # 滚动到底部
        scrollbar = self.text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdvancedChatWindow()
    window.show()
    sys.exit(app.exec())