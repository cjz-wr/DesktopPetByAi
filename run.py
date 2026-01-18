import sys
import os
# 添加当前目录到路径，确保模块可以被正确导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QLineEdit, 
    QPushButton, QVBoxLayout, QWidget, QMessageBox, QHBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from cryptography.fernet import Fernet


class PasswordWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app  # 保存应用实例
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('桌面宠物 - 登录')
        self.setFixedSize(400, 200)
        
        # 设置窗口居中
        self.center_window()
        
        # 创建中心窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 标题标签
        title_label = QLabel('桌面宠物系统')
        title_label.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 密码输入框
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText('请输入密码')
        self.password_input.setFont(QFont('Arial', 12))
        self.password_input.returnPressed.connect(self.check_password)  # 回车确认
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 取消按钮
        cancel_button = QPushButton('取消')
        cancel_button.clicked.connect(self.close)
        
        # 确认按钮
        confirm_button = QPushButton('确认')
        confirm_button.clicked.connect(self.check_password)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(confirm_button)
        
        # 添加组件到布局
        layout.addWidget(title_label)
        layout.addWidget(QLabel(''))  # 空标签作为间隔
        layout.addWidget(self.password_input)
        layout.addLayout(button_layout)
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QLabel {
                color: #333;
            }
            QLineEdit {
                padding: 10px;
                border: 2px solid #ccc;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
            QPushButton {
                padding: 8px 16px;
                font-size: 14px;
                border: none;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton#confirm_button {
                background-color: #4CAF50;
                color: white;
            }
            QPushButton#confirm_button:hover {
                background-color: #45a049;
            }
            QPushButton#cancel_button {
                background-color: #f44336;
                color: white;
            }
            QPushButton#cancel_button:hover {
                background-color: #d32f2f;
            }
        """)
        
        # 设置确认按钮样式
        confirm_button.setObjectName("confirm_button")
        cancel_button.setObjectName("cancel_button")
        
        # 默认焦点设置到密码框
        self.password_input.setFocus()

    def center_window(self):
        # 获取屏幕尺寸
        screen_geometry = self.screen().availableGeometry()
        window_geometry = self.geometry()
        
        # 计算居中位置
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2
        
        # 设置窗口位置
        self.move(x, y)
    
    #加密密码
    def encrypt_password(self, password: str) -> str:
        # 生成密钥
        key = Fernet.generate_key()
        fernet = Fernet(key)
        encrypted_password = fernet.encrypt(password.encode()).decode()
        try:
            self.save_key_passwd(key.decode(), encrypted_password)
            return encrypted_password
        except Exception as e:
            print(f"保存密钥和密码时出错: {str(e)}")
            raise e
        
    #解密密码
    def decrypt_password(self):
        try:
            with open('key_passwd.bin', 'rb') as f:
                # 读取密钥长度（4字节）
                key_length = int.from_bytes(f.read(4), byteorder='little')
                # 读取密钥
                key = f.read(key_length)
                # 读取加密密码
                encrypted_password = f.read()
            
            right_password = Fernet(key).decrypt(encrypted_password).decode()
            print(f"解密得到的密码: {right_password}")
            if right_password == "DSTPBABATE":
                return True
            else:
                return False
        except Exception as e:
            print(f"解密密码时出错: {str(e)}")
            return False
        
    #二进制存储密钥和密码
    def save_key_passwd(self, key: str, encrypted_password: str):
        with open('key_passwd.bin', 'wb') as f:
            # 将密钥和加密密码都转换为字节并写入
            key_bytes = key.encode('utf-8')
            encrypted_bytes = encrypted_password.encode('utf-8')
            
            # 写入密钥长度（4字节）+ 密钥 + 加密密码
            f.write(len(key_bytes).to_bytes(4, byteorder='little'))
            f.write(key_bytes)
            f.write(encrypted_bytes)

    #判断是否第一次进入程序
    def is_first_run(self):
        if not os.path.exists('key_passwd.bin'):
            return True
        else:
            return False

    def check_password(self):
        # 这里设置一个简单的密码，实际使用中可以更复杂或从配置文件读取
        correct_password = "DSTPBABATE"  # 可以修改为实际需要的密码
        print("检查密码中...")
        if self.is_first_run():
            entered_password = self.password_input.text()
            if entered_password == correct_password:
                # 密码正确，启动主程序
                self.start_main_app()
                #加密保存密码
                if not self.encrypt_password(entered_password):
                    QMessageBox.warning(self, '错误', '保存密码时出错，请重试！')
                    self.password_input.clear()
                    self.password_input.setFocus()
                else:
                    QMessageBox.information(self, '提示', '密码保存成功！')
            else:
                # 密码错误，显示提示
                QMessageBox.warning(self, '密码错误', '密码不正确，请重试！')
                self.password_input.clear()
                self.password_input.setFocus()
        else:
            if self.decrypt_password():
                # 密码正确，启动主程序
                self.start_main_app()
            else:
                # 密码错误，显示提示
                QMessageBox.warning(self, '文件错误', '请删除key_passwd.bin文件后重试！')
                self.password_input.clear()
                self.password_input.setFocus()

    def start_main_app(self):
        try:
            from main import DesktopPet
            # 创建桌面宠物实例
            self.pet = DesktopPet()
            self.pet.show()
            # 关闭密码窗口
            # self.close()
            #隐藏密码窗口
            self.hide()
        except ImportError as e:
            QMessageBox.critical(self, '错误', f'无法导入桌面宠物模块: {str(e)}')
            self.close()
        except Exception as e:
            QMessageBox.critical(self, '错误', f'启动桌面宠物失败: {str(e)}')
            self.close()


def main():
    app = QApplication(sys.argv)
    password_window = PasswordWindow(app)
    if password_window.is_first_run():
        password_window.show()
    else:
        if password_window.decrypt_password():
            password_window.start_main_app()
        else:
            QMessageBox.warning(password_window, '文件错误', '请删除key_passwd.bin文件后重试！')
        
    
    # 启动应用程序事件循环
    sys.exit(app.exec())


if __name__ == '__main__':
    main()