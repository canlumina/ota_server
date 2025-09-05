# STM32 OTA Server v2.0

一个现代化的、前后端分离的STM32固件OTA (Over-The-Air) 升级管理系统。

## ✨ 核心特性

- 🚀 **固件管理**: 上传、存储、版本管理STM32固件文件，自动标记最新版本
- 🔒 **多重加密**: 支持XOR、AES-128-CBC、AES-256-CBC等加密算法，STM32兼容
- 🌐 **双界面设计**: 用户前端界面 + 管理员后台界面
- 📡 **RESTful API**: 完整的API接口，支持第三方集成和OTA升级
- 🎯 **跨域支持**: 自动检测访问地址，支持局域网和外网访问

## 🚀 快速开始

### 环境要求
- **Python**: 3.7+
- **操作系统**: Windows, Linux, macOS

### 安装使用

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **一键启动** ⭐ (推荐)

**Linux/Mac:**
```bash
# 启动所有服务
./start_server.sh

# 管理命令
./start_server.sh status    # 查看状态
./start_server.sh stop      # 停止服务
./start_server.sh restart   # 重启服务
./start_server.sh logs      # 查看日志
```

**Windows:**
```cmd
start_server.bat            # 启动服务
start_server.bat status     # 查看状态
start_server.bat stop       # 停止服务
```

**手动启动:**
```bash
# 后端服务 (端口 5000)
python server/app.py

# 前端服务 (端口 3000)
cd client/public && python -m http.server 3000
```

3. **访问应用**
- **前端用户界面**: http://localhost:3000 (固件管理、上传、加密)
- **后端管理界面**: http://localhost:5000 (系统监控、API文档)

## 📁 项目结构

```
ota_server/
├── server/                 # Flask后端服务
│   ├── app.py             # 主应用入口
│   ├── api/v1/           # RESTful API
│   ├── services/         # 业务逻辑层
│   ├── core/             # 核心功能模块
│   └── config/           # 配置文件
├── client/public/         # 前端用户界面 (静态文件)
├── templates/            # 后端管理界面
├── storage/              # 数据存储 (固件/日志/数据库)
├── start_server.sh       # 一键启动脚本
└── requirements.txt      # Python依赖
```

## 🎯 功能界面

### 前端用户界面 (端口 3000)
- 📤 **智能上传**: 支持版本号自动填充，上传时直接选择加密算法
- 🔐 **一体化加密**: 多种加密算法，支持密码派生和随机密钥生成
- 📋 **固件列表**: 最新版本标记，加密状态显示，支持下载和删除
- 📊 **系统监控**: 固件统计和存储使用情况

### 后端管理界面 (端口 5000)
- 📊 **系统仪表板**: 实时监控固件统计和系统资源
- 🔧 **API测试工具**: 内置API接口测试功能
- 📚 **API文档**: 完整的接口文档和示例
- 🔗 **智能链接**: 自动跳转到前端界面

## 🔒 安全特性

### 文件安全
- 文件类型验证 (.bin, .hex, .elf)
- 文件大小限制 (16MB)
- 路径遍历攻击防护

### 加密支持
- **NONE**: 无加密
- **XOR**: 轻量级异或加密
- **AES-128-CBC**: 工业级加密，STM32兼容 ⭐
- **AES-256-CBC**: 增强AES加密

### 网络安全
- CORS跨域支持
- 自动检测访问地址 (localhost/IP)
- API版本控制

## 📡 主要API

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/firmwares` | 获取固件列表 |
| POST | `/api/v1/firmwares` | 上传固件 |
| GET | `/api/v1/firmwares/latest` | 获取最新固件 |
| GET | `/api/v1/system/health` | 系统健康检查 |

更多API文档请访问后端管理界面。

## 🐛 故障排除

### 常见问题

**1. 脚本权限问题 (Linux/Mac)**
```bash
chmod +x start_server.sh quick_start.sh
```

**2. 端口被占用**
```bash
./start_server.sh status    # 检查服务状态
./start_server.sh stop      # 停止服务
```

**3. 查看日志**
```bash
./start_server.sh logs           # 所有日志
./start_server.sh logs backend   # 后端日志
tail -f storage/logs/app.log     # 应用日志
```

**4. 上传失败**
- 确保文件格式为 .bin/.hex/.elf
- 检查文件大小不超过16MB
- 填写完整版本号或使用默认值

**5. 跨域访问问题**
系统已自动支持跨域访问，通过IP访问虚拟机服务时会自动切换API地址。

## 🚗 升级亮点

### v2.0 重要改进
- ✅ **跨域访问修复**: 支持PC访问虚拟机服务
- ✅ **智能上传**: 版本号自动填充，避免"Failed to fetch"错误
- ✅ **动态地址**: 前后端链接根据访问方式自动切换
- ✅ **一键启动**: 完善的脚本管理系统
- ✅ **双界面优化**: 用户界面和管理界面功能分离

---

**⚠️ 重要提醒**: 加密算法已经过STM32端测试验证，请勿修改 `server/core/crypto.py` 中的实现。