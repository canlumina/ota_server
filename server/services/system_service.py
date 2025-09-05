#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import platform
import psutil
from datetime import datetime
from pathlib import Path

from server.core.serial_manager import serial_manager

class SystemService:
    """系统服务"""
    
    def __init__(self):
        self.serial_manager = serial_manager
    
    def get_system_info(self):
        """获取系统信息"""
        # 系统基本信息
        system_info = {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'hostname': platform.node()
        }
        
        # 系统资源信息
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        resource_info = {
            'cpu_count': psutil.cpu_count(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_total': memory.total,
            'memory_available': memory.available,
            'memory_percent': memory.percent,
            'disk_total': disk.total,
            'disk_used': disk.used,
            'disk_free': disk.free,
            'disk_percent': disk.percent
        }
        
        # 应用信息
        app_info = {
            'name': 'STM32 OTA Server',
            'version': '2.0.0',
            'start_time': datetime.now().isoformat(),
            'python_executable': sys.executable
        }
        
        return {
            'system': system_info,
            'resources': resource_info,
            'application': app_info
        }
    
    def get_health_status(self):
        """获取系统健康状态"""
        # 检查各个组件状态
        serial_status = {
            'total_devices': len(self.serial_manager.devices),
            'connected_devices': len(self.serial_manager.get_connected_devices()),
            'available_ports': len(self.serial_manager.get_available_ports())
        }
        
        # 系统资源检查
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        warnings = []
        if memory.percent > 90:
            warnings.append('内存使用率过高')
        if disk.percent > 90:
            warnings.append('磁盘空间不足')
        
        # 健康评分
        health_score = 100
        if memory.percent > 80:
            health_score -= 20
        if disk.percent > 80:
            health_score -= 20
        if len(warnings) > 0:
            health_score -= 10 * len(warnings)
        
        health_score = max(0, health_score)
        
        # 状态判定
        if health_score >= 80:
            status = 'healthy'
        elif health_score >= 60:
            status = 'warning'
        else:
            status = 'critical'
        
        return {
            'status': status,
            'score': health_score,
            'warnings': warnings,
            'serial': serial_status,
            'resources': {
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'cpu_percent': psutil.cpu_percent()
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def get_system_stats(self):
        """获取系统统计信息"""
        # 进程信息
        process = psutil.Process()
        process_info = {
            'pid': process.pid,
            'memory_info': process.memory_info()._asdict(),
            'cpu_percent': process.cpu_percent(),
            'create_time': datetime.fromtimestamp(process.create_time()).isoformat(),
            'num_threads': process.num_threads()
        }
        
        # 网络信息
        network_info = {}
        try:
            network_stats = psutil.net_io_counters()
            if network_stats:
                network_info = {
                    'bytes_sent': network_stats.bytes_sent,
                    'bytes_recv': network_stats.bytes_recv,
                    'packets_sent': network_stats.packets_sent,
                    'packets_recv': network_stats.packets_recv
                }
        except:
            pass
        
        # 启动时间
        boot_time = datetime.fromtimestamp(psutil.boot_time()).isoformat()
        
        # 固件统计信息
        firmware_stats = self._get_firmware_stats()
        
        return {
            'process': process_info,
            'network': network_info,
            'boot_time': boot_time,
            'uptime_seconds': psutil.time.time() - psutil.boot_time(),
            'firmwares': firmware_stats
        }
    
    def _get_firmware_stats(self):
        """获取固件统计信息"""
        try:
            # 直接使用FirmwareManager，避免内部API调用的循环依赖
            from server.core.firmware_manager import FirmwareManager
            from server.config.settings import get_config
            
            config = get_config()
            firmware_manager = FirmwareManager(config.FIRMWARE_FOLDER)
            
            # 获取所有固件列表
            firmwares = firmware_manager.list_firmwares()
            
            total_count = len(firmwares)
            encrypted_count = len([fw for fw in firmwares if fw.is_encrypted])
            total_size = sum(fw.size for fw in firmwares)
            
            return {
                'total': total_count,
                'encrypted': encrypted_count,
                'total_size': total_size
            }
            
        except Exception as e:
            # 如果获取固件统计失败，返回默认值
            return {
                'total': 0,
                'encrypted': 0,
                'total_size': 0
            }
    
    def get_recent_logs(self, limit=50):
        """获取最近的系统日志"""
        # 这里可以读取实际的日志文件
        # 目前返回模拟数据
        logs = []
        
        # 模拟一些日志条目
        log_levels = ['INFO', 'WARNING', 'ERROR', 'DEBUG']
        modules = ['firmware', 'device', 'crypto', 'system']
        
        import random
        for i in range(min(limit, 20)):
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'level': random.choice(log_levels),
                'module': random.choice(modules),
                'message': f'示例日志消息 {i+1}',
                'id': i + 1
            }
            logs.append(log_entry)
        
        return logs