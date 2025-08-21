# STM32 OTA 固件更新服务器

基于Flask的独立Web服务器，为STM32固件提供上传、管理和OTA下载功能。

## 🚀 功能特性

- **Web界面上传**: 支持通过浏览器上传.bin/.hex固件文件
- **版本管理**: 自动管理固件版本、大小、MD5校验等信息
- **REST API**: 为STM32提供标准化的HTTP API接口
- **安全验证**: 文件大小限制、MD5校验、文件类型验证
- **统计信息**: 下载次数统计、存储使用情况
- **响应式界面**: 支持桌面和移动端浏览器

## 📋 环境要求

- Python 3.7+
- Flask 3.0+
- 网络连接 (局域网或互联网)

## 🛠️ 安装和运行

### 1. 安装依赖

```bash
# 克隆项目
git clone <repository_url>
cd ota_server

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装Python依赖
pip install -r requirements.txt
```

### 2. 启动服务器

```bash
# 运行服务器
python server.py
```

服务器将在 `http://localhost:3685` 启动。

### 3. 访问界面

- **主页 (固件上传)**: http://localhost:3685
- **管理界面**: http://localhost:3685/manage
- **API测试**: http://localhost:3685/api/test

## 🌐 Web界面使用

### 固件上传

1. 访问主页 http://localhost:3685
2. 填写版本号 (格式: 1.0.0)
3. 添加版本描述 (可选)
4. 选择.bin或.hex固件文件
5. 点击"🚀 上传固件"

### 固件管理

1. 访问管理页面 http://localhost:3685/manage
2. 查看所有已上传固件的详细信息
3. 下载、删除或查看固件详情
4. 测试API接口连通性

## 🔌 STM32 API 接口

### 基础接口

#### 1. 测试连接
```http
GET /api/test
```

**响应示例:**
```json
{
  "status": "success",
  "message": "STM32 OTA Server is running",
  "timestamp": "2025-01-20T10:30:00",
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

**响应示例:**
```json
{
  "status": "success",
  "count": 2,
  "firmware": [
    {
      "version": "1.1.0",
      "size": 45678,
      "md5": "a1b2c3d4e5f6...",
      "description": "修复WiFi连接问题",
      "upload_time": "2025-01-20T10:30:00"
    }
  ]
}
```

#### 3. 获取最新固件
```http
GET /api/firmware/latest
```

**响应示例:**
```json
{
  "status": "success",
  "version": "1.1.0",
  "size": 45678,
  "md5": "a1b2c3d4e5f6...",
  "description": "修复WiFi连接问题",
  "download_url": "/api/firmware/download/1.1.0"
}
```

#### 4. 获取指定版本信息
```http
GET /api/firmware/info/<version>
```

#### 5. 下载固件
```http
GET /api/firmware/download/<version>
```

## 🔧 STM32 集成示例

### ESP8266 HTTP请求示例

```c
// 1. 测试服务器连接
esp8266_status_t test_ota_server(const char* server_ip) {
    char cmd[128];
    snprintf(cmd, sizeof(cmd), 
             "AT+CIPSTART=0,\"TCP\",\"%s\",3685", server_ip);
    
    if (esp8266_send_command(cmd, "OK", 10000) != ESP8266_OK) {
        return ESP8266_ERROR;
    }
    
    // 发送HTTP GET请求
    const char* http_request = 
        "GET /api/test HTTP/1.1\r\n"
        "Host: %s:3685\r\n"
        "Connection: close\r\n\r\n";
    
    char request[256];
    snprintf(request, sizeof(request), http_request, server_ip);
    
    return esp8266_send_data(0, (uint8_t*)request, strlen(request));
}

// 2. 获取最新固件信息
esp8266_status_t get_latest_firmware_info(const char* server_ip) {
    // 建立连接
    char cmd[128];
    snprintf(cmd, sizeof(cmd), 
             "AT+CIPSTART=0,\"TCP\",\"%s\",3685", server_ip);
    
    if (esp8266_send_command(cmd, "OK", 10000) != ESP8266_OK) {
        return ESP8266_ERROR;
    }
    
    // 发送HTTP请求
    const char* http_request = 
        "GET /api/firmware/latest HTTP/1.1\r\n"
        "Host: %s:3685\r\n"
        "Connection: close\r\n\r\n";
    
    char request[256];
    snprintf(request, sizeof(request), http_request, server_ip);
    
    return esp8266_send_data(0, (uint8_t*)request, strlen(request));
}

