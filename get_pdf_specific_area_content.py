# 安装 PyMuPDF 库的命令：
# pip install PyMuPDF
#
# PyMuPDF 提供了 fitz 模块，用于处理 PDF 文件
# 安装完成后，可以通过以下方式导入
import fitz

def get_pdf_specific_area_content(pdf_path, page_num, rect, irect):
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
        pix = page.get_pixmap(matrix=mat, clip=irect)
        image_path = f"page_{page_num + 1}_area.png"
        pix.save(image_path)
        print(f"特定区域已保存为图片: {image_path}")

        doc.close()
        return text
    except Exception as e:
        print(f"读取 PDF 文件时出错: {e}")
        return None

if __name__ == "__main__":
    pdf_path = 'docs/output.pdf'
    # 假设要获取第 0 页上的一个区域，这里的坐标需要根据实际情况调整
    page_num = 0
    # 矩形区域 (x0, y0, x1, y1)，表示左上角和右下角的坐标
    # rect = fitz.Rect(1140, 70, 1650, 1160)
    # rect = fitz.Rect(1105, 400, 1605, 405)
    irect = fitz.IRect(1105, 3, 1605, 405)
    rect = fitz.Rect(1105, 3, 1605, 405)
    # rect = fitz.Rect(100, 100, 100, 100)
    content = get_pdf_specific_area_content(pdf_path, page_num, rect, irect)
    if content:
        print("特定区域的内容如下：")
        print(content)
    