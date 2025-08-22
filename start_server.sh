#!/bin/bash

# STM32 OTA 服务器启动脚本

echo "=========================================="
echo "STM32 OTA 固件更新服务器"
echo "=========================================="

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3"
    echo "请先安装 Python3"
    exit 1
fi

# 检查是否在正确目录
if [ ! -f "server.py" ]; then
    echo "❌ 错误: 请在 ota_server 目录下运行此脚本"
    exit 1
fi

# 检查并安装依赖
echo "🔍 检查 Python 依赖..."
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ 虚拟环境创建失败"
        exit 1
    fi
fi

echo "🔧 激活虚拟环境..."
source venv/bin/activate

if [ -f "requirements.txt" ]; then
    echo "📦 安装依赖包..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败，请检查网络连接"
        exit 1
    fi
else
    echo "⚠️  未找到 requirements.txt，手动安装 Flask..."
    pip install Flask==3.0.0 Werkzeug==3.0.1
fi

# 创建必要的目录
echo "📁 创建上传目录..."
mkdir -p uploads

# 获取本机IP地址
echo "🌐 检测网络配置..."
if command -v ip &> /dev/null; then
    LOCAL_IP=$(ip route get 8.8.8.8 | head -1 | awk '{print $7}')
elif command -v ifconfig &> /dev/null; then
    LOCAL_IP=$(ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -1)
else
    LOCAL_IP="localhost"
fi

echo "=========================================="
echo "🚀 启动 OTA 服务器..."
echo "=========================================="
echo "本机IP地址: $LOCAL_IP"
echo "服务器端口: 3685"
echo ""
echo "访问地址:"
echo "  Web界面:  http://$LOCAL_IP:3685"
echo "  管理界面: http://$LOCAL_IP:3685/manage"
echo "  API测试:  http://$LOCAL_IP:3685/api/test"
echo ""
echo "STM32 API 地址: http://$LOCAL_IP:3685/api/"
echo "=========================================="
echo "按 Ctrl+C 停止服务器"
echo "=========================================="

# 启动服务器 (在虚拟环境中)
python server.py