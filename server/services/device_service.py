#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from server.core.serial_manager import serial_manager

class DeviceService:
    """设备服务"""
    
    def __init__(self):
        self.serial_manager = serial_manager
    
    def get_available_ports(self):
        """获取可用串口列表"""
        return self.serial_manager.get_available_ports()
    
    def get_device_list(self):
        """获取设备列表"""
        devices = []
        for port, device in self.serial_manager.devices.items():
            # 处理端口路径中的特殊字符
            port_safe = port.replace('/', '_').replace('\\', '_')
            device_info = {
                'id': f"device_{port_safe}",
                'port': port,
                'baudrate': device.baudrate,
                'connected': device.is_connected,
                'type': 'serial',
                'name': f"STM32 ({port})"
            }
            devices.append(device_info)
        
        return devices
    
    def connect_device(self, port, baudrate=115200):
        """连接设备"""
        try:
            # 创建或获取设备
            device = self.serial_manager.create_device(port, baudrate)
            
            # 连接设备
            if device.connect():
                # 处理端口路径中的特殊字符
                port_safe = port.replace('/', '_').replace('\\', '_')
                return {
                    'success': True,
                    'data': {
                        'device_id': f"device_{port_safe}",
                        'port': port,
                        'baudrate': baudrate,
                        'connected': True
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f'设备 {port} 连接失败'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def disconnect_device(self, port):
        """断开设备"""
        try:
            device = self.serial_manager.get_device(port)
            if device:
                device.disconnect()
                return {
                    'success': True,
                    'message': f'设备 {port} 已断开'
                }
            else:
                return {
                    'success': False,
                    'error': f'设备 {port} 不存在'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_device_status(self, device_id):
        """获取设备状态"""
        try:
            port = self._extract_port_from_device_id(device_id)
            device = self.serial_manager.get_device(port)
            
            if not device:
                return {
                    'success': False,
                    'error': '设备不存在'
                }
            
            return {
                'success': True,
                'data': {
                    'device_id': device_id,
                    'port': port,
                    'connected': device.is_connected,
                    'baudrate': device.baudrate
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_command(self, device_id, command):
        """发送设备命令"""
        try:
            port = self._extract_port_from_device_id(device_id)
            device = self.serial_manager.get_device(port)
            
            if not device:
                return {
                    'success': False,
                    'error': '设备不存在'
                }
            
            if not device.is_connected:
                return {
                    'success': False,
                    'error': '设备未连接'
                }
            
            # 发送命令
            if device.send_command(command):
                # 等待响应
                time.sleep(0.5)
                messages = device.get_messages()
                
                return {
                    'success': True,
                    'data': {
                        'command': command,
                        'response': messages
                    }
                }
            else:
                return {
                    'success': False,
                    'error': '命令发送失败'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_device_messages(self, device_id):
        """获取设备消息"""
        try:
            port = self._extract_port_from_device_id(device_id)
            device = self.serial_manager.get_device(port)
            
            if not device:
                return {
                    'success': False,
                    'error': '设备不存在'
                }
            
            messages = device.get_messages()
            
            return {
                'success': True,
                'data': messages
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_device_info(self, device_id):
        """获取设备信息"""
        try:
            port = self._extract_port_from_device_id(device_id)
            device = self.serial_manager.get_device(port)
            
            if not device:
                return {
                    'success': False,
                    'error': '设备不存在'
                }
            
            if not device.is_connected:
                return {
                    'success': False,
                    'error': '设备未连接'
                }
            
            # 发送信息查询命令
            device.send_command('i')
            time.sleep(1)  # 等待响应
            
            messages = device.get_messages()
            
            # 解析设备信息
            device_info = {
                'mcu': 'STM32F103ZET6',
                'bootloader_version': '2.0',
                'flash_size': '512KB',
                'bootloader_size': '64KB',
                'app_size': '448KB',
                'status': 'bootloader' if any('bootloader' in msg.lower() for msg in messages) else 'unknown',
                'raw_response': messages
            }
            
            return {
                'success': True,
                'data': device_info
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def execute_bootloader_command(self, device_id, command):
        """执行bootloader命令"""
        try:
            port = self._extract_port_from_device_id(device_id)
            device = self.serial_manager.get_device(port)
            
            if not device:
                return {
                    'success': False,
                    'error': '设备不存在'
                }
            
            if not device.is_connected:
                return {
                    'success': False,
                    'error': '设备未连接'
                }
            
            # 命令映射
            command_map = {
                'help': 'h',
                'info': 'i',
                'erase': 'e',
                'reset': 'r',
                'jump': 'j',
                'update': 'u',
                'wifi': 'w',
                'backup': 'xb',
                'restore': 'xr'
            }
            
            actual_command = command_map.get(command, command)
            
            if device.send_command(actual_command):
                time.sleep(0.5)
                messages = device.get_messages()
                
                return {
                    'success': True,
                    'data': {
                        'command': command,
                        'actual_command': actual_command,
                        'response': messages
                    }
                }
            else:
                return {
                    'success': False,
                    'error': '命令发送失败'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_port_from_device_id(self, device_id):
        """从device_id提取端口"""
        # 移除前缀
        port_safe = device_id.replace('device_', '')
        
        # 根据操作系统类型恢复路径分隔符
        # 在Linux/Mac上使用 '/', 在Windows上使用 '\\'
        import os
        if os.name == 'nt':  # Windows
            # 如果包含多个下划线，可能是Windows路径
            if '_' in port_safe and '\\' not in port_safe:
                port = port_safe.replace('_', '\\', 1)  # 只替换第一个下划线
            else:
                port = port_safe.replace('_', '\\')
        else:  # Linux/Mac
            port = port_safe.replace('_', '/')
        
        return port