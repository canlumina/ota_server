#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Blueprint

def create_api_v1():
    """创建并配置API v1蓝图"""
    # 创建API v1 蓝图
    api_v1 = Blueprint('api_v1', __name__)
    
    # 导入各个模块
    from . import base, firmware, device, crypto, system
    
    # 注册子蓝图
    api_v1.register_blueprint(base.bp)  # 基础路由，无前缀
    api_v1.register_blueprint(firmware.bp, url_prefix='/firmwares')
    api_v1.register_blueprint(device.bp, url_prefix='/devices')
    api_v1.register_blueprint(crypto.bp, url_prefix='/crypto')
    api_v1.register_blueprint(system.bp, url_prefix='/system')
    
    return api_v1

def register_api_v1(app):
    """注册API v1路由到应用"""
    api_v1 = create_api_v1()
    app.register_blueprint(api_v1, url_prefix='/api/v1')