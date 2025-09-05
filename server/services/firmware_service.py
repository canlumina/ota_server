#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Response, send_file

from server.core.firmware_manager import FirmwareManager
from server.core.crypto import EncryptionType
from server.config.settings import get_config

class FirmwareService:
    """固件服务"""
    
    def __init__(self):
        config = get_config()
        self.upload_folder = config.FIRMWARE_FOLDER
        self.firmware_manager = FirmwareManager(self.upload_folder)
    
    def list_firmwares(self, target_device=None, encrypted_only=None):
        """获取固件列表"""
        firmwares = self.firmware_manager.list_firmwares(
            target_device=target_device,
            encrypted_only=encrypted_only
        )
        
        firmware_list = []
        latest_firmware = self.firmware_manager.get_latest_version_firmware(target_device)
        
        for fw in firmwares:
            fw_dict = fw.to_dict()
            fw_dict['is_latest'] = (latest_firmware and fw.id == latest_firmware.id)
            firmware_list.append(fw_dict)
        
        return firmware_list
    
    def upload_firmware(self, file, version=None, target_device='STM32F103ZET6', description='', 
                       encryption_type='none', key_method='password', password='', encryption_key=''):
        """上传固件"""
        try:
            # 检查文件扩展名
            allowed_extensions = {'.bin', '.hex', '.elf'}
            file_ext = os.path.splitext(file.filename.lower())[1]
            if file_ext not in allowed_extensions:
                return {
                    'success': False,
                    'error': f'只支持 {", ".join(allowed_extensions)} 格式的固件文件'
                }
            
            # 保存文件
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_filename = f"{timestamp}_{filename}"
            
            upload_path = self.upload_folder / safe_filename
            file.save(str(upload_path))
            
            # 添加到固件管理器
            firmware = self.firmware_manager.add_firmware(
                file_path=str(upload_path),
                original_filename=filename,
                version=version,
                target_device=target_device,
                metadata={
                    'upload_source': 'web_api',
                    'upload_timestamp': datetime.now().isoformat(),
                    'description': description
                }
            )
            
            # 如果指定了加密，立即进行加密处理
            if encryption_type != 'none':
                encrypt_result = self.encrypt_firmware(
                    firmware_id=firmware.id,
                    algorithm=encryption_type,
                    password=password if key_method == 'password' else None,
                    key_hex=encryption_key if key_method == 'manual' else None
                )
                
                if not encrypt_result['success']:
                    # 如果加密失败，删除已上传的固件
                    self.delete_firmware(firmware.id)
                    return {
                        'success': False,
                        'error': f'固件加密失败: {encrypt_result["error"]}'
                    }
                
                # 返回加密后的固件信息
                return {
                    'success': True,
                    'data': encrypt_result['data']
                }
            
            return {
                'success': True,
                'data': firmware.to_dict()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_firmware_detail(self, firmware_id):
        """获取固件详情"""
        firmware = self.firmware_manager.get_firmware(firmware_id)
        return firmware.to_dict() if firmware else None
    
    def delete_firmware(self, firmware_id):
        """删除固件"""
        if self.firmware_manager.remove_firmware(firmware_id):
            return {'success': True}
        else:
            return {'success': False, 'error': '固件不存在或删除失败'}
    
    def download_firmware(self, firmware_id, request):
        """下载固件"""
        firmware = self.firmware_manager.get_firmware(firmware_id)
        if not firmware:
            return {'success': False, 'error': '固件不存在'}
        
        file_path = self.firmware_manager.get_firmware_path(firmware_id)
        if not file_path or not file_path.exists():
            return {'success': False, 'error': '固件文件不存在'}
        
        response = self._send_file_with_range(
            str(file_path),
            firmware.original_filename,
            'application/octet-stream',
            request
        )
        
        # 添加加密信息到响应头
        if firmware.is_encrypted:
            response.headers['X-Firmware-Encrypted'] = 'true'
            response.headers['X-Encryption-Algorithm'] = firmware.encryption_algorithm
            # 添加加密密码
            if firmware.encryption_metadata and 'password' in firmware.encryption_metadata:
                response.headers['X-Encryption-Password'] = firmware.encryption_metadata['password']
        else:
            response.headers['X-Firmware-Encrypted'] = 'false'
        
        return {'success': True, 'response': response}
    
    def encrypt_firmware(self, firmware_id, algorithm, password=None, key_hex=None):
        """加密固件"""
        try:
            # 验证加密算法
            try:
                algo_enum = EncryptionType(algorithm)
            except ValueError:
                return {
                    'success': False,
                    'error': f'不支持的加密算法: {algorithm}'
                }
            
            # 处理密钥
            key_bytes = None
            if key_hex:
                try:
                    key_bytes = bytes.fromhex(key_hex)
                except ValueError:
                    return {
                        'success': False,
                        'error': '密钥格式错误，请提供十六进制格式的密钥'
                    }
            
            # 执行加密
            if self.firmware_manager.encrypt_firmware(firmware_id, algo_enum, password, key_bytes):
                firmware = self.firmware_manager.get_firmware(firmware_id)
                return {
                    'success': True,
                    'data': firmware.to_dict() if firmware else None
                }
            else:
                return {
                    'success': False,
                    'error': '固件加密失败'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_latest_firmware(self, target_device=None, download=False, request=None):
        """获取最新版本固件"""
        latest_firmware = self.firmware_manager.get_latest_version_firmware(target_device)
        
        if not latest_firmware:
            return {
                'success': False,
                'error': '没有找到固件'
            }
        
        if download:
            file_path = self.firmware_manager.get_firmware_path(latest_firmware.id)
            if not file_path or not file_path.exists():
                return {
                    'success': False,
                    'error': '固件文件不存在'
                }
            
            response = self._send_file_with_range(
                str(file_path),
                latest_firmware.original_filename,
                'application/octet-stream',
                request
            )
            
            # 添加固件信息到响应头
            if latest_firmware.is_encrypted:
                response.headers['X-Firmware-Encrypted'] = 'true'
                response.headers['X-Encryption-Algorithm'] = latest_firmware.encryption_algorithm
                # 添加加密密码
                if latest_firmware.encryption_metadata and 'password' in latest_firmware.encryption_metadata:
                    response.headers['X-Encryption-Password'] = latest_firmware.encryption_metadata['password']
            else:
                response.headers['X-Firmware-Encrypted'] = 'false'
            
            response.headers['X-Firmware-Size'] = str(latest_firmware.size)
            response.headers['X-Firmware-Version'] = latest_firmware.version
            
            return {'success': True, 'response': response}
        
        # 返回固件信息
        firmware_dict = latest_firmware.to_dict()
        firmware_dict['is_latest'] = True
        firmware_dict['download_url'] = f'/api/v1/firmwares/latest?download=true'
        if target_device:
            firmware_dict['download_url'] += f'&target_device={target_device}'
        
        from flask import jsonify
        response = jsonify({
            'success': True,
            'data': firmware_dict,
            'message': f'获取最新固件成功: {latest_firmware.version}'
        })
        
        # 添加固件元信息到HTTP响应头
        response.headers['X-Firmware-Size'] = str(latest_firmware.size)
        response.headers['X-Firmware-Version'] = latest_firmware.version
        response.headers['X-Firmware-Filename'] = latest_firmware.original_filename
        
        if latest_firmware.is_encrypted:
            response.headers['X-Firmware-Encrypted'] = 'true'
            response.headers['X-Encryption-Algorithm'] = latest_firmware.encryption_algorithm
            # 添加加密密码
            if latest_firmware.encryption_metadata and 'password' in latest_firmware.encryption_metadata:
                response.headers['X-Encryption-Password'] = latest_firmware.encryption_metadata['password']
        else:
            response.headers['X-Firmware-Encrypted'] = 'false'
        
        return {'success': True, 'response': response}
    
    def get_firmware_by_version(self, version, target_device=None, download=False, request=None):
        """根据版本号获取固件"""
        firmwares = self.firmware_manager.list_firmwares(target_device=target_device)
        
        # 标准化版本号
        if not version.startswith('v'):
            version = f'v{version}'
        
        # 查找匹配版本的固件
        matching_firmware = None
        for firmware in firmwares:
            if firmware.version == version:
                matching_firmware = firmware
                break
        
        if not matching_firmware:
            return {
                'success': False,
                'error': f'没有找到版本 {version} 的固件'
            }
        
        if download:
            file_path = self.firmware_manager.get_firmware_path(matching_firmware.id)
            if not file_path or not file_path.exists():
                return {
                    'success': False,
                    'error': '固件文件不存在'
                }
            
            response = self._send_file_with_range(
                str(file_path),
                matching_firmware.original_filename,
                'application/octet-stream',
                request
            )
            
            # 添加加密信息到响应头
            if matching_firmware.is_encrypted:
                response.headers['X-Firmware-Encrypted'] = 'true'
                response.headers['X-Encryption-Algorithm'] = matching_firmware.encryption_algorithm
                # 添加加密密码
                if matching_firmware.encryption_metadata and 'password' in matching_firmware.encryption_metadata:
                    response.headers['X-Encryption-Password'] = matching_firmware.encryption_metadata['password']
            else:
                response.headers['X-Firmware-Encrypted'] = 'false'
            
            return {'success': True, 'response': response}
        
        # 返回固件信息
        firmware_dict = matching_firmware.to_dict()
        latest_firmware = self.firmware_manager.get_latest_version_firmware(target_device)
        firmware_dict['is_latest'] = (latest_firmware and matching_firmware.id == latest_firmware.id)
        firmware_dict['download_url'] = f'/api/v1/firmwares/version/{version}?download=true'
        if target_device:
            firmware_dict['download_url'] += f'&target_device={target_device}'
        
        from flask import jsonify
        response = jsonify({
            'success': True,
            'data': firmware_dict,
            'message': f'获取固件成功: {version}'
        })
        
        return {'success': True, 'response': response}
    
    def list_firmware_versions(self, target_device=None):
        """获取所有固件版本列表"""
        firmwares = self.firmware_manager.list_firmwares(target_device=target_device)
        latest_firmware = self.firmware_manager.get_latest_version_firmware(target_device)
        
        versions = []
        for firmware in firmwares:
            version_info = {
                'version': firmware.version,
                'id': firmware.id,
                'filename': firmware.original_filename,
                'size': firmware.size,
                'upload_time': firmware.upload_time,
                'is_encrypted': firmware.is_encrypted,
                'is_latest': (latest_firmware and firmware.id == latest_firmware.id)
            }
            versions.append(version_info)
        
        return {
            'versions': versions,
            'count': len(versions),
            'latest_version': latest_firmware.version if latest_firmware else None
        }
    
    def _send_file_with_range(self, file_path, original_filename, mimetype, request):
        """支持Range请求的文件发送函数"""
        file_size = os.path.getsize(file_path)
        
        range_header = request.headers.get('Range', None)
        if not range_header:
            return send_file(
                file_path,
                as_attachment=True,
                download_name=original_filename,
                mimetype=mimetype
            )
        
        # 解析Range请求
        m = re.search(r'bytes=(\d+)-(\d*)', range_header)
        if not m:
            return send_file(
                file_path,
                as_attachment=True,
                download_name=original_filename,
                mimetype=mimetype
            )
        
        start = int(m.group(1))
        end = int(m.group(2)) if m.group(2) else file_size - 1
        
        start = max(0, min(start, file_size - 1))
        end = max(start, min(end, file_size - 1))
        
        content_length = end - start + 1
        
        # 读取指定范围的数据
        with open(file_path, 'rb') as f:
            f.seek(start)
            data = f.read(content_length)
        
        # 创建206 Partial Content响应
        response = Response(data, 206, mimetype=mimetype)
        response.headers.add('Content-Range', f'bytes {start}-{end}/{file_size}')
        response.headers.add('Content-Length', str(content_length))
        response.headers.add('Accept-Ranges', 'bytes')
        response.headers.add('Content-Disposition', f'attachment; filename="{original_filename}"')
        
        return response