#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fitz
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea
from PyQt5.QtGui import QPixmap, QPainter, QPen, QImage
from PyQt5.QtCore import Qt, QRect, pyqtSignal, QPoint
import numpy as np
import os

class PDFViewer(QWidget):
    # 自定义信号
    page_changed = pyqtSignal(int, int)  # 当前页码, 总页数
    document_loaded = pyqtSignal()  # 文档加载完成
    selection_changed = pyqtSignal(QRect)  # 选择区域变化
    zoom_changed = pyqtSignal(float)  # 缩放比例变化
    
    def __init__(self):
        super().__init__()
        
        self.doc = None
        self.current_page = 0
        self.total_pages = 0
        self.zoom_factor = 1.0
        
        # 选择区域
        self.selection_start = None
        self.selection_end = None
        self.selecting = False
        self.selection_rect = None
        
        self.init_ui()
    
    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        
        # 图像标签
        self.image_label = PDFLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.selection_changed.connect(self.update_selection)
        
        self.scroll_area.setWidget(self.image_label)
        self.layout.addWidget(self.scroll_area)
    
    def load_pdf(self, pdf_path):
        """加载PDF文件"""
        try:
            self.doc = fitz.open(pdf_path)
            self.total_pages = len(self.doc)
            self.current_page = 0
            self.render_page()
            self.document_loaded.emit()
            self.page_changed.emit(self.current_page, self.total_pages)
            return True
        except Exception as e:
            print(f"加载PDF时出错: {e}")
            return False
    
    def render_page(self):
        """渲染当前页面"""
        if not self.doc:
            return
        
        # 清除选择
        self.clear_selection()
        
        page = self.doc.load_page(self.current_page)
        
        # 设置缩放因子
        zoom_matrix = fitz.Matrix(self.zoom_factor, self.zoom_factor)
        pix = page.get_pixmap(matrix=zoom_matrix)
        
        # 创建QImage
        img_format = QImage.Format_RGBA8888 if pix.alpha else QImage.Format_RGB888
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, img_format)
        
        # 转换为QPixmap并显示
        pixmap = QPixmap.fromImage(img)
        self.image_label.setPixmap(pixmap)
        self.image_label.adjustSize()
    
    def prev_page(self):
        """显示上一页"""
        if self.doc and self.current_page > 0:
            self.current_page -= 1
            self.render_page()
            self.page_changed.emit(self.current_page, self.total_pages)
    
    def next_page(self):
        """显示下一页"""
        if self.doc and self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.render_page()
            self.page_changed.emit(self.current_page, self.total_pages)
    
    def jump_to_page(self, page_num):
        """跳转到指定页面"""
        if self.doc and 0 <= page_num < self.total_pages:
            self.current_page = page_num
            self.render_page()
            self.page_changed.emit(self.current_page, self.total_pages)
    
    def zoom(self, factor):
        """缩放视图"""
        if not self.doc:
            return
        
        # 保存滚动位置
        h_value = self.scroll_area.horizontalScrollBar().value()
        v_value = self.scroll_area.verticalScrollBar().value()
        
        # 计算新的缩放因子
        old_zoom = self.zoom_factor
        self.zoom_factor *= factor
        
        # 限制缩放范围
        if self.zoom_factor < 0.1:
            self.zoom_factor = 0.1
        elif self.zoom_factor > 5.0:
            self.zoom_factor = 5.0
        
        # 重新渲染页面
        self.render_page()
        
        # 调整滚动位置以保持视图中心
        scale = self.zoom_factor / old_zoom
        self.scroll_area.horizontalScrollBar().setValue(int(h_value * scale))
        self.scroll_area.verticalScrollBar().setValue(int(v_value * scale))
        
        # 发出缩放变化信号
        self.zoom_changed.emit(self.zoom_factor)
    
    def update_selection(self, rect):
        """更新选择区域"""
        self.selection_rect = rect
        self.selection_changed.emit(rect)
    
    def clear_selection(self):
        """清除选择区域"""
        self.selection_start = None
        self.selection_end = None
        self.selecting = False
        self.selection_rect = None
        if hasattr(self.image_label, 'clear_selection'):
            self.image_label.clear_selection()
    
    def has_selection(self):
        """检查是否有选择区域"""
        return self.image_label.has_selection()
    
    def get_selection_rect(self):
        """获取文档坐标系中的选择区域"""
        if not self.has_selection() or not self.doc:
            return None
        
        # 获取界面上的选择区域
        ui_rect = self.image_label.get_selection_rect()
        if not ui_rect:
            return None
        
        # 转换为文档坐标系
        page = self.doc.load_page(self.current_page)
        page_rect = page.rect
        
        # 获取缩放后的图像尺寸
        pixmap = self.image_label.pixmap()
        if not pixmap:
            return None
        
        img_width = pixmap.width()
        img_height = pixmap.height()
        
        # 获取图像在标签中的实际位置（考虑居中对齐）
        label_width = self.image_label.width()
        label_height = self.image_label.height()
        
        # 计算图像偏移
        x_offset = (label_width - img_width) / 2 if label_width > img_width else 0
        y_offset = (label_height - img_height) / 2 if label_height > img_height else 0
        
        # 考虑偏移量调整选区坐标
        adj_left = max(0, ui_rect.left() - x_offset)
        adj_top = max(0, ui_rect.top() - y_offset)
        adj_right = min(img_width, ui_rect.right() - x_offset)
        adj_bottom = min(img_height, ui_rect.bottom() - y_offset)
        
        # 检查调整后的坐标是否有效
        if adj_left >= adj_right or adj_top >= adj_bottom:
            print("调整后的选择区域无效")
            return None
        
        # 这里直接返回UI坐标系中的坐标
        # 现在我们知道PyMuPDF内部会进行坐标转换（从右上角原点到左上角原点）
        # 因此我们只需传递原始UI坐标，不需要做额外转换
        # 记录坐标信息用于调试
        print(f"UI选区: {ui_rect}")
        print(f"调整后选区: ({adj_left}, {adj_top}, {adj_right}, {adj_bottom})")
        print(f"缩放比例: {self.zoom_factor}")
        
        # 返回UI坐标系下的选区
        return fitz.Rect(adj_left, adj_top, adj_right, adj_bottom)