// 3. 下载固件到外部Flash
esp8266_status_t download_firmware(const char* server_ip, const char* version) {
    // 建立连接
    char cmd[128];
    snprintf(cmd, sizeof(cmd), 
             "AT+CIPSTART=0,\"TCP\",\"%s\",3685", server_ip);
    
    if (esp8266_send_command(cmd, "OK", 10000) != ESP8266_OK) {
        return ESP8266_ERROR;
    }
    
    // 发送下载请求
    char request[512];
    snprintf(request, sizeof(request),
        "GET /api/firmware/download/%s HTTP/1.1\r\n"
        "Host: %s:3685\r\n"
        "Connection: close\r\n\r\n",
        version, server_ip);
    
    if (esp8266_send_data(0, (uint8_t*)request, strlen(request)) != ESP8266_OK) {
        return ESP8266_ERROR;
    }
    
    // 接收并存储固件数据到外部Flash
    // 实现数据接收和W25Q64写入逻辑
    
    return ESP8266_OK;
}
```

## 📁 目录结构

```
ota_server/
├── server.py              # 主服务器程序
├── requirements.txt       # Python依赖
├── README.md              # 使用说明
├── firmware_info.json     # 固件信息数据库 (自动生成)
├── templates/             # HTML模板
│   ├── index.html         # 上传界面
│   └── manage.html        # 管理界面
├── static/                # 静态资源
│   └── style.css          # 样式文件
└── uploads/               # 固件存储目录 (自动创建)
    └── firmware_v1.0.0_*.bin
```

## ⚙️ 配置选项

### 服务器配置

在 `server.py` 中可以修改以下配置:

```python
# 最大文件大小 (默认2MB)
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'bin', 'hex'}

# 服务器端口 (默认3685)
app.run(host='0.0.0.0', port=3685, debug=True)
```

### 网络配置

- **局域网访问**: 使用 `0.0.0.0` 允许局域网内其他设备访问
- **端口设置**: 默认端口3685，可在防火墙中开放
- **HTTPS**: 生产环境建议配置SSL证书

## 🚨 安全注意事项

1. **文件验证**: 服务器会验证文件类型和大小
2. **MD5校验**: 自动计算和验证文件完整性
3. **路径安全**: 使用secure_filename防止路径遍历
4. **大小限制**: 默认限制2MB，防止DoS攻击
5. **网络安全**: 建议在受信任的网络环境中使用

## 🐛 故障排除

### 常见问题

**1. 服务器无法启动**
```bash
# 检查端口是否被占用
netstat -an | grep 3685

# 更换端口
python server.py  # 修改server.py中的端口号
```

**2. STM32无法连接**
```bash
# 检查防火墙设置
sudo ufw allow 3685

# 检查IP地址
ip addr show
```

**3. 文件上传失败**
- 检查文件大小是否超过2MB限制
- 确认文件扩展名为.bin或.hex
- 检查磁盘空间是否充足

**4. ESP8266连接问题**
- 确认ESP8266和服务器在同一网络
- 检查服务器IP地址是否正确
- 验证网络连通性: `ping <server_ip>`

## 📊 性能参数

- **并发连接**: 支持多个STM32同时下载
- **文件大小**: 最大2MB (可配置)
- **传输速度**: 取决于网络条件和ESP8266性能
- **存储格式**: 自动生成版本化文件名
- **数据持久化**: JSON格式存储固件元数据

## 🔄 开发扩展

### 添加新功能

1. **用户认证**: 添加登录系统
2. **固件加密**: 支持加密固件文件
3. **日志记录**: 详细的操作日志
4. **邮件通知**: 固件更新通知
5. **数据库**: 替换JSON为SQL数据库

### API扩展

```python
@app.route('/api/firmware/verify', methods=['POST'])
def verify_firmware():
    """固件完整性验证"""
    pass

@app.route('/api/device/register', methods=['POST'])  
def register_device():
    """设备注册管理"""
    pass
```

## 📞 技术支持

- 检查server.py中的日志输出
- 访问 `/api/test` 验证服务器状态
- 使用浏览器开发者工具调试API
- 参考STM32 bootloader文档

## 🎯 项目特点

- **独立部署**: 作为独立项目运行，不依赖其他代码库
- **轻量级**: 基于Flask的简洁实现，易于维护和扩展
- **多平台**: 支持Linux、Windows、macOS等操作系统
- **安全可靠**: 内置文件验证、类型检查和完整性校验
- **易于集成**: 标准REST API接口，支持各种STM32项目

---

**STM32 OTA固件更新服务器 | Generated with Claude Code**