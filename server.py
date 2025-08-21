#!/usr/bin/env python3
"""
STM32 OTA 固件更新服务器
支持固件上传、下载和版本管理

作者: Generated with Claude Code
"""

import os
import hashlib
import json
import time
from datetime import datetime
from flask import Flask, request, render_template, jsonify, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

app = Flask(__name__)
app.secret_key = 'stm32_ota_server_secret_key_2025'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB 最大文件大小

# 配置
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'bin', 'hex'}
FIRMWARE_INFO_FILE = 'firmware_info.json'

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_md5(file_path):
    """计算文件MD5值"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def load_firmware_info():
    """加载固件信息"""
    if os.path.exists(FIRMWARE_INFO_FILE):
        try:
            with open(FIRMWARE_INFO_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_firmware_info(info):
    """保存固件信息"""
    with open(FIRMWARE_INFO_FILE, 'w', encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False, indent=2)

def get_file_size(file_path):
    """获取文件大小"""
    return os.path.getsize(file_path)

@app.route('/')
def index():
    """主页 - 固件上传界面"""
    firmware_info = load_firmware_info()
    return render_template('index.html', firmware_list=firmware_info)

@app.route('/upload', methods=['POST'])
def upload_file():
    """处理固件上传"""
    try:
        if 'file' not in request.files:
            flash('没有选择文件', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        version = request.form.get('version', '').strip()
        description = request.form.get('description', '').strip()
        
        if file.filename == '':
            flash('没有选择文件', 'error')
            return redirect(request.url)
        
        if not version:
            flash('请输入版本号', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # 生成安全的文件名
            original_filename = secure_filename(file.filename)
            timestamp = int(time.time())
            filename = f"firmware_v{version}_{timestamp}.bin"
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            
            # 保存文件
            file.save(file_path)
            
            # 计算文件信息
            file_size = get_file_size(file_path)
            md5_hash = calculate_md5(file_path)
            
            # 更新固件信息
            firmware_info = load_firmware_info()
            firmware_info[version] = {
                'filename': filename,
                'original_name': original_filename,
                'size': file_size,
                'md5': md5_hash,
                'description': description,
                'upload_time': datetime.now().isoformat(),
                'download_count': 0
            }
            save_firmware_info(firmware_info)
            
            flash(f'固件上传成功！版本: {version}, 大小: {file_size} 字节, MD5: {md5_hash}', 'success')
            return redirect(url_for('index'))
        else:
            flash('不支持的文件类型，请上传 .bin 或 .hex 文件', 'error')
            return redirect(request.url)
            
    except RequestEntityTooLarge:
        flash('文件太大，最大支持2MB', 'error')
        return redirect(request.url)
    except Exception as e:
        flash(f'上传失败: {str(e)}', 'error')
        return redirect(request.url)

@app.route('/manage')
def manage():
    """固件管理页面"""
    firmware_info = load_firmware_info()
    return render_template('manage.html', firmware_list=firmware_info)

@app.route('/delete/<version>', methods=['POST'])
def delete_firmware(version):
    """删除固件"""
    try:
        firmware_info = load_firmware_info()
        if version in firmware_info:
            # 删除文件
            filename = firmware_info[version]['filename']
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # 删除记录
            del firmware_info[version]
            save_firmware_info(firmware_info)
            
            flash(f'固件版本 {version} 已删除', 'success')
        else:
            flash('固件版本不存在', 'error')
    except Exception as e:
        flash(f'删除失败: {str(e)}', 'error')
    
    return redirect(url_for('manage'))

# STM32 API 接口

@app.route('/api/firmware/list', methods=['GET'])
def api_firmware_list():
    """API: 获取固件列表（给STM32使用）"""
    firmware_info = load_firmware_info()
    
    # 转换为STM32友好的格式
    firmware_list = []
    for version, info in firmware_info.items():
        firmware_list.append({
            'version': version,
            'size': info['size'],
            'md5': info['md5'],
            'description': info['description'],
            'upload_time': info['upload_time']
        })
    
    # 按版本排序（最新的在前）
    firmware_list.sort(key=lambda x: x['upload_time'], reverse=True)
    
    return jsonify({
        'status': 'success',
        'count': len(firmware_list),
        'firmware': firmware_list
    })

@app.route('/api/firmware/latest', methods=['GET'])
def api_latest_firmware():
    """API: 获取最新固件信息"""
    firmware_info = load_firmware_info()
    
    if not firmware_info:
        return jsonify({
            'status': 'error',
            'message': 'No firmware available'
        }), 404
    
    # 找到最新的固件
    latest_version = max(firmware_info.keys(), 
                        key=lambda k: firmware_info[k]['upload_time'])
    latest_info = firmware_info[latest_version]
    
    return jsonify({
        'status': 'success',
        'version': latest_version,
        'size': latest_info['size'],
        'md5': latest_info['md5'],
        'description': latest_info['description'],
        'download_url': f'/api/firmware/download/{latest_version}'
    })

@app.route('/api/firmware/info/<version>', methods=['GET'])
def api_firmware_info(version):
    """API: 获取指定版本固件信息"""
    firmware_info = load_firmware_info()
    
    if version not in firmware_info:
        return jsonify({
            'status': 'error',
            'message': 'Firmware version not found'
        }), 404
    
    info = firmware_info[version]
    return jsonify({
        'status': 'success',
        'version': version,
        'size': info['size'],
        'md5': info['md5'],
        'description': info['description'],
        'download_url': f'/api/firmware/download/{version}'
    })

@app.route('/api/firmware/download/<version>', methods=['GET'])
def api_download_firmware(version):
    """API: 下载指定版本固件"""
    firmware_info = load_firmware_info()
    
    # 支持"latest"作为特殊版本参数
    if version == 'latest':
        if not firmware_info:
            return jsonify({
                'status': 'error',
                'message': 'No firmware available'
            }), 404
        
        # 获取最新版本（简单字符串排序，假设版本格式为x.y.z）
        sorted_versions = sorted(firmware_info.keys(), reverse=True)
        version = sorted_versions[0]
    
    if version not in firmware_info:
        return jsonify({
            'status': 'error',
            'message': 'Firmware version not found'
        }), 404
    
    info = firmware_info[version]
    filename = info['filename']
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    if not os.path.exists(file_path):
        return jsonify({
            'status': 'error',
            'message': 'Firmware file not found'
        }), 404
    
    # 更新下载计数
    firmware_info[version]['download_count'] = info.get('download_count', 0) + 1
    save_firmware_info(firmware_info)
    
    # 设置适合STM32的响应头
    return send_file(
        file_path,
        as_attachment=True,
        download_name=f'firmware_v{version}.bin',
        mimetype='application/octet-stream'
    )

@app.route('/api/test', methods=['GET'])
def api_test():
    """API: 测试连接"""
    return jsonify({
        'status': 'success',
        'message': 'STM32 OTA Server is running',
        'timestamp': datetime.now().isoformat(),
        'server_info': {
            'max_file_size': '2MB',
            'supported_formats': ['bin', 'hex'],
            'api_version': '1.0'
        }
    })

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({
        'status': 'error',
        'message': 'API endpoint not found'
    }), 404

@app.errorhandler(413)
def too_large_error(error):
    return jsonify({
        'status': 'error',
        'message': 'File too large (max 2MB)'
    }), 413

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500

if __name__ == '__main__':
    print("=" * 50)
    print("STM32 OTA 固件更新服务器")
    print("=" * 50)
    print("Web 界面: http://localhost:3685")
    print("管理界面: http://localhost:3685/manage")
    print("API 测试: http://localhost:3685/api/test")
    print("=" * 50)
    print("STM32 API 接口:")
    print("  获取固件列表: GET /api/firmware/list")
    print("  获取最新固件: GET /api/firmware/latest") 
    print("  获取固件信息: GET /api/firmware/info/<version>")
    print("  下载固件:     GET /api/firmware/download/<version>")
    print("=" * 50)
    
    # 启动服务器
    app.run(host='0.0.0.0', port=3685, debug=True)