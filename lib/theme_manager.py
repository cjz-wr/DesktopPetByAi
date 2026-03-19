"""
主题管理器 - 负责界面美化和动画效果
"""

import os
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton
from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, pyqtProperty, QObject, QEvent

class ThemeManager:
    """主题管理器类"""
    
    THEMES = {
        'green': 'themes/green_theme_fixed.qss',
        'blue': 'themes/blue_theme.qss',
        'pink': 'themes/pink_theme.qss'
    }
    
    @staticmethod
    def load_theme(theme_name='green'):
        """加载指定主题"""
        theme_path = ThemeManager.THEMES.get(theme_name, ThemeManager.THEMES['green'])
        if os.path.exists(theme_path):
            try:
                with open(theme_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"加载主题文件失败: {e}")
                return ""
        return ""
    
    @staticmethod
    def apply_theme(widget, theme_name='green'):
        """应用主题到指定控件"""
        stylesheet = ThemeManager.load_theme(theme_name)
        if stylesheet:
            widget.setStyleSheet(stylesheet)
            return True
        return False

class AnimationManager(QObject):
    """动画管理器类"""
    
    @staticmethod
    def create_hover_animation(widget, duration=200):
        """创建悬停动画效果"""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.OutBack)
        return animation
    
    @staticmethod
    def create_fade_animation(widget, duration=300):
        """创建淡入淡出动画"""
        animation = QPropertyAnimation(widget, b"windowOpacity")
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        return animation
    
    @staticmethod
    def create_scale_animation(widget, duration=150):
        """创建缩放动画"""
        # 这里需要自定义属性来实现缩放效果
        class ScaleWidget(QWidget):
            def __init__(self, parent=None):
                super().__init__(parent)
                self._scale_factor = 1.0
            
            def getScaleFactor(self):
                return self._scale_factor
            
            def setScaleFactor(self, factor):
                self._scale_factor = factor
                self.updateGeometry()
            
            scaleFactor = pyqtProperty(float, getScaleFactor, setScaleFactor)
        
        animation = QPropertyAnimation(ScaleWidget(widget), b"scaleFactor")
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.OutBack)
        return animation

class WidgetEnhancer:
    """控件增强器 - 为控件添加美化效果"""
    
    @staticmethod
    def enhance_button(button, style_type='primary'):
        """增强按钮样式和动画"""
        if not isinstance(button, QPushButton):
            return
        
        # 设置对象名称便于样式定位
        button.setObjectName(f"enhanced-button-{style_type}")
        
        # 安装事件过滤器实现悬停效果
        original_enter_event = button.enterEvent
        original_leave_event = button.leaveEvent
        
        def enhanced_enter_event(event):
            # 添加悬停动画
            WidgetEnhancer._apply_hover_effect(button, True)
            if original_enter_event:
                original_enter_event(event)
        
        def enhanced_leave_event(event):
            # 移除悬停动画
            WidgetEnhancer._apply_hover_effect(button, False)
            if original_leave_event:
                original_leave_event(event)
        
        button.enterEvent = enhanced_enter_event
        button.leaveEvent = enhanced_leave_event
    
    @staticmethod
    def _apply_hover_effect(button, is_hover):
        """应用悬停效果"""
        if is_hover:
            # 悬停时的动画
            animation = QPropertyAnimation(button, b"geometry")
            animation.setDuration(150)
            animation.setStartValue(button.geometry())
            
            # 计算稍微放大后的位置
            geom = button.geometry()
            new_width = int(geom.width() * 1.05)
            new_height = int(geom.height() * 1.05)
            dx = (geom.width() - new_width) // 2
            dy = (geom.height() - new_height) // 2
            
            new_geom = geom.adjusted(dx, dy, -dx, -dy)
            animation.setEndValue(new_geom)
            animation.setEasingCurve(QEasingCurve.Type.OutBack)
            animation.start()
        else:
            # 恢复原始大小
            animation = QPropertyAnimation(button, b"geometry")
            animation.setDuration(150)
            animation.setStartValue(button.geometry())
            animation.setEndValue(button.geometry())  # 这里应该恢复到原始几何位置
            animation.setEasingCurve(QEasingCurve.Type.InBack)
            animation.start()
    
    @staticmethod
    def enhance_card_widget(widget):
        """增强卡片控件效果"""
        widget.setObjectName("enhanced-card")
        widget.installEventFilter(CardEventFilter(widget))

