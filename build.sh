#!/bin/bash

# 设置镜像名称和标签
IMAGE_NAME="plex-stun"
TAG="latest"

# 构建Docker镜像
echo "开始构建Docker镜像..."
docker build -t ${IMAGE_NAME}:${TAG} .

# 检查构建结果
if [ $? -eq 0 ]; then
    echo "Docker镜像构建成功: ${IMAGE_NAME}:${TAG}"
else
    echo "Docker镜像构建失败"
    exit 1
fi
