"""
插件页面组件 - 插件管理的主界面
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
                             QLabel, QPushButton, QFrame, QMessageBox, QGridLayout)
from PyQt6.QtCore import Qt
import logging
from PyQt6.QtGui import QIcon

from lib.plugin_manager import PluginManager
from lib.plugin_card_widget import PluginCardWidget
# 延迟导入，避免循环依赖
# from lib.add_plugin_dialog import AddPluginDialog

class PluginPageWidget(QWidget):
    """插件页面主组件"""
    
    def __init__(self, font_manager=None, parent=None):
        """
        初始化插件页面
        
        Args:
            font_manager: 字体管理器
            parent: 父组件
        """
        super().__init__(parent)
        self.font_manager = font_manager
        self.plugin_manager = PluginManager()
        self.plugin_cards = {}  # 存储插件卡片引用
        
        # 初始化日志
        self.logger = logging.getLogger(__name__)
        
        self.setup_ui()
        self.load_plugins()
    
    def setup_ui(self):
        """设置插件页面UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # 顶部工具栏
        toolbar = self.create_toolbar()
        main_layout.addWidget(toolbar)
        
        # 状态信息栏
        self.status_label = QLabel()
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #f0f8ff;
                border: 1px solid #87ceeb;
                border-radius: 5px;
                padding: 8px;
                color: #2F4F2F;
                font-size: 14px;
            }
        """)
        main_layout.addWidget(self.status_label)
        
        # 插件列表区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(200, 200, 200, 100);
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(150, 150, 150, 150);
                min-height: 20px;
                border-radius: 4px;
            }
        """)
        
        # 插件卡片容器
        self.cards_container = QWidget()
        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setSpacing(15)
        self.cards_layout.setContentsMargins(10, 10, 10, 10)
        
        self.scroll_area.setWidget(self.cards_container)
        main_layout.addWidget(self.scroll_area)
        
        # 注册字体
        if self.font_manager:
            self.font_manager.register_widget(self.status_label)
    
    def create_toolbar(self) -> QFrame:
        """创建工具栏"""
        toolbar = QFrame()
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #f8fff8;
                border: 1px solid #e8f5e8;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setSpacing(15)
        
        # 页面标题
        title_label = QLabel("🔌 插件管理")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2F4F2F;
            }
        """)
        toolbar_layout.addWidget(title_label)
        toolbar_layout.addStretch()
        
        # 刷新按钮
        self.refresh_button = QPushButton("🔄 刷新")
        self.refresh_button.setFixedSize(100, 35)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #98FB98;
                color: #2F4F2F;
                border: 1px solid #3CB371;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #77DD77;
                border: 1px solid #228B22;
            }
            QPushButton:pressed {
                background-color: #55AA55;
            }
        """)
        self.refresh_button.clicked.connect(self.refresh_plugins)
        toolbar_layout.addWidget(self.refresh_button)
        
        # 添加插件按钮
        self.add_button = QPushButton("➕ 添加插件")
        self.add_button.setFixedSize(120, 35)
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #87CEEB;
                color: white;
                border: 1px solid #4682B4;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #70C1D5;
                border: 1px solid #3A6D9C;
            }
            QPushButton:pressed {
                background-color: #5BA9C2;
            }
        """)
        self.add_button.clicked.connect(self.add_plugin)
        toolbar_layout.addWidget(self.add_button)
        
        # 注册字体
        if self.font_manager:
            widgets_to_register = [title_label, self.refresh_button, self.add_button]
            for widget in widgets_to_register:
                if hasattr(widget, 'setFont'):
                    self.font_manager.register_widget(widget)
        
        return toolbar
    
    def load_plugins(self):
        """加载并显示所有插件"""
        try:
            # 清除现有卡片
            self.clear_plugin_cards()
            
            # 获取插件数据
            plugins = self.plugin_manager.get_plugins()
            
            if not plugins:
                self.show_empty_state()
                return
            
            # 创建插件卡片
            row, col = 0, 0
            max_cols = 2  # 每行最多2个卡片
            
            for plugin_name, plugin_data in plugins.items():
                card = PluginCardWidget(plugin_name, plugin_data, self.font_manager)
                
                # 连接信号
                card.edit_clicked.connect(self.edit_plugin)
                card.delete_clicked.connect(self.delete_plugin)
                
                # 添加到布局
                self.cards_layout.addWidget(card, row, col)
                
                # 保存卡片引用
                self.plugin_cards[plugin_name] = card
                
                # 更新行列位置
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
            
            # 更新状态信息
            self.update_status(f"已加载 {len(plugins)} 个插件")
            
        except Exception as e:
            self.logger.error(f"加载插件失败: {e}")
            self.show_error_state(f"加载插件失败: {str(e)}")
    
    def clear_plugin_cards(self):
        """清除所有插件卡片"""
        # 清除布局中的所有widget
        while self.cards_layout.count():
            child = self.cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # 清空卡片引用
        self.plugin_cards.clear()
    
    def show_empty_state(self):
        """显示空状态"""
        empty_label = QLabel("暂无插件，请点击「添加插件」按钮创建新插件")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #888888;
                padding: 50px;
            }
        """)
        
        if self.font_manager:
            self.font_manager.register_widget(empty_label)
        
        self.cards_layout.addWidget(empty_label, 0, 0)
        self.update_status("暂无插件")
    
    def show_error_state(self, error_message: str):
        """显示错误状态"""
        error_label = QLabel(f"❌ {error_message}")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #FF0000;
                padding: 50px;
                background-color: #FFE6E6;
                border: 1px solid #FFCCCC;
                border-radius: 8px;
            }
        """)
        
        if self.font_manager:
            self.font_manager.register_widget(error_label)
        
        self.cards_layout.addWidget(error_label, 0, 0)
        self.update_status(f"错误: {error_message}")
    
    def update_status(self, message: str):
        """更新状态信息"""
        self.status_label.setText(message)
    
    def refresh_plugins(self):
        """刷新插件列表"""
        self.update_status("正在刷新插件...")
        self.plugin_manager.load_plugins()
        self.load_plugins()
    
    def add_plugin(self):
        """添加新插件"""
        try:
            # 延迟导入避免循环依赖
            from lib.add_plugin_dialog import AddPluginDialog
            dialog = AddPluginDialog(self.font_manager, self)
            if dialog.exec() == AddPluginDialog.DialogCode.Accepted:
                plugin_data = dialog.get_plugin_data()
                plugin_name = plugin_data.pop('name')  # 提取插件名称
                
                if self.plugin_manager.add_plugin(plugin_name, plugin_data):
                    self.load_plugins()  # 重新加载显示
                    QMessageBox.information(self, "成功", f"插件 '{plugin_name}' 添加成功！")
                else:
                    QMessageBox.critical(self, "错误", "添加插件失败！")
                    
        except Exception as e:
            self.logger.error(f"添加插件异常: {e}")
            QMessageBox.critical(self, "错误", f"添加插件时发生异常: {str(e)}")
    
    def edit_plugin(self, plugin_name: str):
        """编辑插件"""
        try:
            # 获取当前插件数据
            current_data = self.plugin_manager.get_plugin(plugin_name)
            if not current_data:
                QMessageBox.warning(self, "警告", f"插件 '{plugin_name}' 不存在！")
                return
            
            # 延迟导入避免循环依赖
            from lib.add_plugin_dialog import AddPluginDialog
            # 创建编辑对话框
            dialog = AddPluginDialog(self.font_manager, self, plugin_name, current_data)
            if dialog.exec() == AddPluginDialog.DialogCode.Accepted:
                new_plugin_data = dialog.get_plugin_data()
                new_name = new_plugin_data.pop('name')
                
                # 如果名称改变，需要特殊处理
                if new_name != plugin_name:
                    # 先删除旧插件，再添加新插件
                    if self.plugin_manager.delete_plugin(plugin_name):
                        if self.plugin_manager.add_plugin(new_name, new_plugin_data):
                            self.load_plugins()
                            QMessageBox.information(self, "成功", f"插件已更新为 '{new_name}'！")
                        else:
                            # 如果添加失败，尝试恢复原插件
                            self.plugin_manager.add_plugin(plugin_name, current_data)
                            QMessageBox.critical(self, "错误", "更新插件失败！")
                    else:
                        QMessageBox.critical(self, "错误", "删除原插件失败！")
                else:
                    # 名称未改变，直接更新
                    if self.plugin_manager.update_plugin(plugin_name, new_plugin_data):
                        self.load_plugins()
                        QMessageBox.information(self, "成功", f"插件 '{plugin_name}' 更新成功！")
                    else:
                        QMessageBox.critical(self, "错误", "更新插件失败！")
                        
        except Exception as e:
            self.logger.error(f"编辑插件异常: {e}")
            QMessageBox.critical(self, "错误", f"编辑插件时发生异常: {str(e)}")
    
    def delete_plugin(self, plugin_name: str):
        """删除插件"""
        try:
            # 确认对话框
            msg_box = QMessageBox(self)
            msg_box.setWindowIcon(QIcon("ico/ico.png"))  # 设置窗口标题栏图标
            msg_box.setIcon(QMessageBox.Icon.Question)  # 设置对话框内的问号图标
            msg_box.setWindowTitle("确认删除")
            msg_box.setText(f"确定要删除插件 '{plugin_name}' 吗？此操作不可撤销！")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QMessageBox.StandardButton.No)
            
            reply = msg_box.exec()
        
            
            if reply == QMessageBox.StandardButton.Yes:
                if self.plugin_manager.delete_plugin(plugin_name):
                    self.load_plugins()  # 重新加载显示
                    QMessageBox.information(self, "成功", f"插件 '{plugin_name}' 已删除！")
                else:
                    QMessageBox.critical(self, "错误", "删除插件失败！")
                    
        except Exception as e:
            self.logger.error(f"删除插件异常: {e}")
            QMessageBox.critical(self, "错误", f"删除插件时发生异常: {str(e)}")

# 测试代码
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    import logging
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    app = QApplication(sys.argv)
    
    # 创建插件页面
    plugin_page = PluginPageWidget()
    plugin_page.setWindowTitle("插件管理页面测试")
    plugin_page.resize(800, 600)
    plugin_page.show()
    
    sys.exit(app.exec())