class CardEventFilter(QObject):
    """卡片事件过滤器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Enter:
            self._apply_card_hover_effect(obj, True)
            return True
        elif event.type() == QEvent.Type.Leave:
            self._apply_card_hover_effect(obj, False)
            return True
        return False
    
    def _apply_card_hover_effect(self, widget, is_hover):
        """应用卡片悬停效果"""
        if is_hover:
            # 提升效果
            animation = QPropertyAnimation(widget, b"geometry")
            animation.setDuration(200)
            geom = widget.geometry()
            new_geom = geom.adjusted(0, -3, 0, 3)
            animation.setStartValue(geom)
            animation.setEndValue(new_geom)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            animation.start()
        else:
            # 恢复原位
            animation = QPropertyAnimation(widget, b"geometry")
            animation.setDuration(200)
            geom = widget.geometry()
            original_geom = geom.adjusted(0, 3, 0, -3)
            animation.setStartValue(geom)
            animation.setEndValue(original_geom)
            animation.setEasingCurve(QEasingCurve.Type.InCubic)
            animation.start()

class StyleHelper:
    """样式助手类"""
    
    @staticmethod
    def create_card_style(title, background_gradient=None):
        """创建卡片样式"""
        if background_gradient is None:
            background_gradient = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #F8FFF8, stop:1 #E8F5E8)"
        
        return f"""
        #{title.lower().replace(' ', '-')}-card {{
            background: {background_gradient};
            border-radius: 15px;
            padding: 25px;
            margin: 15px;
            border: 1px solid #E8F5E8;
            transition: all 0.3s ease;
        }}
        
        #{title.lower().replace(' ', '-')}-card:hover {{
            transform: translateY(-3px);
        }}
        
        #{title.lower().replace(' ', '-')}-card QLabel {{
            color: #2F4F2F;
            font-weight: 500;
        }}
        """
    
    @staticmethod
    def create_button_style(color_primary, color_hover, color_pressed):
        """创建按钮样式"""
        return f"""
        QPushButton {{
            background-color: {color_primary};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 500;
            min-height: 30px;
            transition: all 0.2s ease;
        }}
        
        QPushButton:hover {{
            background-color: {color_hover};
            transform: translateY(-2px);
        }}
        
        QPushButton:pressed {{
            background-color: {color_pressed};
            transform: translateY(0);
        }}
        """
    
    @staticmethod
    def _hex_to_rgba(hex_color):
        """将十六进制颜色转换为RGBA字符串"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            return f"{r}, {g}, {b}"
        return "143, 188, 143"

# 使用示例函数
def apply_beautiful_theme(dialog):
    """为对话框应用美化主题"""
    # 应用主题
    ThemeManager.apply_theme(dialog, 'green')
    
    # 增强按钮效果
    for button in dialog.findChildren(QPushButton):
        WidgetEnhancer.enhance_button(button)
    
    # 增强卡片效果
    for widget in dialog.findChildren(QWidget):
        if 'card' in widget.objectName().lower():
            WidgetEnhancer.enhance_card_widget(widget)

if __name__ == "__main__":
    # 测试代码
    app = QApplication([])
    from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton
    
    dialog = QDialog()
    layout = QVBoxLayout(dialog)
    
    button = QPushButton("测试按钮")
    layout.addWidget(button)
    
    apply_beautiful_theme(dialog)
    dialog.show()
    
    app.exec()