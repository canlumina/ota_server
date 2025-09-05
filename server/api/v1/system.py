#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, current_app

from server.services.system_service import SystemService

bp = Blueprint('system', __name__)

def get_system_service():
    """获取系统服务实例"""
    if not hasattr(current_app, 'system_service'):
        current_app.system_service = SystemService()
    return current_app.system_service

@bp.route('/info', methods=['GET'])
def get_system_info():
    """获取系统信息"""
    try:
        service = get_system_service()
        info = service.get_system_info()
        
        return jsonify({
            'success': True,
            'data': info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/health', methods=['GET'])
def get_health_status():
    """获取系统健康状态"""
    try:
        service = get_system_service()
        health = service.get_health_status()
        
        return jsonify({
            'success': True,
            'data': health
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/stats', methods=['GET'])
def get_system_stats():
    """获取系统统计信息"""
    try:
        service = get_system_service()
        stats = service.get_system_stats()
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/logs', methods=['GET'])
def get_system_logs():
    """获取系统日志"""
    try:
        service = get_system_service()
        logs = service.get_recent_logs()
        
        return jsonify({
            'success': True,
            'data': {
                'logs': logs,
                'count': len(logs)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500