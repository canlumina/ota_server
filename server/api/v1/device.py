#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from flask import Blueprint, request, jsonify, current_app

from server.services.device_service import DeviceService

bp = Blueprint('device', __name__)

def get_device_service():
    """获取设备服务实例"""
    if not hasattr(current_app, 'device_service'):
        current_app.device_service = DeviceService()
    return current_app.device_service

@bp.route('/ports', methods=['GET'])
def get_serial_ports():
    """获取可用串口列表"""
    try:
        service = get_device_service()
        ports = service.get_available_ports()
        
        return jsonify({
            'success': True,
            'data': {
                'ports': ports,
                'count': len(ports)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('', methods=['GET'])
def get_devices():
    """获取设备列表"""
    try:
        service = get_device_service()
        devices = service.get_device_list()
        
        return jsonify({
            'success': True,
            'data': {
                'devices': devices,
                'count': len(devices)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/connect', methods=['POST'])
def connect_device():
    """连接设备"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        port = data.get('port')
        baudrate = data.get('baudrate', 115200)
        
        if not port:
            return jsonify({
                'success': False,
                'error': '端口参数不能为空'
            }), 400
        
        service = get_device_service()
        result = service.connect_device(port, baudrate)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': f'设备 {port} 连接成功',
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

@bp.route('/disconnect', methods=['POST'])
def disconnect_device():
    """断开设备"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        port = data.get('port')
        if not port:
            return jsonify({
                'success': False,
                'error': '端口参数不能为空'
            }), 400
        
        service = get_device_service()
        result = service.disconnect_device(port)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message']
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

@bp.route('/<path:device_id>/status', methods=['GET'])
def get_device_status(device_id):
    """获取设备状态"""
    try:
        service = get_device_service()
        result = service.get_device_status(device_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['data']
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

@bp.route('/<path:device_id>/command', methods=['POST'])
def send_device_command(device_id):
    """发送设备命令"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        command = data.get('command', '')
        if not command:
            return jsonify({
                'success': False,
                'error': '命令参数不能为空'
            }), 400
        
        service = get_device_service()
        result = service.send_command(device_id, command)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': '命令发送成功',
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

@bp.route('/<path:device_id>/messages', methods=['GET'])
def get_device_messages(device_id):
    """获取设备消息"""
    try:
        service = get_device_service()
        result = service.get_device_messages(device_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': {
                    'messages': result['data'],
                    'count': len(result['data'])
                }
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

@bp.route('/<path:device_id>/info', methods=['GET'])
def get_device_info(device_id):
    """获取设备信息"""
    try:
        service = get_device_service()
        result = service.get_device_info(device_id)
        
        if result['success']:
            return jsonify({
                'success': True,
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

@bp.route('/<path:device_id>/bootloader/<command>', methods=['POST'])
def bootloader_command(device_id, command):
    """执行bootloader命令"""
    try:
        service = get_device_service()
        result = service.execute_bootloader_command(device_id, command)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': f'Bootloader命令 {command} 执行成功',
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