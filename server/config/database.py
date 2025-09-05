#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sqlite3
from pathlib import Path

class DatabaseConfig:
    """数据库配置"""
    
    def __init__(self, storage_dir):
        self.storage_dir = Path(storage_dir)
        self.db_path = self.storage_dir / 'ota_server.db'
        
    def init_database(self):
        """初始化数据库"""
        self.storage_dir.mkdir(exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建设备表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT UNIQUE NOT NULL,
                    name TEXT,
                    hardware_version TEXT,
                    firmware_version TEXT,
                    last_seen DATETIME,
                    status TEXT DEFAULT 'offline',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建固件表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS firmware (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER,
                    checksum TEXT,
                    encryption_type TEXT DEFAULT 'none',
                    target_location TEXT DEFAULT 'internal',
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建更新记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS update_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    firmware_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'pending',
                    method TEXT,
                    progress INTEGER DEFAULT 0,
                    error_message TEXT,
                    started_at DATETIME,
                    completed_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (firmware_id) REFERENCES firmware (id),
                    FOREIGN KEY (device_id) REFERENCES devices (device_id)
                )
            ''')
            
            # 创建系统日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    module TEXT,
                    device_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)