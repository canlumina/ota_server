#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from datetime import datetime

from server.services.firmware_service import FirmwareService
from server.core.crypto import EncryptionType

bp = Blueprint('firmware', __name__)

def get_firmware_service():
    """获取固件服务实例"""
    if not hasattr(current_app, 'firmware_service'):
        current_app.firmware_service = FirmwareService()
    return current_app.firmware_service

@bp.route('', methods=['GET'])
def get_firmwares():
    """获取固件列表"""
    try:
        target_device = request.args.get('target_device')
        encrypted_only = request.args.get('encrypted_only')
        
        if encrypted_only is not None:
            encrypted_only = encrypted_only.lower() == 'true'
        
        service = get_firmware_service()
        firmwares = service.list_firmwares(
            target_device=target_device,
            encrypted_only=encrypted_only
        )
        
        # 获取最新版本固件
        firmware_manager = service.firmware_manager
        latest_firmware = firmware_manager.get_latest_version_firmware(target_device)
        
        # 为固件列表添加is_latest标记
        firmware_list = []
        for fw in firmwares:
            fw_dict = fw.copy()
            fw_dict['is_latest'] = (latest_firmware and fw.get('id') == latest_firmware.id)
            firmware_list.append(fw_dict)
        
        return jsonify({
            'success': True,
            'data': {
                'firmwares': firmware_list,
                'count': len(firmware_list),
                'latest_firmware_id': latest_firmware.id if latest_firmware else None
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('', methods=['POST'])
def upload_firmware():
    """上传固件"""
    try:
        if 'firmware' not in request.files:
            return jsonify({
                'success': False,
                'error': '未选择固件文件'
            }), 400
        
        file = request.files['firmware']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': '文件名为空'
            }), 400
        
        # 获取参数
        version = request.form.get('version', '').strip()
        target_device = request.form.get('target_device', 'STM32F103ZET6')
        description = request.form.get('description', '')
        
        # 获取加密参数
        encryption_type = request.form.get('encryption_type', 'none')
        key_method = request.form.get('key_method', 'password')
        password = request.form.get('password', '')
        encryption_key = request.form.get('encryption_key', '')
        
        # 验证版本号格式
        if version and version != 'auto':
            version_pattern = r'^v?\d+\.\d+\.\d+\.\d+$'
            if not re.match(version_pattern, version):
                return jsonify({
                    'success': False,
                    'error': '版本号格式不正确。请使用标准格式：v主版本.次版本.修订版.构建版 (例如: v2.1.5.2024)'
                }), 400
            
            if not version.startswith('v'):
                version = 'v' + version
        
        # 验证加密参数
        if encryption_type != 'none':
            if encryption_type not in ['xor', 'aes-128-cbc', 'aes-256-cbc']:
                return jsonify({
                    'success': False,
                    'error': '不支持的加密算法'
                }), 400
            
            # 如果选择了加密，必须提供密码或密钥
            if key_method == 'password' and not password:
                return jsonify({
                    'success': False,
                    'error': '请输入加密密码'
                }), 400
            elif key_method == 'manual' and not encryption_key:
                return jsonify({
                    'success': False,
                    'error': '请输入加密密钥'
                }), 400
        
        service = get_firmware_service()
        result = service.upload_firmware(
            file=file,
            version=version,
            target_device=target_device,
            description=description,
            encryption_type=encryption_type,
            key_method=key_method,
            password=password,
            encryption_key=encryption_key
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': '固件上传成功',
                'data': result['data']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/<firmware_id>', methods=['GET'])
def get_firmware(firmware_id):
    """获取固件详情"""
    try:
        service = get_firmware_service()
        firmware = service.get_firmware_detail(firmware_id)
        
        if firmware:
            return jsonify({
                'success': True,
                'data': firmware
            })
        else:
            return jsonify({
                'success': False,
                'error': '固件不存在'
            }), 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/<firmware_id>', methods=['DELETE'])
def delete_firmware(firmware_id):
    """删除固件"""
    try:
        service = get_firmware_service()
        result = service.delete_firmware(firmware_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': '固件删除成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/<firmware_id>/download', methods=['GET'])
def download_firmware(firmware_id):
    """下载固件"""
    try:
        service = get_firmware_service()
        result = service.download_firmware(firmware_id, request)
        
        if result['success']:
            return result['response']
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/<firmware_id>/encrypt', methods=['POST'])
def encrypt_firmware(firmware_id):
    """加密固件"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        service = get_firmware_service()
        result = service.encrypt_firmware(
            firmware_id=firmware_id,
            algorithm=data.get('algorithm', 'none'),
            password=data.get('password'),
            key_hex=data.get('key')
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': '固件加密成功',
                'data': result['data']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/latest', methods=['GET'])
def get_latest_firmware():
    """获取最新版本固件"""
    try:
        target_device = request.args.get('target_device')
        download = request.args.get('download', 'false').lower() == 'true'
        
        service = get_firmware_service()
        result = service.get_latest_firmware(target_device, download, request)
        
        if result['success']:
            return result['response']
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/version/<version>', methods=['GET'])
def get_firmware_by_version(version):
    """根据版本号获取固件"""
    try:
        target_device = request.args.get('target_device')
        download = request.args.get('download', 'false').lower() == 'true'
        
        service = get_firmware_service()
        result = service.get_firmware_by_version(version, target_device, download, request)
        
        if result['success']:
            return result['response']
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/versions', methods=['GET'])
def list_firmware_versions():
    """获取所有固件版本列表"""
    try:
        target_device = request.args.get('target_device')
        
        service = get_firmware_service()
        result = service.list_firmware_versions(target_device)
        
        return jsonify({
            'success': True,
            'data': result,
            'message': f'获取版本列表成功，共 {len(result["versions"])} 个版本'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500