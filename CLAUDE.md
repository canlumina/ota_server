# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a standalone Flask-based STM32 OTA (Over-The-Air) firmware update server. It provides web interfaces for firmware upload/management and REST API endpoints for STM32 devices to check for and download firmware updates.

## Key Architecture

### Core Components
- **server.py** - Main Flask application with all routes and business logic
- **templates/** - Jinja2 HTML templates for web UI (index.html for upload, manage.html for management)  
- **static/style.css** - CSS styling for the web interface
- **uploads/** - Directory where firmware files are stored (auto-created)
- **firmware_info.json** - JSON database storing firmware metadata (auto-generated)

### API Structure
The server provides both web interfaces and REST APIs:
- Web UI: `/` (upload), `/manage` (management)
- STM32 APIs: `/api/firmware/list`, `/api/firmware/latest`, `/api/firmware/info/<version>`, `/api/firmware/download/<version>`, `/api/test`

## Development Commands

### Running the Server
```bash
# Install dependencies
pip install -r requirements.txt

# Run the server in development mode
python server.py
```

The server runs on `http://localhost:3685` with debug mode enabled.

### Dependencies
- Flask 3.0.0
- Werkzeug 3.0.1

No additional build tools, test frameworks, or linters are configured in this project.

## Configuration

### Server Settings (in server.py)
- `MAX_CONTENT_LENGTH`: 2MB file size limit
- `UPLOAD_FOLDER`: 'uploads' directory for firmware storage
- `ALLOWED_EXTENSIONS`: {'bin', 'hex'} file types
- `app.secret_key`: Flask session secret
- Server port: 3685

### File Naming Convention
Uploaded firmware files are renamed to: `firmware_v{version}_{timestamp}.bin`

## Data Storage

### Firmware Metadata (firmware_info.json)
```json
{
  "version": {
    "filename": "firmware_v1.0.0_timestamp.bin",
    "original_name": "original_filename.bin", 
    "size": file_size_bytes,
    "md5": "md5_hash",
    "description": "version description",
    "upload_time": "ISO_datetime",
    "download_count": 0
  }
}
```

## Security Features

- File type validation (only .bin/.hex allowed)
- File size limits (2MB max)
- Secure filename generation using werkzeug.utils.secure_filename
- MD5 hash calculation for file integrity
- Request size limits to prevent DoS

## STM32 Integration

The server is designed to work with STM32 bootloaders that can make HTTP requests via ESP8266 or similar WiFi modules. The API returns JSON responses with firmware metadata and provides binary file downloads.

### Typical STM32 Update Flow
1. STM32 calls `/api/firmware/latest` to check for new firmware
2. Compares version/MD5 with current firmware
3. Downloads via `/api/firmware/download/<version>` if update needed
4. Writes firmware to external flash and triggers bootloader update

## Error Handling

The server includes error handlers for:
- 404: API endpoint not found
- 413: File too large 
- 500: Internal server error
- Request validation errors return appropriate flash messages for web UI