# STM32 OTA 固件更新服务器

一个专为 STM32F103ZET6 微控制器设计的 OTA (Over-The-Air) 固件更新服务器，支持固件上传、管理和远程更新。

## 功能特性

- 🚀 **固件上传**: 支持 `.bin` 和 `.hex` 格式固件文件上传
- 📋 **版本管理**: 支持多版本固件管理，自动生成 MD5 校验值
- 🌐 **Web 界面**: 直观的固件上传和管理界面
- 🔧 **RESTful API**: 完整的 API 接口，供 STM32 设备调用
- 📊 **统计信息**: 下载次数统计和存储使用情况
- 🛡️ **安全检查**: 文件类型验证和大小限制
- 📱 **响应式设计**: 支持移动设备访问

## 系统要求

- Python 3.7+
- Flask 3.0.0
- Werkzeug 3.0.1

## 快速开始

### 自动启动（推荐）

```bash
chmod +x start_server.sh
./start_server.sh
```

启动脚本会自动：

- 检查 Python 环境
- 创建虚拟环境
- 安装依赖包
- 创建必要目录
- 启动服务器

### 手动启动

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 创建上传目录
mkdir -p uploads

# 启动服务器
python server.py
```

## 访问地址

服务器启动后，可通过以下地址访问：

- **Web 界面**: http://localhost:3685
- **管理界面**: http://localhost:3685/manage
- **API 测试**: http://localhost:3685/api/test

## API 接口文档

### 基础信息

- **基础 URL**: `http://localhost:3685/api`
- **端口**: 3685
- **支持格式**: JSON

### 接口列表

#### 1. 测试连接

```http
GET /api/test
```

**响应示例**:

```json
{
  "status": "success",
  "message": "STM32 OTA Server is running",
  "timestamp": "2025-08-22T15:16:34.262516",
  "server_info": {
    "max_file_size": "2MB",
    "supported_formats": ["bin", "hex"],
    "api_version": "1.0"
  }
}
```

#### 2. 获取固件列表

```http
GET /api/firmware/list
```

**响应示例**:

```json
{
  "status": "success",
  "count": 2,
  "firmware": [
    {
      "version": "3.0.0",
      "size": 368,
      "md5": "b52a83563f26434951e584a2c9b6df12",
      "description": "",
      "upload_time": "2025-08-22T15:16:34.262516"
    }
  ]
}
```

#### 3. 获取最新固件信息

```http
GET /api/firmware/latest
```

#### 4. 获取指定版本固件信息

```http
GET /api/firmware/info/{version}
```

#### 5. 下载固件文件

```http
GET /api/firmware/download/{version}
GET /api/firmware/download/latest
```

**特殊参数**:

- `latest`: 自动下载最新版本固件

## 项目结构

```
ota_server/
├── server.py              # 主服务器文件
├── requirements.txt       # Python 依赖
├── start_server.sh       # 一键启动脚本
├── firmware_info.json    # 固件信息数据库
├── templates/            # HTML 模板
│   ├── index.html       # 主页（上传界面）
│   └── manage.html      # 管理界面
├── static/              # 静态资源
│   └── style.css       # 样式文件
├── uploads/             # 固件文件存储目录
├── firmware/            # 示例固件目录
└── venv/               # Python 虚拟环境
```

## 配置说明

### 服务器配置

- **端口**: 3685
- **最大文件大小**: 2MB
- **支持文件格式**: `.bin`, `.hex`
- **存储目录**: `uploads/`

### 安全设置

- 文件类型严格验证
- 文件大小限制
- 安全文件名处理
- MD5 校验值验证

## STM32 集成示例

### C 代码示例（HTTP 请求）

```c
// 获取最新固件信息
void check_firmware_update() {
    char url[] = "http://192.168.1.100:3685/api/firmware/latest";

    // 发送 HTTP GET 请求
    if (http_get(url, response_buffer) == HTTP_OK) {
        // 解析 JSON 响应
        parse_firmware_info(response_buffer);
    }
}

// 下载固件文件
void download_firmware(const char* version) {
    char url[256];
    snprintf(url, sizeof(url),
             "http://192.168.1.100:3685/api/firmware/download/%s",
             version);

    // 下载固件到缓冲区
    if (http_download(url, firmware_buffer) == HTTP_OK) {
        // 验证 MD5
        if (verify_md5(firmware_buffer, expected_md5)) {
            // 写入 Flash
            write_firmware_to_flash(firmware_buffer);
        }
    }
}
```

## 开发说明

### 添加新功能

1. **修改服务器逻辑**: 编辑 `server.py`
2. **更新界面**: 修改 `templates/` 下的 HTML 文件
3. **调整样式**: 编辑 `static/style.css`

### 数据存储

固件信息存储在 `firmware_info.json` 中，包含：

- 版本号
- 文件信息（名称、大小、MD5）
- 上传时间
- 下载统计
- 版本描述

### 错误处理

服务器包含完整的错误处理机制：

- 404: API 端点不存在
- 413: 文件过大
- 500: 服务器内部错误

## 常见问题

### Q: 如何修改服务器端口？

A: 编辑 `server.py` 文件第 326 行的端口号。

### Q: 如何增加最大文件大小？

A: 修改 `server.py` 第 20 行的 `MAX_CONTENT_LENGTH` 配置。

### Q: 如何备份固件数据？

A: 备份 `uploads/` 目录和 `firmware_info.json` 文件。

### Q: 支持哪些文件格式？

A: 目前支持 `.bin` 和 `.hex` 格式。可在 `server.py` 第 24 行添加新格式。

## 许可证

本项目使用 MIT 许可证。

## 作者

Generated with [canlumina](https://github.com/canlumina)

---

**注意**: 此服务器专为开发和测试环境设计。生产环境使用时请添加适当的身份验证和安全措施。
