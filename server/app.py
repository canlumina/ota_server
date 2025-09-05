#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from flask import Flask
from flask_cors import CORS

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from server.config.settings import get_config
from server.config.database import DatabaseConfig
from server.api.v1 import register_api_v1

def create_app(config_name=None):
    """应用工厂函数"""
    # 创建Flask应用实例 - 配置模板和静态文件目录
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # 加载配置
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    config_class = get_config()
    config_class.init_app(app)
    
    # 配置日志
    configure_logging(app)
    
    # 启用CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "Range"]
        }
    })
    
    # 初始化数据库
    db_config = DatabaseConfig(app.config['STORAGE_DIR'])
    db_config.init_database()
    app.db_config = db_config
    
    # 注册API路由
    register_api_v1(app)
    
    # 注册错误处理器
    register_error_handlers(app)
    
    # 注册清理函数
    register_cleanup_handlers(app)
    
    # 注册基础路由
    register_base_routes(app)
    
    return app

def configure_logging(app):
    """配置日志"""
    if app.config['DEBUG']:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                app.config['LOGS_FOLDER'] / 'app.log',
                encoding='utf-8'
            )
        ]
    )
    
    # 设置Flask日志级别
    app.logger.setLevel(log_level)

def register_error_handlers(app):
    """注册错误处理器"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return {
            'success': False,
            'error': '请求参数错误',
            'message': str(error.description)
        }, 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return {
            'success': False,
            'error': '未授权访问',
            'message': '请提供有效的认证信息'
        }, 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return {
            'success': False,
            'error': '访问被禁止',
            'message': '您没有权限访问此资源'
        }, 403
    
    @app.errorhandler(404)
    def not_found(error):
        return {
            'success': False,
            'error': '资源不存在',
            'message': '请求的资源未找到'
        }, 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return {
            'success': False,
            'error': '方法不被允许',
            'message': '请求方法不被支持'
        }, 405
    
    @app.errorhandler(413)
    def payload_too_large(error):
        return {
            'success': False,
            'error': '文件过大',
            'message': '上传的文件超过了大小限制'
        }, 413
    
    @app.errorhandler(429)
    def too_many_requests(error):
        return {
            'success': False,
            'error': '请求过于频繁',
            'message': '请稍后再试'
        }, 429
    
    @app.errorhandler(500)
    def internal_server_error(error):
        app.logger.error(f'服务器内部错误: {error}')
        return {
            'success': False,
            'error': '服务器内部错误',
            'message': '服务器遇到了一个错误，请稍后再试'
        }, 500

def register_cleanup_handlers(app):
    """注册清理处理器"""
    
    @app.teardown_appcontext
    def cleanup_request(error):
        """请求清理"""
        if error:
            app.logger.error(f'请求处理错误: {error}')
    
    # 注册应用退出时的清理函数
    import atexit
    
    def cleanup_on_exit():
        """应用退出时清理资源"""
        app.logger.info('应用正在关闭，清理资源...')
        
        # 清理串口连接
        try:
            from .core.serial_manager import serial_manager
            serial_manager.cleanup()
            app.logger.info('串口连接已清理')
        except Exception as e:
            app.logger.error(f'清理串口连接时出错: {e}')
    
    atexit.register(cleanup_on_exit)

def register_base_routes(app):
    """注册基础路由"""
    from flask import redirect, send_file, render_template
    
    @app.route('/')
    def index():
        """根路径显示后端管理界面"""
        return render_template('admin.html')
    
    @app.route('/api')
    def api_info():
        """API信息接口"""
        from flask import request
        
        # 获取当前请求的主机名
        hostname = request.host.split(':')[0]  # 移除端口号
        
        # 根据访问方式生成URLs
        if hostname in ['localhost', '127.0.0.1']:
            base_url = 'http://localhost'
        else:
            base_url = f'http://{hostname}'
        
        return {
            'message': 'STM32 OTA Server API',
            'version': '2.0.0',
            'frontend': f'{base_url}:3000',
            'api': f'{base_url}:5000/api/v1',
            'health': f'{base_url}:5000/api/v1/system/health'
        }
    
    @app.route('/favicon.ico')
    def favicon():
        """处理favicon请求"""
        return '', 204  # 返回空内容，状态码204 No Content

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    config = get_config()
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )