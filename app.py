import os
import sys
import json
import requests
from plexapi.server import PlexServer
from flask import Flask, jsonify, request

app = Flask(__name__)

PLEX_USERNAME = os.environ.get('PLEX_USERNAME', '')
PLEX_PASSWORD = os.environ.get('PLEX_PASSWORD', '')
PLEX_SERVER_BASEURL = os.environ.get('PLEX_URL','')


# Plex API URL
LOGIN_URL = "https://plex.tv/users/sign_in.json"

# 登录请求的头信息
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "X-Plex-Client-Identifier": "MyPlexApp"
}

# 获取新令牌的登录请求数据
data = {
    "user": {
        "login": PLEX_USERNAME,
        "password": PLEX_PASSWORD
    }
}

def check_environment():
    """
    检查必要的环境变量是否设置
    """
    required_vars = {
        'PLEX_USERNAME': os.environ.get('PLEX_USERNAME', ''),
        'PLEX_PASSWORD': os.environ.get('PLEX_PASSWORD', ''),
        'PLEX_URL': os.environ.get('PLEX_URL', '')
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        return False, f"缺少必要的环境变量: {', '.join(missing_vars)}"
    return True, None

def get_plex_token():
    """
    通过向 Plex API 发送登录请求获取 Plex 认证令牌。
    """
    try:
        response = requests.post(LOGIN_URL, headers=HEADERS, data=json.dumps(data))
        if response.status_code == 201:  # 状态码 201 表示登录成功
            return response.json()['user']['authentication_token']
        else:
            print(f"获取令牌失败。状态码: {response.status_code}")
            return None
    except Exception as e:
        print(f"认证过程中发生错误: {str(e)}")
        return None

def read_token_from_file(token_file):
    """
    从指定的 JSON 文件中读取 Plex 令牌。
    """
    if os.path.exists(token_file):
        try:
            with open(token_file, 'r') as file:
                data = json.load(file)
                return data.get('token')
        except Exception as e:
            print(f"读取令牌文件时发生错误: {str(e)}")
            return None
    else:
        return None

def save_token_to_file(token_file, token):
    """
    将 Plex 令牌保存到指定的 JSON 文件中。
    """
    try:
        with open(token_file, 'w') as file:
            json.dump({"token": token}, file)
    except Exception as e:
        print(f"保存令牌到文件时发生错误: {str(e)}")

def check_token_validity(baseurl, token):
    """
    通过向服务器发送验证请求来检查 Plex 令牌的有效性。
    """
    try:
        check_url = f"{baseurl}/library/sections?X-Plex-Token={token}"
        response = requests.get(check_url)
        return response.status_code == 200
    except Exception as e:
        print(f"检查令牌有效性时发生错误: {str(e)}")
        return False

def modify_port(plex, new_port):
    """
    修改 Plex 服务器设置中的手动端口映射。
    """
    manual_port_setting = plex.settings.get('manualPortMappingPort')
    
    if manual_port_setting:
        try:
            manual_port_setting.set(new_port)
            plex.settings.save()
            print(f"手动端口映射已成功更改为: {new_port}")
        except Exception as e:
            print(f"修改端口或保存设置时发生错误: {str(e)}")
    else:
        print("无法找到手动端口映射设置。")

@app.route('/change-port/<int:new_port>', methods=['GET'])
def change_port(new_port):
    """
    处理端口修改请求的Flask路由
    """
    # 检查环境变量
    env_check, error_msg = check_environment()
    if not env_check:
        return jsonify({
            "success": False,
            "message": error_msg
        }), 500

    # 定义令牌存储文件
    TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token/plex_token.json")

    # 从文件中读取令牌或生成新令牌
    PLEX_TOKEN = read_token_from_file(TOKEN_FILE)

    # 如果文件中没有令牌，或者令牌无效，则生成新令牌
    if PLEX_TOKEN is None or not check_token_validity(PLEX_SERVER_BASEURL, PLEX_TOKEN):
        PLEX_TOKEN = get_plex_token()
        if PLEX_TOKEN:
            save_token_to_file(TOKEN_FILE, PLEX_TOKEN)
        else:
            return jsonify({
                "success": False,
                "message": "获取有效令牌失败"
            }), 500

    # 使用 plexapi 连接到 Plex 服务器并修改手动端口
    try:
        plex = PlexServer(PLEX_SERVER_BASEURL, PLEX_TOKEN)
        modify_port(plex, new_port)
        return jsonify({
            "success": True,
            "message": f"端口已成功修改为 {new_port}"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"修改端口时发生错误: {str(e)}"
        }), 500

@app.route('/change-custom-url/<path:custom_url>', methods=['GET'])
def change_custom_url(custom_url):
    """
    处理自定义URL修改请求的Flask路由
    """
    # 检查环境变量
    env_check, error_msg = check_environment()
    if not env_check:
        return jsonify({
            "success": False,
            "message": error_msg
        }), 500

    # 验证URL格式
    if not custom_url.startswith(('http://', 'https://')):
        custom_url = f"http://{custom_url}"

    # 定义令牌存储文件
    TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token/plex_token.json")

    # 从文件中读取令牌或生成新令牌
    PLEX_TOKEN = read_token_from_file(TOKEN_FILE)

    # 如果文件中没有令牌，或者令牌无效，则生成新令牌
    if PLEX_TOKEN is None or not check_token_validity(PLEX_SERVER_BASEURL, PLEX_TOKEN):
        PLEX_TOKEN = get_plex_token()
        if PLEX_TOKEN:
            save_token_to_file(TOKEN_FILE, PLEX_TOKEN)
        else:
            return jsonify({
                "success": False,
                "message": "获取有效令牌失败"
            }), 500

    # 使用 plexapi 连接到 Plex 服务器并修改自定义URL
    try:
        plex = PlexServer(PLEX_SERVER_BASEURL, PLEX_TOKEN)
        # 获取当前的自定义连接列表
        current_urls = plex.settings.get('customConnections').value.split(',') if plex.settings.get('customConnections').value else []
        
        # 解析新的URL
        from urllib.parse import urlparse
        new_url_parsed = urlparse(custom_url)
        new_host = new_url_parsed.hostname
        new_port = new_url_parsed.port or (443 if new_url_parsed.scheme == 'https' else 80)
        
        # 检查是否存在相同IP的URL
        updated = False
        for i, url in enumerate(current_urls):
            parsed = urlparse(url)
            if parsed.hostname == new_host:
                # 如果找到相同IP的URL,只更新端口
                current_urls[i] = f"{parsed.scheme}://{parsed.hostname}:{new_port}"
                updated = True
                break
                
        # 如果没有找到相同IP的URL,添加新URL
        if not updated:
            current_urls.append(custom_url)
        
        # 更新设置
        plex.settings.get('customConnections').set(','.join(current_urls))
        plex.settings.save()
        
        return jsonify({
            "success": True,
            "message": f"自定义URL已{'更新端口' if updated else '添加'}: {custom_url}",
            "current_urls": current_urls
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"修改自定义URL时发生错误: {str(e)}"
        }), 500

@app.route('/')
def index():
    """
    显示服务状态和使用说明的根路由
    """
    # 检查环境变量
    env_check, error_msg = check_environment()
    
    # 获取当前主机的IP地址和端口
    host = request.host.split(':')[0]
    port = 4201

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Plex端口修改服务</title>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 20px auto;
                padding: 0 20px;
                line-height: 1.6;
            }}
            .status {{
                color: #2ecc71;
                font-weight: bold;
            }}
            .error {{
                color: #e74c3c;
                font-weight: bold;
            }}
            .endpoint {{
                background-color: #f8f9fa;
                padding: 10px;
                border-radius: 4px;
                font-family: monospace;
            }}
        </style>
    </head>
    <body>
        <h1>Plex-STUN端口修改服务</h1>
    """

    if env_check:
        html += """
        <p class="status">✅ 服务当前已经正常运行</p>
        <h2>接口信息：</h2>
        <p>要修改Plex端口，请将以下参数复制到Lucky中的Webhook中：</p>
        """
    else:
        html += f"""
        <p class="error">❌ 服务启动失败</p>
        <p class="error">错误信息：{error_msg}</p>
        <p>请确保在启动容器时设置以下环境变量：</p>
        <div class="endpoint">
            PLEX_USERNAME=你的Plex账号<br>
            PLEX_PASSWORD=你的Plex密码<br>
            PLEX_URL=你的Plex服务器地址
        </div>
        <p>例如使用docker-compose.yml：</p>
        <div class="endpoint">
            <pre>version: '3'
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
        restart: unless-stopped</pre>
        </div>
        <p>或者使用Docker命令行：</p>
        <div class="endpoint">
            <pre>docker run -d \\
    --name plex-stun \\
    -p 4201:4201 \\
    -v ./token:/app/token \\
    -e PLEX_USERNAME=your_username \\
    -e PLEX_PASSWORD=your_password \\
    -e PLEX_URL=http://your_plex_server:32400 \\
    --restart unless-stopped \\
    plex-stun:latest</pre>
        </div>
        """
    
    if env_check:
        html += f"""
        <p>端口修改接口：</p>
        <div class="endpoint">
            http://{host}:{port}/change-port/#{{port}}
        </div>
        <p>自定义URL修改接口：</p>
        <div class="endpoint">
            http://{host}:{port}/change-custom-url/ip:port
        </div>
        <p>示例：</p>
        <div class="endpoint">
            http://{host}:{port}/change-custom-url/192.168.1.100:32400
        </div>
        <p>请求方法：</p>
        <div class="endpoint">
            GET
        </div>
        <p>接口调用成功包含的字符串：</p>
        <div class="endpoint">
            "success":true
        </div>
        """

    html += """
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=4201)