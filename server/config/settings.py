#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent.parent.parent

class BaseConfig:
    """基础配置类"""
    
    # Flask基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'openload_webmanager_2024'
    DEBUG = False
    TESTING = False
    
    # 服务器配置
    HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    PORT = int(os.environ.get('FLASK_PORT', 5000))
    
    # 存储配置
    STORAGE_DIR = BASE_DIR / 'storage'
    UPLOAD_FOLDER = STORAGE_DIR / 'uploads'
    FIRMWARE_FOLDER = STORAGE_DIR / 'firmware'
    LOGS_FOLDER = STORAGE_DIR / 'logs'
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'bin', 'hex', 'elf'}
    
    # 串口配置
    DEFAULT_BAUDRATE = 115200
    SERIAL_TIMEOUT = 1.0
    
    # Bootloader配置
    BOOTLOADER_COMMANDS = {
        'help': 'h',
        'info': 'i', 
        'update': 'u',
        'erase': 'e',
        'reset': 'r',
        'jump': 'j',
        'wifi': 'w',
        'backup': 'xb',
        'restore': 'xr'
    }
    
    # 加密选项
    ENCRYPTION_TYPES = {
        'none': '无加密',
        'xor': 'XOR加密',
        'aes': 'AES-128-CBC'
    }
    
    # 升级方式
    UPDATE_METHODS = {
        'xmodem': 'XMODEM (串口)',
        'ota': 'OTA (WiFi)'
    }
    
    # 目标位置
    TARGET_LOCATIONS = {
        'internal': '内部Flash',
        'external': '外部Flash'
    }
    
    # API配置
    API_PREFIX = '/api'
    API_VERSION = 'v1'
    
    # 安全配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1小时
    
    @classmethod
    def init_app(cls, app):
        """初始化应用配置"""
        # 确保存储目录存在
        cls.STORAGE_DIR.mkdir(exist_ok=True)
        cls.UPLOAD_FOLDER.mkdir(exist_ok=True)
        cls.FIRMWARE_FOLDER.mkdir(exist_ok=True)
        cls.LOGS_FOLDER.mkdir(exist_ok=True)
        
        # 设置Flask配置
        app.config.from_object(cls)
        
        return app

class DevelopmentConfig(BaseConfig):
    """开发环境配置"""
    DEBUG = True
    
class TestingConfig(BaseConfig):
    """测试环境配置"""
    TESTING = True
    DEBUG = True

class ProductionConfig(BaseConfig):
    """生产环境配置"""
    DEBUG = False
    
    @classmethod
    def init_app(cls, app):
        """初始化生产环境配置"""
        # 生产环境安全配置
        secret_key = os.environ.get('SECRET_KEY')
        if not secret_key:
            raise ValueError("生产环境必须设置SECRET_KEY环境变量")
        app.config['SECRET_KEY'] = secret_key
        
        super().init_app(app)

# 配置字典
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# 获取当前配置
def get_config():
    """获取当前环境配置"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])