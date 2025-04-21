#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import QObject, pyqtSignal, QRect, QPoint, Qt
from PyQt5.QtGui import QPainter, QPen, QColor
import fitz

class RegionSelector(QObject):
    """
    区域选择器类，用于处理PDF上的区域选择逻辑
    主要功能已在PDFLabel类中实现，此类提供额外的功能扩展
    """
    region_selected = pyqtSignal(fitz.Rect)  # 区域选择完成信号
    selection_changed = pyqtSignal(QRect)    # 选择区域变化信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_point = None
        self.end_point = None
        self.is_selecting = False
        self.selection_rect = None
        self.pdf_rect = None     # PDF文档的原始尺寸
        self.view_rect = None    # 显示视图的尺寸
        self.zoom_factor = 1.0   # 当前缩放因子
    
    def start_selection(self, point):
        """
        开始选择区域
        
        Args:
            point (QPoint): 起始点
        """
        self.start_point = point
        self.end_point = point
        self.is_selecting = True
        self.selection_rect = QRect(point, point)
        self.selection_changed.emit(self.selection_rect)
    
    def update_selection(self, point):
        """
        更新选择区域
        
        Args:
            point (QPoint): 当前点
        """
        if not self.is_selecting:
            return
            
        self.end_point = point
        self.selection_rect = QRect(self.start_point, self.end_point).normalized()
        self.selection_changed.emit(self.selection_rect)
    
    def end_selection(self, point):
        """
        结束选择区域
        
        Args:
            point (QPoint): 结束点
        """
        if not self.is_selecting:
            return
            
        self.is_selecting = False
        self.end_point = point
        self.selection_rect = QRect(self.start_point, self.end_point).normalized()
        
        # 转换为PDF坐标系的Rect
        pdf_rect = self.convert_to_pdf_rect(self.selection_rect)
        if pdf_rect:
            self.region_selected.emit(pdf_rect)
        
        self.selection_changed.emit(self.selection_rect)
    
    def clear_selection(self):
        """清除选择区域"""
        self.start_point = None
        self.end_point = None
        self.is_selecting = False
        self.selection_rect = None
        self.selection_changed.emit(QRect())
    
    def set_document_size(self, pdf_rect, view_rect, zoom):
        """
        设置文档尺寸和显示尺寸，用于坐标转换
        
        Args:
            pdf_rect (fitz.Rect): PDF页面的尺寸
            view_rect (QRect): 显示视图的尺寸
            zoom (float): 缩放因子
        """
        self.pdf_rect = pdf_rect
        self.view_rect = view_rect
        self.zoom_factor = zoom
    
    def convert_to_pdf_rect(self, ui_rect):
        """
        将UI坐标系的矩形转换为PDF坐标系的矩形
        
        Args:
            ui_rect (QRect): UI坐标系中的矩形
            
        Returns:
            fitz.Rect: PDF坐标系中的矩形，如果转换失败则返回None
        """
        if not self.pdf_rect or not self.view_rect:
            return None
        
        # 计算缩放比例
        x_ratio = self.pdf_rect.width / self.view_rect.width() * self.zoom_factor
        y_ratio = self.pdf_rect.height / self.view_rect.height() * self.zoom_factor
        
        # 转换坐标
        x0 = ui_rect.left() * x_ratio
        y0 = ui_rect.top() * y_ratio
        x1 = ui_rect.right() * x_ratio
        y1 = ui_rect.bottom() * y_ratio
        
        return fitz.Rect(x0, y0, x1, y1)
    
    def convert_to_ui_rect(self, pdf_rect):
        """
        将PDF坐标系的矩形转换为UI坐标系的矩形
        
        Args:
            pdf_rect (fitz.Rect): PDF坐标系中的矩形
            
        Returns:
            QRect: UI坐标系中的矩形，如果转换失败则返回None
        """
        if not self.pdf_rect or not self.view_rect:
            return None
        
        # 计算缩放比例
        x_ratio = self.view_rect.width() / self.pdf_rect.width / self.zoom_factor
        y_ratio = self.view_rect.height() / self.pdf_rect.height / self.zoom_factor
        
        # 转换坐标
        left = int(pdf_rect.x0 * x_ratio)
        top = int(pdf_rect.y0 * y_ratio)
        right = int(pdf_rect.x1 * x_ratio)
        bottom = int(pdf_rect.y1 * y_ratio)
        
        return QRect(left, top, right - left, bottom - top)
    
    def draw_selection(self, painter):
        """
        绘制选择区域
        
        Args:
            painter (QPainter): 绘图对象
        """
        if not self.selection_rect:
            return
            
        # 保存原始画笔
        original_pen = painter.pen()
        
        # 设置红色虚线画笔绘制选择框
        pen = QPen(QColor(255, 0, 0, 180), 2, Qt.DashLine)
        painter.setPen(pen)
        painter.drawRect(self.selection_rect)
        
        # 恢复原始画笔
        painter.setPen(original_pen)


# 辅助函数
def normalize_rect(rect):
    """
    确保矩形的左上角坐标小于右下角坐标
    
    Args:
        rect (fitz.Rect): 要规范化的矩形
        
    Returns:
        fitz.Rect: 规范化后的矩形
    """
    x0, y0, x1, y1 = rect
    if x0 > x1:
        x0, x1 = x1, x0
    if y0 > y1:
        y0, y1 = y1, y0
    return fitz.Rect(x0, y0, x1, y1) 