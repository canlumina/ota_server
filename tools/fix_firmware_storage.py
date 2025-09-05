#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
固件存储修复脚本
修复Linux环境下的固件显示问题
"""

import os
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime

def calculate_checksum(file_path):
    """计算文件校验和"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def extract_version_from_filename(filename):
    """从文件名提取版本信息"""
    import re
    
    # 常见版本号模式
    version_patterns = [
        r'v?(\d+\.\d+\.\d+\.\d+)',  # v1.2.3.4
        r'v?(\d+\.\d+\.\d+)',       # v1.2.3
        r'v?(\d+\.\d+)',            # v1.2
        r'(\d+)\.(\d+)\.(\d+)\.(\d+)',  # 1.2.3.4
    ]
    
    for pattern in version_patterns:
        match = re.search(pattern, filename.lower())
        if match:
            version = match.group(1) if len(match.groups()) == 1 else '.'.join(match.groups())
            return f"v{version}" if not version.startswith('v') else version
    
    # 如果没有找到版本号，使用默认版本
    return "v1.0.0.1"

def fix_firmware_storage():
    """修复固件存储"""
    print("🔧 开始修复固件存储...")
    
    base_dir = Path(__file__).parent
    storage_dir = base_dir / 'storage'
    firmware_dir = storage_dir / 'firmware'
    
    # 1. 确保目录存在
    print("📁 检查目录结构...")
    firmware_dir.mkdir(parents=True, exist_ok=True)
    (storage_dir / 'uploads').mkdir(exist_ok=True)
    (storage_dir / 'logs').mkdir(exist_ok=True)
    
    # 2. 扫描现有固件文件
    print("🔍 扫描固件文件...")
    firmware_files = []
    for ext in ['*.bin', '*.hex', '*.elf']:
        firmware_files.extend(firmware_dir.glob(ext))
    
    print(f"   找到 {len(firmware_files)} 个固件文件")
    
    if not firmware_files:
        print("   ⚠️ 没有找到固件文件")
        return
    
    # 3. 重新生成元数据
    print("📄 重新生成元数据...")
    metadata = {}
    
    for file_path in firmware_files:
        try:
            print(f"   处理: {file_path.name}")
            
            # 获取文件信息
            stat = file_path.stat()
            size = stat.st_size
            mtime = datetime.fromtimestamp(stat.st_mtime)
            
            # 生成固件ID
            firmware_id = f"fw_{int(stat.st_mtime)}_{file_path.stem}"
            
            # 计算校验和
            checksum = calculate_checksum(file_path)
            
            # 提取版本信息
            version = extract_version_from_filename(file_path.name)
            
            # 创建固件信息
            firmware_info = {
                "id": firmware_id,
                "filename": file_path.name,
                "original_filename": file_path.name,
                "version": version,
                "size": size,
                "checksum": checksum,
                "upload_time": mtime.isoformat(),
                "target_device": "STM32F103ZET6",
                "is_encrypted": False,
                "encryption_algorithm": "none",
                "encryption_metadata": {},
                "metadata": {
                    "created_by": "fix_script",
                    "scan_time": datetime.now().isoformat()
                }
            }
            
            metadata[firmware_id] = firmware_info
            print(f"     ✅ ID: {firmware_id}, 版本: {version}, 大小: {size} bytes")
            
        except Exception as e:
            print(f"     ❌ 处理失败: {e}")
    
    # 4. 保存元数据文件
    metadata_file = firmware_dir / 'metadata.json'
    print(f"💾 保存元数据到: {metadata_file}")
    
    try:
        # 备份旧的元数据文件
        if metadata_file.exists():
            backup_file = metadata_file.with_suffix('.json.backup')
            metadata_file.rename(backup_file)
            print(f"   备份旧文件到: {backup_file}")
        
        # 写入新的元数据
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"   ✅ 成功保存 {len(metadata)} 个固件的元数据")
        
    except Exception as e:
        print(f"   ❌ 保存失败: {e}")
        return False
    
    # 5. 验证修复结果
    print("🧪 验证修复结果...")
    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            loaded_metadata = json.load(f)
        
        print(f"   ✅ 成功加载元数据，包含 {len(loaded_metadata)} 个固件")
        
        for fw_id, fw_data in loaded_metadata.items():
            filename = fw_data['filename']
            version = fw_data['version']
            size = fw_data['size']
            print(f"     - {filename} (版本: {version}, 大小: {size} bytes)")
    
    except Exception as e:
        print(f"   ❌ 验证失败: {e}")
        return False
    
    print("\n✅ 固件存储修复完成！")
    print("\n📋 后续步骤:")
    print("1. 重启后端服务")
    print("2. 刷新前端页面")
    print("3. 检查系统统计和固件列表")
    
    return True

if __name__ == "__main__":
    fix_firmware_storage()