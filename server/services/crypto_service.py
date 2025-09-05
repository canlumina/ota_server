#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from server.core.crypto import crypto_manager, EncryptionType

class CryptoService:
    """加密服务"""
    
    def __init__(self):
        self.crypto_manager = crypto_manager
    
    def get_supported_algorithms(self):
        """获取支持的加密算法"""
        return self.crypto_manager.get_supported_algorithms()
    
    def generate_key(self, algorithm, password=None):
        """生成加密密钥"""
        try:
            # 验证加密算法
            try:
                algo_enum = EncryptionType(algorithm)
            except ValueError:
                return {
                    'success': False,
                    'error': f'不支持的加密算法: {algorithm}'
                }
            
            # 生成密钥
            key = self.crypto_manager.generate_key(algo_enum, password)
            
            return {
                'success': True,
                'data': {
                    'algorithm': algorithm,
                    'key': key.hex() if key else '',
                    'key_length': len(key) if key else 0,
                    'password_based': bool(password)
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def encrypt_file(self, file, algorithm, password=None, key_hex=None):
        """加密文件数据"""
        try:
            # 验证加密算法
            try:
                algo_enum = EncryptionType(algorithm)
            except ValueError:
                return {
                    'success': False,
                    'error': f'不支持的加密算法: {algorithm}'
                }
            
            # 读取文件数据
            data_bytes = file.read()
            
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
            encrypted_data = self.crypto_manager.encrypt(data_bytes, algo_enum, password, key_bytes)
            
            return {
                'success': True,
                'data': {
                    'algorithm': algorithm,
                    'original_size': len(data_bytes),
                    'encrypted_size': len(encrypted_data),
                    'encrypted_data': encrypted_data.hex(),
                    'password_based': bool(password)
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def encrypt_data(self, data_hex, algorithm, password=None, key_hex=None):
        """加密十六进制数据"""
        try:
            # 验证加密算法
            try:
                algo_enum = EncryptionType(algorithm)
            except ValueError:
                return {
                    'success': False,
                    'error': f'不支持的加密算法: {algorithm}'
                }
            
            # 处理十六进制数据
            try:
                data_bytes = bytes.fromhex(data_hex) if data_hex else b''
            except ValueError:
                return {
                    'success': False,
                    'error': '数据格式错误，请提供十六进制格式的数据'
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
            encrypted_data = self.crypto_manager.encrypt(data_bytes, algo_enum, password, key_bytes)
            
            return {
                'success': True,
                'data': {
                    'algorithm': algorithm,
                    'original_size': len(data_bytes),
                    'encrypted_size': len(encrypted_data),
                    'encrypted_data': encrypted_data.hex(),
                    'password_based': bool(password)
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def decrypt_file(self, file, algorithm, password=None, key_hex=None):
        """解密文件数据"""
        try:
            # 验证加密算法
            try:
                algo_enum = EncryptionType(algorithm)
            except ValueError:
                return {
                    'success': False,
                    'error': f'不支持的加密算法: {algorithm}'
                }
            
            # 读取文件数据
            encrypted_bytes = file.read()
            
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
            
            # 执行解密
            decrypted_data = self.crypto_manager.decrypt(encrypted_bytes, algo_enum, password, key_bytes)
            
            return {
                'success': True,
                'data': {
                    'algorithm': algorithm,
                    'encrypted_size': len(encrypted_bytes),
                    'decrypted_size': len(decrypted_data),
                    'decrypted_data': decrypted_data.hex(),
                    'password_based': bool(password)
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def decrypt_data(self, encrypted_hex, algorithm, password=None, key_hex=None):
        """解密十六进制数据"""
        try:
            # 验证加密算法
            try:
                algo_enum = EncryptionType(algorithm)
            except ValueError:
                return {
                    'success': False,
                    'error': f'不支持的加密算法: {algorithm}'
                }
            
            # 处理十六进制数据
            try:
                encrypted_bytes = bytes.fromhex(encrypted_hex) if encrypted_hex else b''
            except ValueError:
                return {
                    'success': False,
                    'error': '数据格式错误，请提供十六进制格式的加密数据'
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
            
            # 执行解密
            decrypted_data = self.crypto_manager.decrypt(encrypted_bytes, algo_enum, password, key_bytes)
            
            return {
                'success': True,
                'data': {
                    'algorithm': algorithm,
                    'encrypted_size': len(encrypted_bytes),
                    'decrypted_size': len(decrypted_data),
                    'decrypted_data': decrypted_data.hex(),
                    'password_based': bool(password)
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_data(self, data_hex, expected_hash, algorithm='sha256'):
        """验证数据完整性"""
        try:
            # 处理十六进制数据
            try:
                data_bytes = bytes.fromhex(data_hex) if data_hex else b''
            except ValueError:
                return {
                    'error': '数据格式错误，请提供十六进制格式的数据',
                    'valid': False
                }
            
            # 计算哈希
            import hashlib
            if algorithm == 'sha256':
                calculated_hash = hashlib.sha256(data_bytes).hexdigest()
            elif algorithm == 'md5':
                calculated_hash = hashlib.md5(data_bytes).hexdigest()
            else:
                return {
                    'error': f'不支持的哈希算法: {algorithm}',
                    'valid': False
                }
            
            # 验证
            is_valid = calculated_hash.lower() == expected_hash.lower()
            
            return {
                'valid': is_valid,
                'algorithm': algorithm,
                'calculated_hash': calculated_hash,
                'expected_hash': expected_hash,
                'data_size': len(data_bytes)
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'valid': False
            }