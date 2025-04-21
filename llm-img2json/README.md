# GPT-4o-mini 图片分析API

这是一个使用FastAPI和aiohttp构建的API，用于调用OpenAI的GPT-4o-mini模型进行图片分析。

## 功能特点

- 上传图片和提示词，使用GPT-4o-mini模型进行分析
- 支持返回普通文本或JSON格式的结果
- 异步处理API请求，提高性能
- 完善的错误处理和日志记录

## 安装

1. 克隆仓库

```bash
git clone <repository-url>
cd llm-img2json
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 配置环境变量

将 `.env.example` 复制为 `.env` 并填入你的OpenAI API密钥：

```bash
cp .env.example .env
# 然后编辑 .env 文件，填入你的API密钥
```

## 使用方法

1. 启动服务器

```bash
python main.py
```

服务器将在 http://localhost:8000 上运行。

2. API端点

- **POST /analyze**：上传图片和提示词，返回分析文本结果
- **POST /analyze/json**：上传图片和提示词，返回JSON格式的分析结果
- **GET /health**：健康检查端点

3. 访问API文档

启动服务器后，访问 http://localhost:8000/docs 查看交互式API文档。

## API请求示例

### 使用curl发送请求

```bash
curl -X POST http://localhost:8000/analyze \
  -F "file=@/path/to/your/image.jpg" \
  -F "prompt=描述这张图片中的内容"
```

### 使用Python发送请求

```python
import requests

url = "http://localhost:8000/analyze"
files = {"file": ("image.jpg", open("/path/to/your/image.jpg", "rb"), "image/jpeg")}
data = {"prompt": "描述这张图片中的内容"}

response = requests.post(url, files=files, data=data)
print(response.json())
```

## 返回JSON格式结果

如果需要返回结构化的JSON数据，可以使用`/analyze/json`端点，并在提示词中明确要求返回JSON格式：

```bash
curl -X POST http://localhost:8000/analyze/json \
  -F "file=@/path/to/your/image.jpg" \
  -F "prompt=分析这张图片并以JSON格式返回以下信息：主要对象、颜色、场景描述"
```

## 部署

对于生产环境部署，建议使用Gunicorn作为ASGI服务器：

```bash
pip install gunicorn
gunicorn main:app -k uvicorn.workers.UvicornWorker -w 4 --bind 0.0.0.0:8000
```

## 许可证

[MIT License](LICENSE)