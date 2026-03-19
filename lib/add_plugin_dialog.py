"""
添加/编辑插件对话框
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLabel, QLineEdit, QTextEdit, QCheckBox, 
                             QPushButton, QMessageBox, QFrame)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

class AddPluginDialog(QDialog):
    """添加/编辑插件对话框"""
    
    def __init__(self, font_manager=None, parent=None, plugin_name=None, plugin_data=None):
        """
        初始化对话框
        
        Args:
            font_manager: 字体管理器
            parent: 父组件
            plugin_name (str): 编辑模式下的插件名称
            plugin_data (dict): 编辑模式下的插件数据
        """
        super().__init__(parent)
        self.font_manager = font_manager
        self.is_edit_mode = plugin_name is not None
        self.original_plugin_name = plugin_name
        
        self.setup_ui()
        self.setWindowIcon(QIcon("ico/ico.png"))  # 设置窗口图标
        
        # 如果是编辑模式，填充现有数据
        if self.is_edit_mode and plugin_data:
            self.populate_data(plugin_name, plugin_data)
    
    def setup_ui(self):
        """设置对话框UI"""
        self.setWindowTitle("添加插件" if not self.is_edit_mode else "编辑插件")
        self.setModal(True)
        self.resize(500, 600)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        # 标题
        title = "添加新插件" if not self.is_edit_mode else f"编辑插件: {self.original_plugin_name}"
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2F4F2F;
                padding: 10px;
            }
        """)
        main_layout.addWidget(title_label)
        
        # 表单区域
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: #f8fff8;
                border: 1px solid #e8f5e8;
                border-radius: 8px;
                padding: 15px;
                color: #2F4F2F;
            }
        """)
        
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # 插件名称
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("请输入插件名称（英文，如：get_weather）")
        self.name_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #B0E0E6;
                border-radius: 4px;
                font-size: 14px;
                color: #2F4F2F;
            }
            QLineEdit:focus {
                border-color: #3CB371;
            }
        """)
        form_layout.addRow("插件名称*:", self.name_edit)
        
        # 插件描述
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)
        self.desc_edit.setPlaceholderText("请输入插件的功能描述...")
        self.desc_edit.setStyleSheet("""
            QTextEdit {
                padding: 8px;
                border: 1px solid #B0E0E6;
                border-radius: 4px;
                font-size: 14px;
            }
            QTextEdit:focus {
                border-color: #3CB371;
            }
        """)
        form_layout.addRow("功能描述*:", self.desc_edit)
        
        # 执行格式
        self.format_edit = QLineEdit()
        self.format_edit.setPlaceholderText("请输入执行格式（如：[USESKILLS:GetWeather:GetWeather]）")
        self.format_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #B0E0E6;
                border-radius: 4px;
                font-size: 14px;
                font-family: Consolas, Monaco, monospace;
                color: #2F4F2F;
            }
            QLineEdit:focus {
                border-color: #3CB371;
            }
        """)
        form_layout.addRow("执行格式*:", self.format_edit)
        
        # 使用说明
        self.usage_edit = QTextEdit()
        self.usage_edit.setMaximumHeight(80)
        self.usage_edit.setPlaceholderText("请输入插件的使用说明...")
        self.usage_edit.setStyleSheet("""
            QTextEdit {
                padding: 8px;
                border: 1px solid #B0E0E6;
                border-radius: 4px;
                font-size: 14px;
            }
            QTextEdit:focus {
                border-color: #3CB371;
            }
        """)
        form_layout.addRow("使用说明*:", self.usage_edit)
        
        # 注意事项
        self.attention_edit = QTextEdit()
        self.attention_edit.setMaximumHeight(80)
        self.attention_edit.setPlaceholderText("请输入使用时需要注意的事项...")
        self.attention_edit.setStyleSheet("""
            QTextEdit {
                padding: 8px;
                border: 1px solid #B0E0E6;
                border-radius: 4px;
                font-size: 14px;
            }
            QTextEdit:focus {
                border-color: #3CB371;
            }
        """)
        form_layout.addRow("注意事项:", self.attention_edit)
        
        # AI可使用选项
        self.ai_use_checkbox = QCheckBox("允许AI自动使用此插件")
        self.ai_use_checkbox.setChecked(True)
        self.ai_use_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                color: #2F4F2F;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        form_layout.addRow("", self.ai_use_checkbox)
        
        # 详细信息选项
        self.detailed_checkbox = QCheckBox("提供详细信息")
        self.detailed_checkbox.setChecked(False)
        self.detailed_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                color: #2F4F2F;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        form_layout.addRow("", self.detailed_checkbox)
        
        # 外部插件选项
        self.external_plugin_checkbox = QCheckBox("标记为外部插件")
        self.external_plugin_checkbox.setChecked(False)
        self.external_plugin_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                color: #2F4F2F;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        form_layout.addRow("", self.external_plugin_checkbox)
        
        main_layout.addWidget(form_frame)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 取消按钮
        cancel_button = QPushButton("取消")
        cancel_button.setFixedSize(100, 35)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #CCCCCC;
                color: #333333;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #BBBBBB;
            }
            QPushButton:pressed {
                background-color: #AAAAAA;
            }
        """)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        button_layout.addStretch()
        
        # 确认按钮
        confirm_button = QPushButton("确认" if not self.is_edit_mode else "更新")
        confirm_button.setFixedSize(100, 35)
        confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        confirm_button.clicked.connect(self.accept)
        button_layout.addWidget(confirm_button)
        
        main_layout.addLayout(button_layout)
        
        # 注册字体
        if self.font_manager:
            widgets_to_register = [
                title_label, self.name_edit, self.desc_edit, self.format_edit,
                self.usage_edit, self.attention_edit, self.ai_use_checkbox,
                self.detailed_checkbox, self.external_plugin_checkbox,
                cancel_button, confirm_button
            ]
            for widget in widgets_to_register:
                if hasattr(widget, 'setFont'):
                    self.font_manager.register_widget(widget)
    
    def populate_data(self, plugin_name: str, plugin_data: dict):
        """填充编辑模式的数据"""
        self.name_edit.setText(plugin_name)
        self.desc_edit.setText(plugin_data.get('discription', ''))
        self.format_edit.setText(plugin_data.get('format', ''))
        self.usage_edit.setText(plugin_data.get('usage', ''))
        self.attention_edit.setText(plugin_data.get('attention', ''))
        self.ai_use_checkbox.setChecked(plugin_data.get('AI_can_use', True))
        self.detailed_checkbox.setChecked(plugin_data.get('detailed_info', False))
        self.external_plugin_checkbox.setChecked(plugin_data.get('have_plugin', False))
    
    def get_plugin_data(self) -> dict:
        """
        获取插件数据
        
        Returns:
            dict: 插件数据字典
        """
        return {
            'name': self.name_edit.text().strip(),
            'discription': self.desc_edit.toPlainText().strip(),
            'format': self.format_edit.text().strip(),
            'usage': self.usage_edit.toPlainText().strip(),
            'attention': self.attention_edit.toPlainText().strip(),
            'AI_can_use': self.ai_use_checkbox.isChecked(),
            'detailed_info': self.detailed_checkbox.isChecked(),
            'have_plugin': self.external_plugin_checkbox.isChecked()
        }
    
    def accept(self):
        """确认按钮处理"""
        # 验证必填字段
        if not self.validate_input():
            return
        
        super().accept()
    
    def validate_input(self) -> bool:
        """
        验证输入数据
        
        Returns:
            bool: 验证通过返回True，否则返回False
        """
        # 检查必填字段
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "输入错误", "插件名称不能为空！")
            self.name_edit.setFocus()
            return False
        
        if not self.desc_edit.toPlainText().strip():
            QMessageBox.warning(self, "输入错误", "功能描述不能为空！")
            self.desc_edit.setFocus()
            return False
        
        if not self.format_edit.text().strip():
            QMessageBox.warning(self, "输入错误", "执行格式不能为空！")
            self.format_edit.setFocus()
            return False
        
        if not self.usage_edit.toPlainText().strip():
            QMessageBox.warning(self, "输入错误", "使用说明不能为空！")
            self.usage_edit.setFocus()
            return False
        
        # 检查插件名称格式（简单验证）
        plugin_name = self.name_edit.text().strip()
        if not plugin_name.replace('_', '').replace('-', '').isalnum():
            QMessageBox.warning(self, "输入错误", "插件名称只能包含字母、数字、下划线和连字符！")
            self.name_edit.setFocus()
            return False
        
        return True

# 测试代码
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # 测试添加模式
    dialog = AddPluginDialog()
    if dialog.exec() == QDialog.DialogCode.Accepted:
        plugin_data = dialog.get_plugin_data()
        print("添加插件数据:", plugin_data)
    
    # 测试编辑模式
    test_data = {
        'discription': '测试插件描述',
        'format': '[TEST:test_plugin]',
        'usage': '测试使用说明',
        'attention': '测试注意事项',
        'AI_can_use': True,
        'detailed_info': False
    }
    
    edit_dialog = AddPluginDialog(plugin_name="test_plugin", plugin_data=test_data)
    if edit_dialog.exec() == QDialog.DialogCode.Accepted:
        plugin_data = edit_dialog.get_plugin_data()
        print("编辑插件数据:", plugin_data)
    
    sys.exit(app.exec())