
'''
食物数据编辑器
该工具提供GUI界面用于查看和修改嵌入在图片中的食物数据
'''

import re  # 添加正则表达式导入
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QLineEdit, QTextEdit, QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QFormLayout, 
    QComboBox  # 添加QComboBox导入
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon
from lib.food_manager import FoodVerification
import os


class LoadFoodListWorker(QThread):
    """加载食物列表的后台线程"""
    finished = pyqtSignal(list)  # 加载完成信号，传递处理好的数据列表
    progress = pyqtSignal(int, int)  # 进度信号，传递当前进度和总数量
    
    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
    
    def run(self):
        """在后台线程中执行加载操作"""
        try:
            # 获取所有图片文件扩展名
            image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
            
            # 获取food文件夹中的所有图片文件
            image_files = [
                os.path.join(self.folder_path, file) 
                for file in os.listdir(self.folder_path) 
                if os.path.splitext(file)[1].lower() in image_extensions
            ]
            
            total_count = len(image_files)
            
            # 准备要发送给主线程的数据
            result_data = []
            for idx, image_path in enumerate(image_files):
                file_name = os.path.basename(image_path)
                
                # 尝试提取食物信息
                success, data = FoodVerification.extract_food_info(image_path)
                
                if success:
                    row_data = [
                        file_name,
                        data.get("FoodName", ""),
                        data.get("FoodDescription", ""),
                        str(data.get("FoodCalories", "")),
                        str(data.get("FoodWater", "")),
                        str(data.get("FoodTime", "")),
                        data.get("FoodType", "")  # 添加食物类型字段
                    ]
                else:
                    # 如果提取失败，填充空白
                    row_data = [
                        file_name,
                        "",
                        "",
                        "",
                        "",
                        "",
                        ""
                    ]
                
                result_data.append((row_data, image_path))  # 附加image_path用于后续操作
                
                # 发送进度信号
                self.progress.emit(idx + 1, total_count)
            
            self.finished.emit(result_data)
        except Exception as e:
            # 发送空列表表示加载失败
            self.finished.emit([])


class SaveFoodDataWorker(QThread):
    """处理食物数据保存的后台线程"""
    finished = pyqtSignal(bool, str)  # 保存完成信号 (success, message)
    
    def __init__(self, image_path, food_name, food_description, food_calories, food_water, food_time, food_type):
        super().__init__()
        self.image_path = image_path
        self.food_name = food_name
        self.food_description = food_description
        self.food_calories = food_calories
        self.food_water = food_water
        self.food_time = food_time
        self.food_type = food_type  # 添加食物类型参数
    
    def run(self):
        """在后台线程中执行保存操作"""
        try:
            # 创建临时文件路径
            base_name, ext = os.path.splitext(self.image_path)
            temp_path = base_name + "_temp" + ext
            
            # 尝试嵌入新的食物信息
            success, message = FoodVerification.embed_food_info(
                self.image_path,  # 原始图片路径
                self.food_name,
                self.food_description,
                self.food_calories,
                self.food_water,
                self.food_time,  # 食用时间参数
                temp_path,  # 临时输出路径
                self.food_type  # 食物类型参数
            )
            
            if success:
                # 替换原文件
                os.replace(temp_path, self.image_path)
                self.finished.emit(True, "食物数据已保存！")
            else:
                # 删除临时文件（如果存在）
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                self.finished.emit(False, message)
        except Exception as e:
            self.finished.emit(False, f"保存过程中发生错误: {str(e)}")


class FoodEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("食物数据编辑器")
        self.setGeometry(100, 100, 1000, 700)
        
        # 设置中央窗口
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 创建UI组件
        self.create_widgets(main_layout)
        
        # 初始化工作线程
        self.worker = None
        self.all_food_data = []  # 存储所有食物数据
        self.current_display_count = 0  # 当前显示的数量
        self.load_batch_size = 20  # 每批加载的数量
        
        # 启动后台线程加载食物列表
        self.load_food_list_async()
    
    def create_widgets(self, layout):
        """创建界面组件"""
        # 左侧：食物列表
        left_group = QGroupBox("食物列表")
        left_layout = QVBoxLayout(left_group)
        
        # 表格显示食物列表
        self.food_table = QTableWidget()
        self.food_table.setColumnCount(7)  # 增加一列，总数改为7列
        self.food_table.setHorizontalHeaderLabels(["图片名称", "食物名称", "食物描述", "食物热量", "食物水分", "食用时间", "食物类型"])
        self.food_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.food_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.food_table.cellClicked.connect(self.on_food_selected)
        
        # 启用滚动条事件监听，用于流式加载
        self.food_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.food_table.verticalScrollBar().valueChanged.connect(self.scroll_changed)
        
        left_layout.addWidget(self.food_table)
        
        # 添加进度标签
        self.progress_label = QLabel("正在加载...")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setVisible(False)
        left_layout.addWidget(self.progress_label)
        
        # 右侧：编辑区域
        right_group = QGroupBox("编辑食物信息")
        right_layout = QFormLayout(right_group)
        
        # 图片预览
        self.image_preview = QLabel()
        self.image_preview.setFixedSize(200, 200)
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setStyleSheet("border: 1px solid gray;")
        right_layout.addRow("图片预览:", self.image_preview)
        
        # 输入字段
        self.name_input = QLineEdit()
        self.description_input = QTextEdit()
        self.calories_input = QLineEdit()
        self.water_input = QLineEdit()
        self.time_input = QLineEdit()  # 新增食用时间输入框
        self.type_combo = QComboBox()  # 新增食物类型下拉框
        
        # 设置输入框的提示文本
        self.time_input.setPlaceholderText("例如: 30s, 10m, 2h, 1d")
        
        # 设置食物类型下拉框选项
        self.type_combo.addItems([
            "主食", 
            "零食", 
            "水果", 
            "蔬菜", 
            "肉类", 
            "饮品", 
            "甜品", 
            "坚果", 
            "乳制品", 
            "其他"
        ])
        
        right_layout.addRow("食物名称:", self.name_input)
        right_layout.addRow("食物描述:", self.description_input)
        right_layout.addRow("食物热量:", self.calories_input)
        right_layout.addRow("食物水分:", self.water_input)
        right_layout.addRow("食用时间:", self.time_input)  # 添加食用时间行
        right_layout.addRow("食物类型:", self.type_combo)  # 添加食物类型行
        
        # 添加食用时间格式说明
        time_info_label = QLabel("食用时间格式说明：\n• s - 秒 (例如: 30s)\n• m - 分 (例如: 10m)\n• h - 时 (例如: 2h)\n• d - 天 (例如: 1d)\n• 支持组合格式 (例如: 1m30s, 2h15m, 1d12h)")
        time_info_label.setStyleSheet("font-size: 10px; color: #666; margin-top: 5px;")
        right_layout.addRow("", time_info_label)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("保存修改")
        self.save_btn.clicked.connect(self.save_food_data)
        
        self.refresh_btn = QPushButton("刷新列表")
        self.refresh_btn.clicked.connect(self.load_food_list_async)
        
        self.select_folder_btn = QPushButton("选择食物文件夹")
        self.select_folder_btn.clicked.connect(self.select_food_folder)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.select_folder_btn)
        
        # 将左右两部分放在主布局中
        main_h_layout = QHBoxLayout()
        main_h_layout.addWidget(left_group, 2)
        main_h_layout.addWidget(right_group, 1)
        
        layout.addLayout(main_h_layout)
        layout.addLayout(button_layout)
        
        # 初始化默认文件夹
        self.current_food_folder = "outfood"
    
    def scroll_changed(self, value):
        """滚动条变化时触发"""
        # 检查是否滚动到底部
        max_scroll = self.food_table.verticalScrollBar().maximum()
        if value >= max_scroll:
            # 加载更多数据
            self.load_more_data()
    
    def load_more_data(self):
        """加载更多数据"""
        if self.current_display_count < len(self.all_food_data):
            # 计算接下来要显示的数据
            start_idx = self.current_display_count
            end_idx = min(start_idx + self.load_batch_size, len(self.all_food_data))
            
            # 临时禁用排序和信号以提高性能
            self.food_table.setSortingEnabled(False)
            self.food_table.blockSignals(True)
            
            # 添加新行
            current_row_count = self.food_table.rowCount()
            rows_to_add = end_idx - start_idx
            self.food_table.setRowCount(current_row_count + rows_to_add)
            
            # 填充数据
            for i, idx in enumerate(range(start_idx, end_idx)):
                row = current_row_count + i
                row_data, _ = self.all_food_data[idx]
                
                for col, cell_data in enumerate(row_data):
                    self.food_table.setItem(row, col, QTableWidgetItem(cell_data))
            
            # 恢复排序和信号
            self.food_table.blockSignals(False)
            self.food_table.setSortingEnabled(True)
            
            # 更新当前显示计数
            self.current_display_count = end_idx
            
            # 更新进度信息
            self.progress_label.setText(f"已加载 {self.current_display_count}/{len(self.all_food_data)} 个项目")
            self.progress_label.setVisible(self.current_display_count < len(self.all_food_data))
    
    def select_food_folder(self):
        """选择食物文件夹"""
        folder_path = QFileDialog.getExistingDirectory(
            self, 
            "选择食物文件夹", 
            self.current_food_folder if os.path.exists(self.current_food_folder) else "."
        )
        
        if folder_path:
            self.current_food_folder = folder_path
            self.load_food_list_async()
    
    def load_food_list_async(self):
        """异步加载食物列表"""
        # 检查文件夹是否存在
        if not os.path.exists(self.current_food_folder):
            QMessageBox.warning(self, "警告", f"文件夹 '{self.current_food_folder}' 不存在！")
            return
        
        # 清空现有数据
        self.all_food_data = []
        self.current_display_count = 0
        self.food_table.setRowCount(0)
        
        # 显示加载提示
        self.food_table.setRowCount(1)
        self.food_table.setItem(0, 0, QTableWidgetItem("正在加载..."))
        self.food_table.setSpan(0, 0, 1, 7)  # 跨越所有列 (原来是6，现在是7)
        self.progress_label.setVisible(True)
        self.progress_label.setText("正在加载...")
        
        # 创建并启动后台线程
        self.load_worker = LoadFoodListWorker(self.current_food_folder)
        self.load_worker.finished.connect(self.on_load_finished)
        self.load_worker.progress.connect(self.update_progress)
        self.load_worker.start()
    
    def update_progress(self, current, total):
        """更新加载进度"""
        self.progress_label.setText(f"正在加载... {current}/{total}")
        self.progress_label.setVisible(True)
    
    def on_load_finished(self, data):
        """处理加载完成的回调"""
        self.all_food_data = data
        
        # 清空表格
        self.food_table.setRowCount(0)
        
        if not data:
            # 如果加载失败，显示错误信息
            self.food_table.setRowCount(1)
            self.food_table.setItem(0, 0, QTableWidgetItem("加载失败"))
            self.food_table.setSpan(0, 0, 1, 7)  # 跨越所有列 (原来是6，现在是7)
            self.progress_label.setVisible(False)
            return
        
        # 显示第一批数据
        self.display_initial_data()
        
        # 更新进度信息
        self.progress_label.setText(f"已加载 {self.current_display_count}/{len(self.all_food_data)} 个项目")
        self.progress_label.setVisible(self.current_display_count < len(self.all_food_data))
    
    def display_initial_data(self):
        """显示初始批次的数据"""
        # 设置表格行数
        end_idx = min(self.load_batch_size, len(self.all_food_data))
        self.food_table.setRowCount(end_idx)
        
        # 批量禁用排序和信号，提高插入性能
        self.food_table.setSortingEnabled(False)
        self.food_table.blockSignals(True)
        
        # 插入数据
        for row, idx in enumerate(range(0, end_idx)):
            row_data, _ = self.all_food_data[idx]
            for col, cell_data in enumerate(row_data):
                self.food_table.setItem(row, col, QTableWidgetItem(cell_data))
        
        # 恢复排序和信号
        self.food_table.blockSignals(False)
        self.food_table.setSortingEnabled(True)
        
        # 调整列宽
        self.food_table.resizeColumnsToContents()
        
        # 更新当前显示计数
        self.current_display_count = end_idx
    
    def on_food_selected(self, row, column):
        """当选择食物时，加载详细信息"""
        # 获取文件名
        file_item = self.food_table.item(row, 0)
        if not file_item:
            return
        
        file_name = file_item.text()
        image_path = os.path.join(self.current_food_folder, file_name)
        
        # 显示图片预览
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                200, 200,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_preview.setPixmap(scaled_pixmap)
        else:
            self.image_preview.setText("图片加载失败")
        
        # 加载食物信息
        success, data = FoodVerification.extract_food_info(image_path)
        
        if success:
            self.name_input.setText(data.get("FoodName", ""))
            self.description_input.setPlainText(data.get("FoodDescription", ""))
            self.calories_input.setText(str(data.get("FoodCalories", "")))
            self.water_input.setText(str(data.get("FoodWater", "")))
            self.time_input.setText(str(data.get("FoodTime", "")))  # 加载食用时间
            # 设置食物类型，如果类型不在预设列表中则添加到列表中
            food_type = data.get("FoodType", "未知类型")
            index = self.type_combo.findText(food_type)
            if index >= 0:
                self.type_combo.setCurrentIndex(index)
            else:
                self.type_combo.addItem(food_type)
                self.type_combo.setCurrentText(food_type)
            
            # 保存当前图片路径，用于后续保存
            self.current_image_path = image_path
        else:
            # 如果图片中没有食物信息，设置默认值
            self.name_input.setText("未命名食物")
            self.description_input.setPlainText("这是一个未命名的食物")
            self.calories_input.setText("100")
            self.water_input.setText("50")
            self.time_input.setText("10m")  # 设置默认食用时间
            self.type_combo.setCurrentText("其他")  # 设置默认食物类型
            
            # 保存当前图片路径，用于后续保存
            self.current_image_path = image_path
    
    def save_food_data(self):
        """保存食物数据到图片"""
        if not hasattr(self, 'current_image_path') or self.current_image_path is None:
            QMessageBox.warning(self, "警告", "请先选择一个食物项目进行编辑！")
            return
        
        # 获取输入的值
        food_name = self.name_input.text().strip()
        food_description = self.description_input.toPlainText().strip()
        food_calories = self.calories_input.text().strip()
        food_water = self.water_input.text().strip()
        food_time = self.time_input.text().strip()  # 获取食用时间
        food_type = self.type_combo.currentText()  # 获取食物类型
        
        # 验证必填字段
        if not food_name:
            QMessageBox.warning(self, "警告", "请输入食物名称！")
            return
        
        if not food_calories:
            QMessageBox.warning(self, "警告", "请输入食物热量！")
            return
        
        if not food_water:
            QMessageBox.warning(self, "警告", "请输入食物水分！")
            return
        
        # 验证数值字段
        try:
            int(food_calories)
            int(food_water)
        except ValueError:
            QMessageBox.warning(self, "警告", "食物热量和食物水分必须是数字！")
            return
        
        # 验证食用时间格式
        if food_time:  # 如果输入了食用时间，则验证格式
            is_valid, error_msg = FoodVerification.validate_food_time_format(food_time)
            if not is_valid:
                QMessageBox.warning(self, "警告", error_msg)
                return
        
        # 禁用保存按钮，防止重复点击
        self.save_btn.setEnabled(False)
        self.save_btn.setText("保存中...")
        
        # 创建并启动后台线程
        self.worker = SaveFoodDataWorker(
            self.current_image_path,
            food_name,
            food_description,
            food_calories,
            food_water,
            food_time,
            food_type  # 添加食物类型参数
        )
        self.worker.finished.connect(self.on_save_finished)
        self.worker.start()
    
    def on_save_finished(self, success, message):
        """处理保存完成的回调"""
        # 重新启用保存按钮
        self.save_btn.setEnabled(True)
        self.save_btn.setText("保存修改")
        
        if success:
            QMessageBox.information(self, "成功", message)
            # 刷新列表
            self.load_food_list_async()
        else:
            QMessageBox.critical(self, "错误", message)
        
        # 清理线程对象
        self.worker = None


def main():
    """启动食物数据编辑器"""
    app = QApplication([])
    editor = FoodEditorWindow()
    editor.show()
    app.exec()


if __name__ == "__main__":
    main()