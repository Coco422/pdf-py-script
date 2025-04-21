#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fitz
import os
import datetime

def create_timestamp_folder():
    """
    创建以时间戳命名的文件夹
    
    Returns:
        str: 创建的文件夹路径
    """
    # 创建以当前时间命名的文件夹
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"pdf_extract_{timestamp}"
    
    # 确保文件夹存在
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    return folder_name

def extract_text_from_region(pdf_path, page_num, rect):
    """
    从PDF文件指定页面的特定区域提取文本
    
    Args:
        pdf_path (str): PDF文件路径
        page_num (int): 页码（从0开始）
        rect (fitz.Rect): 矩形区域
        
    Returns:
        tuple: (提取的文本内容, 保存图像的路径, 输出文件夹)
    """
    if not os.path.exists(pdf_path):
        print(f"文件不存在: {pdf_path}")
        return None, None, None
        
    if rect is None:
        print("未指定区域")
        return None, None, None
    
    try:
        # 创建时间戳文件夹
        output_folder = create_timestamp_folder()
        
        doc = fitz.open(pdf_path)
        if page_num < 0 or page_num >= len(doc):
            print(f"页面范围错误: {page_num}, 总页数: {len(doc)}")
            doc.close()
            return None, None, None
        
        page = doc.load_page(page_num)
        page_width = page.rect.width
        page_height = page.rect.height
        
        # 检测PDF方向
        is_landscape = page_width > page_height
        orientation = "横向" if is_landscape else "纵向"
        print(f"检测到PDF方向: {orientation} (宽={page_width}, 高={page_height})")
        
        # 记录原始UI矩形
        orig_rect = fitz.Rect(rect)
        
        # 转换为整数矩形用于图像裁剪（使用原始坐标，图像提取是正确的）
        img_irect = fitz.IRect(rect)
        
        # 提取图像 - 使用原始坐标
        mat = fitz.Matrix(1, 1)  # 缩放比例，可根据需要调整
        pix = page.get_pixmap(matrix=mat, clip=img_irect)
        
        # 保存图像
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        image_filename = f"{pdf_name}_page_{page_num + 1}_area.png"
        image_path = os.path.join(output_folder, image_filename)
        pix.save(image_path)
        print(f"区域图像已保存: {image_path}")
        
        # 创建各种坐标变换选项
        transforms = []
        
        # 1. 原始坐标
        transforms.append({
            "name": "原始坐标",
            "rect": fitz.Rect(rect),
            "description": "直接使用UI选择的坐标（适用于大多数纵向PDF）"
        })
        
        # 2. 水平翻转
        transforms.append({
            "name": "水平翻转",
            "rect": fitz.Rect(
                page_width - rect.x1,
                rect.y0,
                page_width - rect.x0,
                rect.y1
            ),
            "description": "X轴从右到左（适用于某些布局）"
        })
        
        # 3. 90度顺时针旋转
        transforms.append({
            "name": "90度顺时针",
            "rect": fitz.Rect(
                rect.y0,
                page_width - rect.x1,
                rect.y1,
                page_width - rect.x0
            ),
            "description": "90度顺时针旋转(x,y) → (y, width-x)（适用于许多横向PDF）"
        })
        
        # 4. 90度逆时针旋转
        transforms.append({
            "name": "90度逆时针",
            "rect": fitz.Rect(
                page_height - rect.y1,
                rect.x0,
                page_height - rect.y0,
                rect.x1
            ),
            "description": "90度逆时针旋转(x,y) → (height-y, x)"
        })
        
        # 创建索引文件内容
        index_content = "# PDF区域提取结果\n\n"
        index_content += f"- **文件名**: {pdf_path}\n"
        index_content += f"- **页码**: {page_num + 1}\n"
        index_content += f"- **PDF方向**: {orientation}\n"
        index_content += f"- **页面尺寸**: 宽={page_width}, 高={page_height}\n"
        index_content += f"- **选择区域**: x0={rect.x0}, y0={rect.y0}, x1={rect.x1}, y1={rect.y1}\n\n"
        index_content += "## 提取结果\n\n"
        index_content += "| 坐标转换 | 预览图 | 提取文本 | 适用场景 |\n"
        index_content += "|---------|--------|----------|----------|\n"
        
        # 尝试所有变换并记录结果
        transform_results = []
        transform_texts = []
        best_transform_index = 0
        max_text_length = 0
        
        for i, transform in enumerate(transforms):
            try:
                # 获取并规范化矩形
                text_rect = transform["rect"]
                if text_rect.x0 > text_rect.x1:
                    text_rect.x0, text_rect.x1 = text_rect.x1, text_rect.x0
                if text_rect.y0 > text_rect.y1:
                    text_rect.y0, text_rect.y1 = text_rect.y1, text_rect.y0
                
                # 确保在页面范围内
                text_rect = text_rect.intersect(page.rect)
                
                # 提取文本
                try:
                    text_dict = page.get_text("dict", clip=text_rect)
                    extracted_text = ""
                    for block in text_dict["blocks"]:
                        if block["type"] == 0:  # 文本块
                            for line in block["lines"]:
                                line_text = ""
                                for span in line["spans"]:
                                    line_text += span["text"]
                                extracted_text += line_text + "\n"
                    
                    # 去除尾部多余的换行符
                    extracted_text = extracted_text.rstrip()
                    transform_texts.append(extracted_text)
                    
                    # 保存文本
                    text_filename = f"{pdf_name}_page_{page_num + 1}_{transform['name']}.txt"
                    text_path = os.path.join(output_folder, text_filename)
                    with open(text_path, 'w', encoding='utf-8') as f:
                        f.write(extracted_text)
                    
                    # 同时提取该区域的图像
                    preview_pix = page.get_pixmap(matrix=mat, clip=fitz.IRect(text_rect))
                    preview_path = os.path.join(output_folder, f"{pdf_name}_page_{page_num + 1}_{transform['name']}.png")
                    preview_pix.save(preview_path)
                    
                    # 记录结果
                    transform_results.append({
                        "name": transform["name"],
                        "description": transform["description"],
                        "rect": {
                            "x0": float(text_rect.x0),
                            "y0": float(text_rect.y0),
                            "x1": float(text_rect.x1),
                            "y1": float(text_rect.y1)
                        },
                        "text": extracted_text,
                        "text_length": len(extracted_text),
                        "has_text": len(extracted_text) > 0,
                        "image_path": preview_path,
                        "text_path": text_path
                    })
                    
                    # 更新索引内容
                    index_content += f"| {transform['name']} | [预览图]({os.path.basename(preview_path)}) | [文本]({os.path.basename(text_path)}) | {transform['description']} |\n"
                    
                    # 检查是否是最长文本（可能是最好的转换）
                    if len(extracted_text) > max_text_length:
                        max_text_length = len(extracted_text)
                        best_transform_index = i
                        
                except Exception as e:
                    print(f"提取文本失败 ({transform['name']}): {e}")
                    transform_results.append({
                        "name": transform["name"],
                        "description": transform["description"],
                        "rect": {
                            "x0": float(text_rect.x0),
                            "y0": float(text_rect.y0),
                            "x1": float(text_rect.x1),
                            "y1": float(text_rect.y1)
                        },
                        "error": str(e)
                    })
                    index_content += f"| {transform['name']} | [预览图]({os.path.basename(preview_path)}) | 提取失败 | {transform['description']} |\n"
                    
            except Exception as e:
                print(f"处理变换失败 ({transform['name']}): {e}")
        
        # 添加建议的最佳转换
        if transform_results:
            best_transform = transform_results[best_transform_index]
            recommended = "90度顺时针" if is_landscape else "原始坐标"
            
            index_content += "\n## 推荐使用\n\n"
            index_content += f"基于PDF方向（{orientation}）和文本长度，推荐使用 **{recommended}** 坐标转换。\n\n"
            index_content += f"实际提取最多文本的是: **{best_transform['name']}** (包含 {best_transform['text_length']} 个字符)\n"
        
        # 保存索引文件
        index_path = os.path.join(output_folder, "index.md")
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        # 保存调试信息JSON
        debug_filename = f"{pdf_name}_page_{page_num + 1}_transforms.json"
        debug_path = os.path.join(output_folder, debug_filename)
        import json
        debug_info = {
            "pdf_info": {
                "path": pdf_path,
                "page": page_num,
                "width": page_width,
                "height": page_height,
                "orientation": orientation,
                "is_landscape": is_landscape
            },
            "original_rect": {
                "x0": float(orig_rect.x0),
                "y0": float(orig_rect.y0),
                "x1": float(orig_rect.x1),
                "y1": float(orig_rect.y1)
            },
            "image_rect": {
                "x0": img_irect.x0,
                "y0": img_irect.y0,
                "x1": img_irect.x1,
                "y1": img_irect.y1
            },
            "transforms": transform_results,
            "recommended": recommended,
            "best_match": best_transform_index
        }
        with open(debug_path, 'w', encoding='utf-8') as f:
            json.dump(debug_info, f, ensure_ascii=False, indent=2)
        
        print(f"提取结果已保存到: {output_folder}")
        print(f"图像文件: {image_path}")
        print(f"结果索引: {index_path}")
        
        doc.close()
        
        # 返回最佳转换的文本（或第一个转换的文本，如果没有找到最佳转换）
        best_text = transform_texts[best_transform_index] if transform_texts else ""
        return best_text, image_path, output_folder
        
    except Exception as e:
        print(f"提取文本时出错: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

def extract_text_with_formatting(pdf_path, page_num, rect):
    """
    从PDF文件指定页面的特定区域提取文本并保留格式
    （此功能可以根据需求进一步扩展）
    
    Args:
        pdf_path (str): PDF文件路径
        page_num (int): 页码（从0开始）
        rect (fitz.Rect): 矩形区域
        
    Returns:
        tuple: (包含文本内容及格式信息的字典, 输出文件夹路径)
    """
    try:
        # 创建时间戳文件夹
        output_folder = create_timestamp_folder()
        
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_num)
        
        # 转换坐标系 - 使用90度顺时针旋转
        page_width = page.rect.width
        text_rect = fitz.Rect(
            rect.y0,                # 原x变为y
            page_width - rect.x1,   # 原width-x变为y
            rect.y1,                # 原x变为y
            page_width - rect.x0    # 原width-x变为y
        )
        
        # 确保矩形有效
        if text_rect.x0 > text_rect.x1:
            text_rect.x0, text_rect.x1 = text_rect.x1, text_rect.x0
        if text_rect.y0 > text_rect.y1:
            text_rect.y0, text_rect.y1 = text_rect.y1, text_rect.y0
            
        # 确保矩形有效且在页面范围内
        text_rect = text_rect.intersect(page.rect)
        
        # 获取区域内的文本块
        blocks = page.get_text("dict", clip=text_rect)["blocks"]
        
        result = {
            "text": "",
            "blocks": []
        }
        
        for block in blocks:
            if block["type"] == 0:  # 文本块
                block_text = ""
                lines = []
                
                for line in block["lines"]:
                    line_text = ""
                    spans = []
                    
                    for span in line["spans"]:
                        line_text += span["text"]
                        spans.append({
                            "text": span["text"],
                            "font": span["font"],
                            "size": span["size"],
                            "color": span["color"]
                        })
                    
                    lines.append({
                        "text": line_text,
                        "spans": spans
                    })
                    block_text += line_text + "\n"
                
                result["blocks"].append({
                    "text": block_text,
                    "lines": lines
                })
                result["text"] += block_text
        
        # 保存格式化文本
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        formatted_filename = f"{pdf_name}_page_{page_num + 1}_formatted.json"
        formatted_path = os.path.join(output_folder, formatted_filename)
        
        import json
        with open(formatted_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"格式化文本已保存: {formatted_path}")
        
        doc.close()
        return result, output_folder
    except Exception as e:
        print(f"提取格式化文本时出错: {e}")
        return None, None

def get_page_count(pdf_path):
    """
    获取PDF文件的页数
    
    Args:
        pdf_path (str): PDF文件路径
        
    Returns:
        int: 页数
    """
    try:
        doc = fitz.open(pdf_path)
        count = len(doc)
        doc.close()
        return count
    except Exception as e:
        print(f"获取页数时出错: {e}")
        return 0 