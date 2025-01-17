# Plex-STUN 端口修改服务

这是一个用于自动修改Plex服务器STUN端口的Web服务。当STUN端口发生变化时，可以通过Webhook自动更新Plex服务器的手动端口映射。

## 功能特点

- 提供Web API接口用于修改Plex端口
- 支持Docker部署
- 支持与Lucky工具集成

代码来源：
代码从 [NodeSeek 论坛](https://www.nodeseek.com/post-184057-1) 的脚本而来，增加了自定义URL更改的选项，并可部署为Docker服务。


## 快速开始

### 使用Docker Compose部署

1. 创建`docker-compose.yml`文件：

```yaml
version: '3'
services:
  plex-stun:
    build: .
    container_name: plex-stun
    ports:
      - "4201:4201"
    volumes:
      - ./token:/app/token
    environment:
      - PLEX_USERNAME=your_username
      - PLEX_PASSWORD=your_password
      - PLEX_URL=http://your_plex_server:32400
    restart: unless-stopped
```

2. 启动服务：
```bash
docker-compose up -d
```

### 使用Docker命令行部署

```bash
docker run -d \
    --name plex-stun \
    -p 4201:4201 \
    -v ./token:/app/token \
    -e PLEX_USERNAME=your_username \
    -e PLEX_PASSWORD=your_password \
    -e PLEX_URL=http://your_plex_server:32400 \
    --restart unless-stopped \
    plex-stun:latest
```

## 环境变量配置

| 变量名 | 说明 | 示例 |
|--------|------|------|
| PLEX_USERNAME | Plex账号邮箱 | user@example.com |
| PLEX_PASSWORD | Plex账号密码 | your_password |
| PLEX_URL | Plex服务器地址 | http://192.168.1.100:32400 |

## Lucky配置说明

### Webhook设置

1. 防火墙自动放行：开启
2. Webhook：启用

### 接口信息

- 接口地址：

修改Plex自带的远程访问，手动指定端口选项
```
http://<your-ip>:4201/change-port/#{port}
```

修改自定义URL
```
http://<your-ip>:4201/change-custom-url/#{ipAddr}
```

- 请求方法：
```
GET
```

- 接口调用成功判断依据：
```
"success":true
```

### 部署验证

部署成功后,可以通过访问 `http://<ip>:4201/` 查看服务状态和使用说明。

如果看到"✅ 服务当前已经正常运行"的提示,则表示服务已经成功部署并正常运行。
