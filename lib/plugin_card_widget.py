"""
插件卡片组件 - 展示单个插件信息的卡片
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class PluginCardWidget(QFrame):
    """插件卡片组件"""
    
    # 定义信号
    edit_clicked = pyqtSignal(str)      # 编辑信号，传递插件名称
    delete_clicked = pyqtSignal(str)    # 删除信号，传递插件名称
    
    def __init__(self, plugin_name: str, plugin_data: dict, font_manager=None, parent=None):
        """
        初始化插件卡片
        
        Args:
            plugin_name (str): 插件名称
            plugin_data (dict): 插件数据
            font_manager: 字体管理器
            parent: 父组件
        """
        super().__init__(parent)
        self.plugin_name = plugin_name
        self.plugin_data = plugin_data
        self.font_manager = font_manager
        
        self.setup_ui()
        self.apply_styles()
    
    def setup_ui(self):
        """设置卡片UI"""
        # 设置基本属性
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setLineWidth(1)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # 标题区域（插件名称和图标）
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)
        
        # 插件图标（简化版，使用emoji）
        self.icon_label = QLabel("🔌")
        self.icon_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                padding: 5px;
            }
        """)
        title_layout.addWidget(self.icon_label)
        
        # 插件名称 - 增强视觉效果
        self.name_label = QLabel(self.plugin_name)
        self.name_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #191970;
                background-color: transparent;
                padding: 2px 8px;
                border-radius: 4px;
            }
            QLabel:hover {
                background-color: rgba(135, 206, 235, 0.1);
            }
        """)
        title_layout.addWidget(self.name_label)
        title_layout.addStretch()
        
        main_layout.addLayout(title_layout)
        
        # 描述信息 - 增强视觉效果
        self.desc_label = QLabel(self.plugin_data.get('discription', '暂无描述'))
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #464646;
                padding: 8px 12px;
                background-color: rgba(245, 245, 245, 0.7);
                border-radius: 6px;
                border-left: 3px solid #87CEEB;
            }
        """)
        main_layout.addWidget(self.desc_label)
        
        # 格式信息
        format_text = self.plugin_data.get('format', '')
        if format_text:
            format_label = QLabel(f"格式: {format_text}")
            format_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #666666;
                    font-family: Consolas, Monaco, monospace;
                    background-color: #f8f8f8;
                    padding: 3px 6px;
                    border-radius: 3px;
                }
            """)
            main_layout.addWidget(format_label)
        
        # 使用说明
        usage_text = self.plugin_data.get('usage', '')
        if usage_text:
            usage_label = QLabel(f"说明: {usage_text}")
            usage_label.setWordWrap(True)
            usage_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #444444;
                    padding: 3px 0;
                }
            """)
            main_layout.addWidget(usage_label)
        
        # 注意事项
        attention_text = self.plugin_data.get('attention', '')
        if attention_text:
            attention_label = QLabel(f"注意: {attention_text}")
            attention_label.setWordWrap(True)
            attention_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #8B0000;
                    padding: 3px 0;
                    font-style: italic;
                }
            """)
            main_layout.addWidget(attention_label)
        
        # 状态信息
        status_layout = QHBoxLayout()
        status_layout.setSpacing(15)
        
        # AI可使用状态
        ai_status = "✅" if self.plugin_data.get('AI_can_use', False) else "❌"
        ai_label = QLabel(f"AI可用: {ai_status}")
        ai_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #2F4F2F;
            }
        """)
        status_layout.addWidget(ai_label)
        
        # 详细信息状态
        detail_status = "📋" if self.plugin_data.get('detailed_info', False) else "📄"
        detail_label = QLabel(f"详情: {detail_status}")
        detail_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #2F4F2F;
            }
        """)
        status_layout.addWidget(detail_label)
        
        status_layout.addStretch()
        main_layout.addLayout(status_layout)
        
        # 操作按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        # 编辑按钮 - 增强视觉效果
        self.edit_button = QPushButton("📝 编辑")
        self.edit_button.setFixedSize(85, 35)
        self.edit_button.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                                  stop:0 #87CEEB, stop:1 #5BA9C2);
                color: white;
                border: 1px solid #4A90A4;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                                  stop:0 #70C1D5, stop:1 #4A8CAD);
                border: 1px solid #3A7A8C;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                                  stop:0 #5BA9C2, stop:1 #3A7A8C);
                border: 1px solid #2A6A7C;
            }
        """)
        self.edit_button.clicked.connect(self.on_edit_clicked)
        button_layout.addWidget(self.edit_button)
        
        # 删除按钮 - 增强视觉效果
        self.delete_button = QPushButton("🗑️ 删除")
        self.delete_button.setFixedSize(85, 35)
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                                  stop:0 #FF6B6B, stop:1 #E53935);
                color: white;
                border: 1px solid #CC3333;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                                  stop:0 #FF5252, stop:1 #D32F2F);
                border: 1px solid #B71C1C;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                                  stop:0 #E53935, stop:1 #C62828);
                border: 1px solid #B71C1C;
            }
        """)
        self.delete_button.clicked.connect(self.on_delete_clicked)
        button_layout.addWidget(self.delete_button)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        # 注册到字体管理器
        if self.font_manager:
            widgets_to_register = [
                self.name_label, self.desc_label, self.icon_label,
                self.edit_button, self.delete_button
            ]
            for widget in widgets_to_register:
                if hasattr(widget, 'setFont'):
                    self.font_manager.register_widget(widget)
    
    def apply_styles(self):
        """应用卡片样式 - 增强视觉效果"""
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #E8E8E8;
                border-radius: 15px;
                margin: 8px;
                padding: 3px;
            }
            QFrame:hover {
                border: 2px solid #87CEEB;
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                                  stop:0 #FAFDFF, stop:1 #F0F8FF);
                /* 使用渐变背景和边框增强替代阴影效果 */
            }
        """)
    
    def on_edit_clicked(self):
        """编辑按钮点击处理"""
        self.edit_clicked.emit(self.plugin_name)
    
    def on_delete_clicked(self):
        """删除按钮点击处理"""
        self.delete_clicked.emit(self.plugin_name)
    
    def update_plugin_data(self, plugin_name: str, plugin_data: dict):
        """
        更新插件数据显示
        
        Args:
            plugin_name (str): 新的插件名称
            plugin_data (dict): 新的插件数据
        """
        self.plugin_name = plugin_name
        self.plugin_data = plugin_data
        
        # 更新显示内容
        self.name_label.setText(plugin_name)
        self.desc_label.setText(plugin_data.get('discription', '暂无描述'))
        
        # 重新应用样式（可能需要更新某些状态显示）
        self.apply_styles()

# 测试代码
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication, QScrollArea
    import sys
    
    app = QApplication(sys.argv)
    
    # 创建测试数据
    test_plugin_data = {
        "discription": "这是一个测试插件，用于演示插件卡片的功能",
        "format": "[TEST:demo_plugin]",
        "usage": "点击编辑按钮可以修改插件信息，点击删除按钮可以移除插件",
        "attention": "删除操作不可撤销，请谨慎操作",
        "AI_can_use": True,
        "detailed_info": True
    }
    
    # 创建主窗口
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    
    # 创建测试卡片
    test_card = PluginCardWidget("测试插件", test_plugin_data)
    
    # 连接信号
    def on_edit(name):
        print(f"编辑插件: {name}")
    
    def on_delete(name):
        print(f"删除插件: {name}")
    
    test_card.edit_clicked.connect(on_edit)
    test_card.delete_clicked.connect(on_delete)
    
    scroll_area.setWidget(test_card)
    scroll_area.setWindowTitle("插件卡片测试")
    scroll_area.resize(400, 300)
    scroll_area.show()
    
    sys.exit(app.exec())