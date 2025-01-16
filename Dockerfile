# 使用Python 3.9作为基础镜像
FROM python:3.9-alpine

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r requirements.txt

# 复制应用程序文件
COPY app.py .

# 创建token目录
RUN mkdir -p token

# 暴露端口
EXPOSE 4201

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 运行应用
CMD ["python", "app.py"] 