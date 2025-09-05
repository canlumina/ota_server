# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

STM32 OTA Server 是一个前后端分离的固件管理和设备升级系统，支持多种加密算法和升级方式。

## 核心启动命令

### 推荐启动方式（生产级管理脚本）
```bash
# 一键启动所有服务（后台运行）
./start_server.sh start

# 管理服务
./start_server.sh status    # 查看服务状态
./start_server.sh stop      # 停止所有服务
./start_server.sh restart   # 重启服务
./start_server.sh logs      # 查看实时日志
./start_server.sh logs backend  # 只查看后端日志
```

### 开发环境手动启动
```bash
# 依赖安装
pip install -r requirements.txt

# 后端服务 (Flask API, 端口5000)
python server/app.py

# 前端服务 (静态文件服务, 端口3000) 
cd client/public && python -m http.server 3000
```

### 测试命令
```bash
# 运行测试（如果存在测试文件）
python -m pytest server/tests/

# API健康检查
curl http://localhost:5000/api/v1/system/health
```

## 架构概述

### 三层架构
1. **API层** (`server/api/v1/`): RESTful API端点
2. **服务层** (`server/services/`): 业务逻辑实现  
3. **核心层** (`server/core/`): 底层功能模块

### 关键组件
- **CryptoManager** (`server/core/crypto.py`): 加密算法实现，兼容STM32端
- **FirmwareManager** (`server/core/firmware_manager.py`): 固件文件管理
- **SerialManager** (`server/core/serial_manager.py`): 串口设备通信

### API结构
- 基础URL: `http://localhost:5000/api/v1`
- 主要端点:
  - `/firmwares` - 固件管理
  - `/devices` - 设备管理 
  - `/crypto` - 加密服务
  - `/system` - 系统状态

## 加密算法重要说明

**绝对不能修改加密算法实现**。`server/core/crypto.py`中的加密算法（特别是AES-128-CBC和STM32兼容的密钥派生算法）已经过测试，与STM32单片机端完全兼容。任何修改都可能导致兼容性问题。

### 支持的加密算法
- **NONE**: 无加密
- **XOR**: 简单XOR加密  
- **AES-128-CBC**: 工业级AES加密，STM32兼容
- **AES-256-CBC**: 增强AES加密

## 前端架构

### 当前实现
前端使用纯HTML/CSS/JavaScript实现，位于`client/public/`:
- `index.html` - 主页面，现代Bootstrap 5界面
- `firmware-manager.js` - 固件管理功能
- `styles/firmware-style.css` - 样式定义

### API调用模式
前端通过fetch API与后端通信，API_BASE = 'http://localhost:5000/api/v1'

## 存储结构

```
storage/
├── firmware/          # 固件文件存储
├── uploads/           # 临时上传文件  
├── logs/              # 应用日志
└── ota_server.db      # SQLite数据库

# 脚本管理的进程文件（自动生成）
logs/                   # 脚本生成的日志
├── backend.log        # 后端服务日志
└── frontend.log       # 前端服务日志

pids/                   # 进程ID文件（脚本管理）
├── backend.pid        # 后端进程PID
└── frontend.pid       # 前端进程PID

tools/                  # 维护工具
└── fix_firmware_storage.py  # 固件存储修复工具
```

## 配置管理

配置文件位于`server/config/settings.py`，支持多环境配置：
- `DevelopmentConfig` - 开发环境（默认）
- `TestingConfig` - 测试环境  
- `ProductionConfig` - 生产环境

通过环境变量`FLASK_ENV`控制使用的配置。

## 常见开发任务

### 添加新API端点
1. 在`server/api/v1/`创建新的蓝图模块
2. 在`server/services/`实现对应的服务类
3. 在`server/api/v1/__init__.py`中注册蓝图

### 修复前端问题
- 如果遇到API调用失败，检查`firmware-manager.js`中的API路径
- 固件ID使用格式：`fw_{timestamp}_{filename}`
- 前端选择框应使用`firmware.id`而不是`firmware.filename`

### 调试技巧
- 应用日志位置: `storage/logs/app.log`（应用内部日志）
- 服务日志位置: `logs/backend.log`, `logs/frontend.log`（脚本启动的服务日志）
- 开启调试模式: `export FLASK_ENV=development`
- 查看实时日志: 
  - `tail -f storage/logs/app.log`（应用日志）
  - `./start_server.sh logs`（所有服务日志）
  - `./start_server.sh logs backend`（仅后端日志）

### 进程管理
- 使用脚本启动的服务会自动进行进程管理，支持后台运行
- 进程PID存储在`pids/`目录下
- 可以通过`./start_server.sh status`检查服务状态
- 避免手动kill进程，使用`./start_server.sh stop`优雅停止服务

## 重要约束

1. **加密算法兼容性**: 不能修改`server/core/crypto.py`中的算法实现
2. **固件ID格式**: 必须使用`fw_{timestamp}_{filename}`格式
3. **前后端分离**: 前端为纯静态文件，后端为纯API服务
4. **存储路径**: 所有文件存储在`storage/`目录下，不要修改结构

## 故障排除

### 固件加密失败
- 检查固件ID是否正确（应使用API返回的完整ID）
- 确认加密算法选择正确
- 查看后端日志确认具体错误

### 前端无法访问
- 确保前端服务在端口3000启动
- 检查后端服务是否在端口5000运行
- 清除浏览器缓存重新加载

### API调用失败  
- 检查CORS配置是否正确
- 确认API端点路径正确（注意是`firmwares`不是`firmware`）
- 查看Network面板确认请求详情
- 检查服务状态: `./start_server.sh status`
- 测试API连通性: `curl http://localhost:5000/api/v1/system/health`

### 文件上传失败
- 确保上传的是`.bin`格式的固件文件
- 检查文件不为空
- 查看后端日志确认具体错误信息
- 检查storage目录权限

### 服务依赖
- Python 3.x (推荐Python 3.8+)
- Flask及相关依赖（见requirements.txt）
- curl命令（用于健康检查）
- lsof命令（用于端口检查）