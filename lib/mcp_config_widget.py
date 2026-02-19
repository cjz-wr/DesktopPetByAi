"""
MCP配置界面组件
用于在设置界面中管理MCP服务器配置
"""

import json
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QListWidget, QListWidgetItem, QLineEdit, QLabel, 
                            QMessageBox, QGroupBox, QFormLayout, QCheckBox,
                            QSpinBox, QFrame, QDialog)
from PyQt6.QtCore import pyqtSignal
from typing import Dict, Any

class MCPConfigWidget(QWidget):
    """MCP配置界面组件"""
    
    config_changed = pyqtSignal()  # 配置改变信号
    
    def __init__(self, parent=None, font_manager=None):
        super().__init__(parent)
        self.font_manager = font_manager
        self.config_file = "mcp_config.json"
        self.servers = {}
        
        self.setup_ui()
        self.load_config()
        
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 标题
        title = QLabel("🔌 MCP服务器配置")
        title.setObjectName("section-title")
        if self.font_manager:
            self.font_manager.register_widget(title)
        layout.addWidget(title)
        
        # 服务器列表组
        server_group = QGroupBox("已配置的MCP服务器")
        server_layout = QVBoxLayout(server_group)
        
        # 服务器列表
        self.server_list = QListWidget()
        self.server_list.setObjectName("server-list")
        if self.font_manager:
            self.font_manager.register_widget(self.server_list)
        server_layout.addWidget(self.server_list)
        
        # 操作按钮布局
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("➕ 添加服务器")
        self.add_button.setObjectName("add-server-button")
        self.add_button.clicked.connect(self.add_server)
        if self.font_manager:
            self.font_manager.register_widget(self.add_button)
        
        self.edit_button = QPushButton("✏️ 编辑服务器")
        self.edit_button.setObjectName("edit-server-button")
        self.edit_button.clicked.connect(self.edit_server)
        self.edit_button.setEnabled(False)
        if self.font_manager:
            self.font_manager.register_widget(self.edit_button)
        
        self.remove_button = QPushButton("🗑️ 删除服务器")
        self.remove_button.setObjectName("remove-server-button")
        self.remove_button.clicked.connect(self.remove_server)
        self.remove_button.setEnabled(False)
        if self.font_manager:
            self.font_manager.register_widget(self.remove_button)
        
        self.test_button = QPushButton("🧪 测试连接")
        self.test_button.setObjectName("test-server-button")
        self.test_button.clicked.connect(self.test_connection)
        self.test_button.setEnabled(False)
        if self.font_manager:
            self.font_manager.register_widget(self.test_button)
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addWidget(self.test_button)
        button_layout.addStretch()
        
        server_layout.addLayout(button_layout)
        layout.addWidget(server_group)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # 工具信息显示
        tools_group = QGroupBox("可用工具")
        tools_layout = QVBoxLayout(tools_group)
        
        self.tools_display = QLabel("暂无可用工具")
        self.tools_display.setWordWrap(True)
        self.tools_display.setObjectName("tools-info")
        if self.font_manager:
            self.font_manager.register_widget(self.tools_display)
        tools_layout.addWidget(self.tools_display)
        
        refresh_tools_button = QPushButton("🔄 刷新工具列表")
        refresh_tools_button.setObjectName("refresh-tools-button")
        refresh_tools_button.clicked.connect(self.refresh_tools)
        if self.font_manager:
            self.font_manager.register_widget(refresh_tools_button)
        tools_layout.addWidget(refresh_tools_button)
        
        layout.addWidget(tools_group)
        
        # 连接列表选择信号
        self.server_list.itemSelectionChanged.connect(self.on_selection_changed)
        
        # 设置更现代的布局间距
        layout.setContentsMargins(20, 15, 20, 15)
        server_group.setContentsMargins(10, 10, 10, 10)
        tools_group.setContentsMargins(10, 10, 10, 10)
        
    def load_config(self):
        """加载配置"""
        if not os.path.exists(self.config_file):
            self.create_default_config()
            return
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.servers = config.get('mcpServers', {})
                self.update_server_list()
        except Exception as e:
            QMessageBox.warning(self, "加载失败", f"无法加载MCP配置: {str(e)}")
    
    def create_default_config(self):
        """创建默认配置"""
        default_config = {
            "mcpServers": {
                "bing-search": {
                    "type": "sse",
                    "url": "https://mcp.api-inference.modelscope.net/e3032c28c1cb4f/mcp",
                    "enabled": True,
                    "timeout": 30
                }
            },
            "timeout": 30
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            self.servers = default_config['mcpServers']
            self.update_server_list()
        except Exception as e:
            QMessageBox.warning(self, "创建失败", f"无法创建默认配置: {str(e)}")
    
    def update_server_list(self):
        """更新服务器列表显示"""
        self.server_list.clear()
        
        for name, server_info in self.servers.items():
            item = QListWidgetItem(f"{name} ({'启用' if server_info.get('enabled', True) else '禁用'})")
            item.setData(1, name)  # 存储服务器名称
            self.server_list.addItem(item)
    
    def on_selection_changed(self):
        """选择改变时更新按钮状态"""
        has_selection = len(self.server_list.selectedItems()) > 0
        self.edit_button.setEnabled(has_selection)
        self.remove_button.setEnabled(has_selection)
        self.test_button.setEnabled(has_selection)
    
    def add_server(self):
        """添加服务器"""
        dialog = ServerConfigDialog(self, self.font_manager)
        if dialog.exec() == dialog.DialogCode.Accepted:
            server_config = dialog.get_config()
            name = server_config.pop('name')
            
            if name in self.servers:
                QMessageBox.warning(self, "添加失败", f"服务器 '{name}' 已存在")
                return
            
            self.servers[name] = server_config
            self.save_config()
            self.update_server_list()
            self.config_changed.emit()
    
    def edit_server(self):
        """编辑服务器"""
        selected_items = self.server_list.selectedItems()
        if not selected_items:
            return
            
        name = selected_items[0].data(1)
        server_info = self.servers.get(name, {})
        
        dialog = ServerConfigDialog(self, self.font_manager, name, server_info)
        if dialog.exec() == dialog.DialogCode.Accepted:
            server_config = dialog.get_config()
            new_name = server_config.pop('name')
            
            # 如果名称改变，需要重新处理
            if new_name != name:
                if new_name in self.servers:
                    QMessageBox.warning(self, "编辑失败", f"服务器 '{new_name}' 已存在")
                    return
                del self.servers[name]
            
            self.servers[new_name] = server_config
            self.save_config()
            self.update_server_list()
            self.config_changed.emit()
    
    def remove_server(self):
        """删除服务器"""
        selected_items = self.server_list.selectedItems()
        if not selected_items:
            return
            
        name = selected_items[0].data(1)
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除服务器 '{name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self.servers[name]
            self.save_config()
            self.update_server_list()
            self.config_changed.emit()
    
    def test_connection(self):
        """测试连接"""
        selected_items = self.server_list.selectedItems()
        if not selected_items:
            return
            
        name = selected_items[0].data(1)
        server_info = self.servers.get(name, {})
        
        QMessageBox.information(
            self, "测试结果", 
            f"服务器: {name}\n"
            f"类型: {server_info.get('type', '未知')}\n"
            f"URL: {server_info.get('url', '未设置')}\n\n"
            f"注意：实际连接测试需要MCP功能启用"
        )
    
    def refresh_tools(self):
        """刷新工具列表"""
        # 这里应该调用MCP管理器获取工具列表
        self.tools_display.setText("工具列表刷新功能待实现")
    
    def save_config(self):
        """保存配置"""
        config = {
            "mcpServers": self.servers,
            "timeout": 30
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "保存失败", f"无法保存配置: {str(e)}")


class ServerConfigDialog(QDialog):
    """服务器配置对话框"""
    
    def __init__(self, parent=None, font_manager=None, name="", server_info=None):
        super().__init__(parent)
        self.font_manager = font_manager
        self.setWindowTitle("配置MCP服务器")
        self.resize(400, 300)
        
        self.name = name
        self.server_info = server_info or {}
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        
        # 表单布局
        form_layout = QFormLayout()
        
        # 服务器名称
        self.name_input = QLineEdit()
        self.name_input.setText(self.name)
        self.name_input.setPlaceholderText("输入服务器名称")
        self.name_input.setStyleSheet("color: #2F4F2F;")
        if self.font_manager:
            self.font_manager.register_widget(self.name_input)
        form_layout.addRow("服务器名称:", self.name_input)
        
        # 服务器类型
        self.type_input = QLineEdit()
        self.type_input.setText(self.server_info.get('type', 'sse'))
        self.type_input.setPlaceholderText("例如: sse")
        self.type_input.setStyleSheet("color: #2F4F2F;")
        if self.font_manager:
            self.font_manager.register_widget(self.type_input)
        form_layout.addRow("服务器类型:", self.type_input)
        
        # 服务器URL
        self.url_input = QLineEdit()
        self.url_input.setText(self.server_info.get('url', ''))
        self.url_input.setPlaceholderText("输入MCP服务器URL")
        self.url_input.setStyleSheet("color: #2F4F2F;")
        if self.font_manager:
            self.font_manager.register_widget(self.url_input)
        form_layout.addRow("服务器URL:", self.url_input)
        
        # 超时设置
        self.timeout_input = QSpinBox()
        self.timeout_input.setRange(1, 300)
        self.timeout_input.setValue(self.server_info.get('timeout', 30))
        self.timeout_input.setStyleSheet("color: #2F4F2F;")
        if self.font_manager:
            self.font_manager.register_widget(self.timeout_input)
        form_layout.addRow("超时时间(秒):", self.timeout_input)
        
        # 启用状态
        self.enabled_checkbox = QCheckBox("启用此服务器")
        self.enabled_checkbox.setChecked(self.server_info.get('enabled', True))
        self.enabled_checkbox.setStyleSheet("""
    QCheckBox {
        color: #191970;
        spacing: 8px;
    }
    QCheckBox::indicator {
        width: 20px;
        height: 20px;
        border: 2px solid #87CEEB;
        border-radius: 4px;
        background-color: white;
    }
    QCheckBox::indicator:checked {
        background-color: #4CAF50;
        border-color: #2E7D32;
        image: url(:/qt-project.org/styles/commonstyle/images/checkbox-checked.png);
    }
""")
        
        if self.font_manager:
            self.font_manager.register_widget(self.enabled_checkbox)
        form_layout.addRow("", self.enabled_checkbox)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_button = QPushButton("确定")
        ok_button.setObjectName("ok-button")
        ok_button.clicked.connect(self.accept)
        if self.font_manager:
            self.font_manager.register_widget(ok_button)
        
        cancel_button = QPushButton("取消")
        cancel_button.setObjectName("cancel-button")
        cancel_button.clicked.connect(self.reject)
        if self.font_manager:
            self.font_manager.register_widget(cancel_button)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        # 添加对话框样式 - 优化版本避免不支持的属性
        self.setStyleSheet("""
            QDialog {
                background-color: #F8F8FF;
                border-radius: 12px;
                border: 1px solid #E0E0E0;
            }
            QLabel {
                color: #2F4F2F;
                font-size: 14px;
            }
            QLineEdit, QSpinBox {
                padding: 8px 12px;
                border: 1px solid #B0E0E6;
                border-radius: 6px;
                background-color: #FFFFFF;
                selection-background-color: #98FB98;
                font-size: 14px;
            }
            QLineEdit:focus, QSpinBox:focus {
                border-color: #3CB371;
                background-color: #FFFFFF;
            }
            QCheckBox {
                color: #2F4F2F;
                spacing: 8px;
            }
            QPushButton {
                padding: 8px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton#ok-button {
                background-color: #90EE90;
                color: white;
                border: 1px solid #2E8B57;
            }
            QPushButton#ok-button:hover {
                background-color: #77DD77;
                border: 1px solid #228B22;
            }
            QPushButton#cancel-button {
                background-color: #F0F8FF;
                color: #2F4F2F;
                border: 1px solid #B0E0E6;
            }
            QPushButton#cancel-button:hover {
                background-color: #E0E0E0;
                border: 1px solid #909090;
            }
        """)
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置数据"""
        return {
            'name': self.name_input.text().strip(),
            'type': self.type_input.text().strip(),
            'url': self.url_input.text().strip(),
            'timeout': self.timeout_input.value(),
            'enabled': self.enabled_checkbox.isChecked()
        }