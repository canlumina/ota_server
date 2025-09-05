#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify
from datetime import datetime

bp = Blueprint('base', __name__)

@bp.route('', methods=['GET'])
@bp.route('/', methods=['GET'])
def api_info():
    """API根路径 - 返回API信息"""
    return jsonify({
        'success': True,
        'message': 'STM32 OTA Server API v1',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'firmwares': '/api/v1/firmwares',
            'devices': '/api/v1/devices', 
            'crypto': '/api/v1/crypto',
            'system': '/api/v1/system'
        },
        'documentation': 'https://github.com/your-org/stm32-ota-server/docs'
    })

@bp.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'STM32 OTA Server'
    })