class PDFLabel(QLabel):
    """可选择区域的PDF标签"""
    selection_changed = pyqtSignal(QRect)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selection_start = None
        self.selection_end = None
        self.selecting = False
        self.selection_rect = None
    
    def mousePressEvent(self, event):
        """鼠标按下事件，开始选择"""
        if event.button() == Qt.LeftButton and self.pixmap():
            self.selection_start = event.pos()
            self.selection_end = event.pos()
            self.selecting = True
            self.selection_rect = QRect(self.selection_start, self.selection_end)
            self.update()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件，更新选择区域"""
        if self.selecting and self.pixmap():
            self.selection_end = event.pos()
            self.selection_rect = QRect(self.selection_start, self.selection_end).normalized()
            self.update()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件，完成选择"""
        if self.selecting and event.button() == Qt.LeftButton and self.pixmap():
            self.selecting = False
            self.selection_end = event.pos()
            self.selection_rect = QRect(self.selection_start, self.selection_end).normalized()
            
            # 确保选择区域在图像范围内
            pixmap_rect = self.pixmap().rect()
            self.selection_rect = self.selection_rect.intersected(pixmap_rect)
            
            self.selection_changed.emit(self.selection_rect)
            self.update()
    
    def paintEvent(self, event):
        """绘制事件，显示选择区域"""
        super().paintEvent(event)
        
        if self.selection_rect and self.pixmap():
            painter = QPainter(self)
            pen = QPen(Qt.red, 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(self.selection_rect)
    
    def clear_selection(self):
        """清除选择区域"""
        self.selection_start = None
        self.selection_end = None
        self.selecting = False
        self.selection_rect = None
        self.update()
    
    def has_selection(self):
        """检查是否有选择区域"""
        return self.selection_rect is not None and not self.selection_rect.isEmpty()
    
    def get_selection_rect(self):
        """获取选择区域"""
        return self.selection_rect 