# PDF Region Selector and Text Extractor

一个使用 PyMuPDF 和 Qt 开发的 PDF 区域选择和文本提取工具。该工具允许用户可视化地选择 PDF 文档中的区域，并从选定区域提取文本内容。

## 功能特点

- 使用图形界面打开和浏览 PDF 文件
- 通过鼠标绘制矩形区域选择 PDF 内容
- 提取选定区域中的文本内容
- 支持将选定区域保存为图像
- 支持缩放和页面导航功能
- 简单易用的用户界面

## 技术栈

- **PyMuPDF (fitz)**: 用于 PDF 文件处理和文本提取
- **PyQt5/PySide2**: 提供图形用户界面
- **Python 3.6+**: 基本编程语言

## 安装

1. 克隆此仓库：

```bash
git clone https://github.com/coco422/pdf-region-selector.git
cd pdf-region-selector
```

2. 创建虚拟环境（可选但推荐）：

```bash
python -m venv venv
source venv/bin/activate  # Unix/macOS
# 或者
venv\Scripts\activate  # Windows
```

3. 安装依赖项：

```bash
pip install -r requirements.txt
```

## 使用方法

1. 运行主程序：

```bash
python pdf_selector_app.py
```

2. 使用"打开"按钮加载 PDF 文件
3. 使用鼠标在 PDF 上拖动以选择区域
4. 点击"提取文本"按钮从选定区域获取文本
5. 可选操作：保存选定区域为图像

## 快捷键

- `Ctrl+O`: 打开 PDF 文件
- `Ctrl+S`: 保存提取的文本
- `Ctrl+Q`: 退出应用程序
- `+/-`: 放大/缩小 PDF 视图
- `←/→`: 上一页/下一页

## 项目结构

```
pdf-region-selector/
├── pdf_selector_app.py     # 主应用程序入口
├── pdf_viewer.py           # PDF 查看器组件
├── region_selector.py      # 区域选择实现
├── text_extractor.py       # 文本提取功能
├── requirements.txt        # 项目依赖项
└── README.md               # 项目说明文档
```

## 示例代码

以下是使用 PyMuPDF 提取 PDF 指定区域内容的核心函数：

```python
def get_pdf_specific_area_content(pdf_path, page_num, rect):
    """
    获取 PDF 指定页面特定区域的内容并保存为图片
    :param pdf_path: PDF 文件的路径
    :param page_num: 页面编号，从 0 开始
    :param rect: 矩形区域，格式为 (x0, y0, x1, y1)
    :return: 特定区域内的文本内容
    """
    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_num)
        text = page.get_textbox(rect)
        
        # 渲染特定区域为图片
        mat = fitz.Matrix(1, 1)  # 缩放比例，可根据需要调整
        pix = page.get_pixmap(matrix=mat, clip=rect)
        image_path = f"page_{page_num + 1}_area.png"
        pix.save(image_path)
        
        doc.close()
        return text
    except Exception as e:
        print(f"读取 PDF 文件时出错: {e}")
        return None
```

## 依赖项

项目依赖以下主要库：

- PyMuPDF (fitz) >= 1.18.0
- PyQt5 >= 5.15.0 

完整依赖列表请参见 `requirements.txt` 文件。

## 贡献指南

欢迎对本项目做出贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/your-feature`)
3. 提交更改 (`git commit -m 'Add some feature'`)
4. 推送到分支 (`git push origin feature/your-feature`)
5. 创建 Pull Request

## 许可证

本项目基于 MIT 许可证发布 - 详情请参阅 [LICENSE](LICENSE) 文件。

## 联系方式

如有问题或建议，请通过 [GitHub Issues](https://github.com/yourusername/pdf-region-selector/issues) 联系我们。 