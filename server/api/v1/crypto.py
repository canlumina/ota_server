#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Blueprint, request, jsonify, current_app

from server.services.crypto_service import CryptoService

bp = Blueprint('crypto', __name__)

def get_crypto_service():
    """获取加密服务实例"""
    if not hasattr(current_app, 'crypto_service'):
        current_app.crypto_service = CryptoService()
    return current_app.crypto_service

@bp.route('/algorithms', methods=['GET'])
def get_supported_algorithms():
    """获取支持的加密算法"""
    try:
        service = get_crypto_service()
        algorithms = service.get_supported_algorithms()
        
        return jsonify({
            'success': True,
            'data': {
                'algorithms': algorithms,
                'count': len(algorithms)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/key/generate', methods=['POST'])
def generate_key():
    """生成加密密钥"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        algorithm = data.get('algorithm', 'aes-128-cbc')
        password = data.get('password')
        
        service = get_crypto_service()
        result = service.generate_key(algorithm, password)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': '密钥生成成功',
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

@bp.route('/encrypt', methods=['POST'])
def encrypt_data():
    """加密数据"""
    try:
        service = get_crypto_service()
        
        if 'data' in request.files:
            # 文件上传方式
            file = request.files['data']
            if file.filename == '':
                return jsonify({
                    'success': False,
                    'error': '文件名为空'
                }), 400
            
            result = service.encrypt_file(
                file=file,
                algorithm=request.form.get('algorithm', 'aes-128-cbc'),
                password=request.form.get('password'),
                key_hex=request.form.get('key')
            )
        else:
            # JSON数据方式
            json_data = request.get_json()
            if not json_data:
                return jsonify({
                    'success': False,
                    'error': '请求数据为空'
                }), 400
            
            result = service.encrypt_data(
                data_hex=json_data.get('data'),
                algorithm=json_data.get('algorithm', 'aes-128-cbc'),
                password=json_data.get('password'),
                key_hex=json_data.get('key')
            )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': '数据加密成功',
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

@bp.route('/decrypt', methods=['POST'])
def decrypt_data():
    """解密数据"""
    try:
        service = get_crypto_service()
        
        if 'data' in request.files:
            # 文件上传方式
            file = request.files['data']
            if file.filename == '':
                return jsonify({
                    'success': False,
                    'error': '文件名为空'
                }), 400
            
            result = service.decrypt_file(
                file=file,
                algorithm=request.form.get('algorithm', 'aes-128-cbc'),
                password=request.form.get('password'),
                key_hex=request.form.get('key')
            )
        else:
            # JSON数据方式
            json_data = request.get_json()
            if not json_data:
                return jsonify({
                    'success': False,
                    'error': '请求数据为空'
                }), 400
            
            result = service.decrypt_data(
                encrypted_hex=json_data.get('data'),
                algorithm=json_data.get('algorithm', 'aes-128-cbc'),
                password=json_data.get('password'),
                key_hex=json_data.get('key')
            )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': '数据解密成功',
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

@bp.route('/verify', methods=['POST'])
def verify_data():
    """验证数据完整性"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        service = get_crypto_service()
        result = service.verify_data(
            data_hex=data.get('data'),
            expected_hash=data.get('expected_hash'),
            algorithm=data.get('hash_algorithm', 'sha256')
        )
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500