#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import shutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, 
                            QVBoxLayout, QHBoxLayout, QWidget, QPushButton, 
                            QLabel, QTextEdit, QSplitter, QMessageBox, QAction, QToolBar,
                            QLineEdit, QSpinBox)
from PyQt5.QtCore import Qt, QSize, QEvent
from PyQt5.QtGui import QIcon, QKeySequence

from pdf_viewer import PDFViewer
from text_extractor import extract_text_from_region

class PDFSelectorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.current_pdf_path = None
        self.extracted_image_path = None
        self.current_extract_folder = None
        
    def init_ui(self):
        # 设置窗口基本属性
        self.setWindowTitle("PDF 区域选择与文本提取工具")
        self.setGeometry(100, 100, 1400, 900)
        
        # 创建菜单栏
        self.create_menu()
        
        # 创建工具栏
        self.create_toolbar()
        
        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧面板 - PDF 查看器
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        self.pdf_viewer = PDFViewer()
        left_layout.addWidget(self.pdf_viewer)
        
        # 页面导航和缩放控件
        nav_layout = QHBoxLayout()
        
        # 页面导航
        self.prev_button = QPushButton("上一页")
        self.next_button = QPushButton("下一页")
        self.page_label = QLabel("页面: 0 / 0")
        self.page_label.setAlignment(Qt.AlignCenter)
        
        # 页码跳转
        self.page_jump_layout = QHBoxLayout()
        self.page_jump_layout.addWidget(QLabel("跳转到:"))
        self.page_spinbox = QSpinBox()
        self.page_spinbox.setMinimum(1)  # 页码从1开始
        self.page_spinbox.setMaximum(1)  # 初始最大值为1，后续会更新
        self.page_jump_button = QPushButton("跳转")
        
        self.page_jump_layout.addWidget(self.page_spinbox)
        self.page_jump_layout.addWidget(self.page_jump_button)
        
        # 缩放控件
        zoom_layout = QHBoxLayout()
        self.zoom_out_button = QPushButton("缩小")
        self.zoom_in_button = QPushButton("放大")
        self.zoom_label = QLabel("缩放: 100%")
        self.zoom_label.setAlignment(Qt.AlignCenter)
        
        zoom_layout.addWidget(self.zoom_out_button)
        zoom_layout.addWidget(self.zoom_label)
        zoom_layout.addWidget(self.zoom_in_button)
        
        # 添加导航和缩放控件
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.page_label)
        nav_layout.addWidget(self.next_button)
        nav_layout.addStretch()
        nav_layout.addLayout(self.page_jump_layout)
        nav_layout.addStretch()
        nav_layout.addLayout(zoom_layout)
        
        left_layout.addLayout(nav_layout)
        
        # 右侧面板 - 使用垂直分割器
        right_panel = QSplitter(Qt.Vertical)
        
        # 上半部分 - 文本区域
        upper_right_panel = QWidget()
        upper_right_layout = QVBoxLayout(upper_right_panel)
        
        upper_right_layout.addWidget(QLabel("提取的文本:"))
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        upper_right_layout.addWidget(self.text_edit)
        
        # 下半部分 - 转换结果表格
        lower_right_panel = QWidget()
        lower_right_layout = QVBoxLayout(lower_right_panel)
        
        lower_right_layout.addWidget(QLabel("不同坐标系转换结果:"))
        
        # 创建表格显示转换结果
        from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
        from PyQt5.QtGui import QPixmap
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["转换方式", "预览图", "提取文本"])
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        
        lower_right_layout.addWidget(self.results_table)
        
        # 右侧按钮区
        button_layout = QHBoxLayout()
        self.extract_button = QPushButton("提取文本")
        self.save_text_button = QPushButton("保存文本")
        self.save_image_button = QPushButton("保存区域图像")
        self.open_folder_button = QPushButton("打开输出文件夹")
        
        button_layout.addWidget(self.extract_button)
        button_layout.addWidget(self.save_text_button)
        button_layout.addWidget(self.save_image_button)
        button_layout.addWidget(self.open_folder_button)
        
        lower_right_layout.addLayout(button_layout)
        
        # 添加到右侧分割器
        right_panel.addWidget(upper_right_panel)
        right_panel.addWidget(lower_right_panel)
        right_panel.setSizes([300, 600])  # 设置初始大小分配
        
        # 添加到主分割器
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([700, 700])
        
        main_layout.addWidget(splitter)
        
        # 连接信号和槽
        self.connect_signals()
        
        # 初始禁用部分控件
        self.update_ui_state(False)
        
        # 安装事件过滤器用于全局键盘快捷键
        self.installEventFilter(self)
    
    def create_menu(self):
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        open_action = QAction("打开", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_pdf)
        
        save_text_action = QAction("保存文本", self)
        save_text_action.setShortcut(QKeySequence.Save)
        save_text_action.triggered.connect(self.save_text)
        
        open_folder_action = QAction("打开输出文件夹", self)
        open_folder_action.triggered.connect(self.open_output_folder)
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        
        file_menu.addAction(open_action)
        file_menu.addAction(save_text_action)
        file_menu.addAction(open_folder_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图")
        
        zoom_in_action = QAction("放大", self)
        zoom_in_action.setShortcut(Qt.Key_Plus)  # 设置为加号键
        zoom_in_action.triggered.connect(self.zoom_in)
        
        zoom_out_action = QAction("缩小", self)
        zoom_out_action.setShortcut(Qt.Key_Minus)  # 设置为减号键
        zoom_out_action.triggered.connect(self.zoom_out)
        
        view_menu.addAction(zoom_in_action)
        view_menu.addAction(zoom_out_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        toolbar = QToolBar("工具栏")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)
        
        open_action = QAction("打开PDF", self)
        open_action.triggered.connect(self.open_pdf)
        
        extract_action = QAction("提取文本", self)
        extract_action.triggered.connect(self.extract_text)
        
        open_folder_action = QAction("打开输出文件夹", self)
        open_folder_action.triggered.connect(self.open_output_folder)
        
        toolbar.addAction(open_action)
        toolbar.addAction(extract_action)
        toolbar.addAction(open_folder_action)
    
    def connect_signals(self):
        # 页面导航按钮
        self.prev_button.clicked.connect(self.pdf_viewer.prev_page)
        self.next_button.clicked.connect(self.pdf_viewer.next_page)
        
        # 页码跳转
        self.page_jump_button.clicked.connect(self.jump_to_page)
        
        # 缩放按钮
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.zoom_out_button.clicked.connect(self.zoom_out)
        
        # 文本提取按钮
        self.extract_button.clicked.connect(self.extract_text)
        self.save_text_button.clicked.connect(self.save_text)
        self.save_image_button.clicked.connect(self.save_image)
        self.open_folder_button.clicked.connect(self.open_output_folder)
        
        # PDF查看器信号
        self.pdf_viewer.page_changed.connect(self.update_page_label)
        self.pdf_viewer.document_loaded.connect(self.on_document_loaded)
        self.pdf_viewer.zoom_changed.connect(self.update_zoom_label)
    
    def update_ui_state(self, has_document):
        """根据是否加载了文档更新UI状态"""
        self.prev_button.setEnabled(has_document)
        self.next_button.setEnabled(has_document)
        self.extract_button.setEnabled(has_document)
        self.save_text_button.setEnabled(False)  # 只在有文本时启用
        self.save_image_button.setEnabled(False)  # 只在有选定区域图像时启用
        self.open_folder_button.setEnabled(False)  # 只在有输出文件夹时启用
        self.zoom_in_button.setEnabled(has_document)
        self.zoom_out_button.setEnabled(has_document)
        self.page_spinbox.setEnabled(has_document)
        self.page_jump_button.setEnabled(has_document)
    
    def open_pdf(self):
        """打开PDF文件并加载到查看器"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开PDF文件", "", "PDF文件 (*.pdf)"
        )
        if file_path:
            self.current_pdf_path = file_path
            self.pdf_viewer.load_pdf(file_path)
            self.text_edit.clear()
            
            # 重置当前提取结果
            self.extracted_image_path = None
            self.current_extract_folder = None
            self.update_extraction_ui_state(False)
            
            # 更新页码范围
            if self.pdf_viewer.total_pages > 0:
                self.page_spinbox.setMaximum(self.pdf_viewer.total_pages)
                self.page_spinbox.setValue(1)  # 默认跳转到第1页
    
    def extract_text(self):
        """从选定区域提取文本"""
        if not self.current_pdf_path or not self.pdf_viewer.has_selection():
            QMessageBox.warning(self, "警告", "请先打开PDF文件并选择区域")
            return
        
        rect = self.pdf_viewer.get_selection_rect()
        page_num = self.pdf_viewer.current_page
        
        text, image_path, output_folder = extract_text_from_region(self.current_pdf_path, page_num, rect)
        if text:
            self.text_edit.setText(text)
            self.extracted_image_path = image_path
            # 获取输出文件夹路径
            self.current_extract_folder = output_folder
            self.update_extraction_ui_state(True)
            
            # 显示所有转换结果
            self.display_transform_results(output_folder)
            
            # 显示成功提示
            QMessageBox.information(
                self, 
                "提取成功", 
                f"文本和图像已保存到文件夹:\n{self.current_extract_folder}"
            )
        else:
            QMessageBox.warning(self, "提取失败", "从选定区域提取文本失败")
    
    def update_extraction_ui_state(self, has_extraction):
        """更新与提取相关的UI状态"""
        self.save_text_button.setEnabled(has_extraction)
        self.save_image_button.setEnabled(has_extraction)
        self.open_folder_button.setEnabled(has_extraction)
    
    def save_text(self):
        """保存提取的文本到自定义位置"""
        if not self.text_edit.toPlainText():
            QMessageBox.warning(self, "警告", "没有可保存的文本")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存文本", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.text_edit.toPlainText())
                QMessageBox.information(self, "成功", f"文本已保存到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "保存失败", f"保存文本时出错: {e}")
    
    def save_image(self):
        """保存提取的区域图像到自定义位置"""
        if not self.extracted_image_path or not os.path.exists(self.extracted_image_path):
            QMessageBox.warning(self, "警告", "提取的区域图像不存在")
            return
        
        target_path, _ = QFileDialog.getSaveFileName(
            self, "保存区域图像", "", "PNG图像 (*.png);;所有文件 (*)"
        )
        
        if target_path:
            try:
                shutil.copy2(self.extracted_image_path, target_path)
                QMessageBox.information(self, "成功", f"图像已保存到: {target_path}")
            except Exception as e:
                QMessageBox.critical(self, "保存失败", f"保存图像时出错: {e}")
    
    def open_output_folder(self):
        """打开输出文件夹"""
        if not self.current_extract_folder or not os.path.exists(self.current_extract_folder):
            QMessageBox.warning(self, "警告", "输出文件夹不存在")
            return
        
        # 打开文件夹
        if sys.platform == 'win32':
            os.startfile(self.current_extract_folder)
        elif sys.platform == 'darwin':  # macOS
            os.system(f'open "{self.current_extract_folder}"')
        else:  # Linux
            os.system(f'xdg-open "{self.current_extract_folder}"')
    
    def zoom_in(self):
        """放大PDF视图"""
        if self.pdf_viewer.doc:
            self.pdf_viewer.zoom(1.2)
    
    def zoom_out(self):
        """缩小PDF视图"""
        if self.pdf_viewer.doc:
            self.pdf_viewer.zoom(0.8)
    
    def jump_to_page(self):
        """跳转到指定页码"""
        if not self.pdf_viewer.doc:
            return
            
        page_num = self.page_spinbox.value() - 1  # 转换为0基索引
        if 0 <= page_num < self.pdf_viewer.total_pages:
            self.pdf_viewer.jump_to_page(page_num)
    
    def update_page_label(self, current, total):
        """更新页面标签显示"""
        self.page_label.setText(f"页面: {current + 1} / {total}")
        # 更新页码微调框的值，但不触发跳转
        self.page_spinbox.blockSignals(True)
        self.page_spinbox.setValue(current + 1)
        self.page_spinbox.blockSignals(False)
    
    def update_zoom_label(self, zoom_factor):
        """更新缩放标签显示"""
        zoom_percent = int(zoom_factor * 100)
        self.zoom_label.setText(f"缩放: {zoom_percent}%")
    
    def on_document_loaded(self):
        """文档加载完成后的回调"""
        self.update_ui_state(True)
        self.update_zoom_label(self.pdf_viewer.zoom_factor)
    
    def eventFilter(self, obj, event):
        """事件过滤器用于处理全局键盘快捷键"""
        if event.type() == QEvent.KeyPress:
            # 处理+键和-键用于缩放
            if event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
                self.zoom_in()
                return True
            elif event.key() == Qt.Key_Minus:
                self.zoom_out()
                return True
        return super().eventFilter(obj, event)
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于",
            "PDF区域选择与文本提取工具\n\n"
            "一个使用PyMuPDF和Qt开发的工具，可以可视化地选择PDF文档中的区域并提取文本内容。\n"
            "提取的内容会保存在以时间戳命名的文件夹中。"
        )

    def display_transform_results(self, folder_path):
        """在表格中显示所有坐标转换的结果"""
        import json
        import os
        from PyQt5.QtWidgets import QTableWidgetItem
        from PyQt5.QtGui import QPixmap
        from PyQt5.QtCore import Qt
        
        # 查找JSON调试文件
        json_files = [f for f in os.listdir(folder_path) if f.endswith('_transforms.json')]
        if not json_files:
            return
        
        # 读取JSON文件
        json_path = os.path.join(folder_path, json_files[0])
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                debug_info = json.load(f)
        except Exception as e:
            print(f"读取调试文件失败: {e}")
            return
        
        # 清空表格
        self.results_table.setRowCount(0)
        
        # 填充表格
        transforms = debug_info.get("transforms", [])
        for i, transform in enumerate(transforms):
            self.results_table.insertRow(i)
            
            # 转换名称及描述
            name_item = QTableWidgetItem(transform.get("name", "未知"))
            if "description" in transform:
                name_item.setToolTip(transform.get("description"))
            self.results_table.setItem(i, 0, name_item)
            
            # 预览图像
            image_path = transform.get("image_path")
            if image_path and os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    # 缩放图像到合适大小
                    pixmap = pixmap.scaledToHeight(150, Qt.SmoothTransformation)
                    
                    # 创建标签显示图像
                    from PyQt5.QtWidgets import QLabel
                    image_label = QLabel()
                    image_label.setPixmap(pixmap)
                    image_label.setAlignment(Qt.AlignCenter)
                    image_label.setScaledContents(False)
                    
                    self.results_table.setCellWidget(i, 1, image_label)
            
            # 提取文本
            text = transform.get("text", "")
            text_item = QTableWidgetItem(text if text else "未提取到文本")
            self.results_table.setItem(i, 2, text_item)
        
        # 调整行高
        for i in range(self.results_table.rowCount()):
            self.results_table.setRowHeight(i, 160)
        
        # 标记推荐的行
        recommended_index = debug_info.get("best_match", 0)
        if 0 <= recommended_index < self.results_table.rowCount():
            from PyQt5.QtGui import QColor, QBrush
            for col in range(self.results_table.columnCount()):
                item = self.results_table.item(recommended_index, col)
                if item:
                    item.setBackground(QBrush(QColor(200, 255, 200)))  # 淡绿色背景

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PDFSelectorApp()
    window.show()
    sys.exit(app.exec_()) 