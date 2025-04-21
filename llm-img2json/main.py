#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import base64
import logging
from typing import List, Optional
import json
from dotenv import load_dotenv
import uvicorn
import aiohttp
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 加载环境变量
load_dotenv()

# 初始化日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 从环境变量获取配置：API密钥、API URL、模型名称
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AI_API_URL = os.getenv("AI_API_URL", "https://api.openai.com/v1/chat/completions")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

if not OPENAI_API_KEY:
    logger.error("未找到OPENAI_API_KEY环境变量")
    raise ValueError("请设置OPENAI_API_KEY环境变量")

if not AI_API_URL:
    logger.warning("未设置AI_API_URL环境变量，将使用默认OpenAI API地址")

logger.info(f"使用模型: {MODEL_NAME}")
logger.info(f"API地址: {AI_API_URL}")

# 创建FastAPI应用
app = FastAPI(
    title="llm 图片分析API",
    description="上传图片和提示词，使用 vlm 模型进行分析",
    version="1.0.0",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ImageAnalysisRequest(BaseModel):
    prompt: str
    image_url: Optional[str] = None
    
class ImageAnalysisResponse(BaseModel):
    result: str
    
async def call_openai_api(image_data: bytes, prompt: str):
    """调用OpenAI API处理图片和提示词"""
    # OpenAI API端点
    url = AI_API_URL
    
    # 将图片转换为base64
    base64_image = base64.b64encode(image_data).decode("utf-8")
    
    # 构建请求头
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    # 构建请求体
    payload = {
        "model": MODEL_NAME, 
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 1000
    }
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"OpenAI API错误: {response.status} - {error_text}")
                        # 如果是最后一次重试，则抛出异常
                        if retry_count == max_retries - 1:
                            raise HTTPException(status_code=response.status, detail=f"OpenAI API错误: {error_text}")
                        retry_count += 1
                        continue
                    
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
            # 如果成功执行到这里，跳出循环
            break
        except aiohttp.ClientError as e:
            logger.error(f"调用OpenAI API时发生错误 (尝试 {retry_count+1}/{max_retries}): {str(e)}")
            # 如果是最后一次重试，则抛出异常
            if retry_count == max_retries - 1:
                raise HTTPException(status_code=500, detail=f"调用OpenAI API时发生错误: {str(e)}")
            retry_count += 1

@app.post("/analyze", response_model=ImageAnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    prompt: str = Form(...),
):
    """
    上传图片和提示词，默认使用GPT-4o-mini模型进行分析
    
    - **file**: 要分析的图片文件
    - **prompt**: 分析提示词
    """
    # 验证文件类型
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传有效的图片文件")
    
    try:
        # 读取图片数据
        image_data = await file.read()
        
        # 调用OpenAI API
        result = await call_openai_api(image_data, prompt)
        
        return {"result": result}
    except Exception as e:
        logger.error(f"处理请求时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理请求时发生错误: {str(e)}")

@app.post("/analyze/json", response_model=dict)
async def analyze_image_json(
    file: UploadFile = File(...),
    prompt: str = Form(...),
):
    """
    上传图片和提示词，默认使用GPT-4o-mini模型进行分析并返回JSON结果
    
    - **file**: 要分析的图片文件
    - **prompt**: 分析提示词，应当要求模型返回JSON格式
    """
    # 验证文件类型
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传有效的图片文件")
    
    try:
        # 读取图片数据
        image_data = await file.read()
        
        # 调用OpenAI API
        result_text = await call_openai_api(image_data, prompt + " 请以有效的JSON格式返回结果。")
        
        # 尝试解析JSON
        try:
            # 提取JSON部分（如果输出包含其他文本）
            json_text = result_text
            # 如果文本中包含```json和```，提取它们之间的内容
            if "```json" in result_text and "```" in result_text.split("```json", 1)[1]:
                json_text = result_text.split("```json", 1)[1].split("```", 1)[0].strip()
            # 如果没有json标记但有代码块
            elif "```" in result_text and "```" in result_text.split("```", 1)[1]:
                json_text = result_text.split("```", 1)[1].split("```", 1)[0].strip()
                
            result_json = json.loads(json_text)
            return result_json
        except json.JSONDecodeError:
            # 如果解析JSON失败，返回原始文本
            logger.warning(f"无法解析返回的JSON: {result_text}")
            return {"error": "无法解析返回的JSON", "raw_result": result_text}
    except Exception as e:
        logger.error(f"处理请求时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理请求时发生错误: {str(e)}")

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy"}

if __name__ == "__main__":
    # 创建目录结构
    os.makedirs("uploads", exist_ok=True)
    
    # 运行服务器
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=33880, 
        reload=True
    )
