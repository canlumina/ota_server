// OpenLoad 固件管理器 JavaScript
// 专注于固件管理和加密配置，不涉及串口功能

// API配置 - 自动检测访问地址
const getApiBase = () => {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return 'http://localhost:5000/api/v1';
    } else {
        // 如果是通过IP访问，使用相同的IP但端口改为5000
        return `http://${hostname}:5000/api/v1`;
    }
};

const API_BASE = getApiBase();

// 调试信息 - 显示当前使用的API地址
console.log('前端页面地址:', window.location.href);
console.log('后端API地址:', API_BASE);

// 全局变量
let firmwareList = [];
let selectedFirmware = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeYearSelect();
    initializeEventHandlers();
    loadFirmwareList();
    loadSystemStats();
    
    // 定期更新系统统计信息
    setInterval(loadSystemStats, 30000); // 每30秒更新一次
});

// 初始化年份选择器
function initializeYearSelect() {
    const yearSelect = document.getElementById('version-build');
    if (!yearSelect) return;
    
    const currentYear = new Date().getFullYear();
    const startYear = currentYear;
    const endYear = currentYear + 10; // 未来10年
    
    // 清空现有选项
    yearSelect.innerHTML = '';
    
    // 添加年份选项（从当前年份开始）
    for (let year = startYear; year <= endYear; year++) {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        if (year === currentYear) {
            option.selected = true; // 默认选择当前年份
        }
        yearSelect.appendChild(option);
    }
}

// 初始化事件处理器
function initializeEventHandlers() {
    // 上传表单事件
    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleFirmwareUpload);
    }
    
    
    // 上传表单中的加密类型变化事件
    const uploadEncryptionRadios = document.querySelectorAll('input[name="upload-encryption-type"]');
    uploadEncryptionRadios.forEach(radio => {
        radio.addEventListener('change', handleUploadEncryptionTypeChange);
    });
    
    // 上传表单中的密钥方式变化事件
    const uploadKeyMethodRadios = document.querySelectorAll('input[name="upload-key-method"]');
    uploadKeyMethodRadios.forEach(radio => {
        radio.addEventListener('change', handleUploadKeyMethodChange);
    });
    
    // 文件选择事件
    const fileInput = document.getElementById('firmware-file');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelect);
    }
    
    // 版本号输入框事件绑定
    const versionInputs = ['version-major', 'version-minor', 'version-patch', 'version-build'];
    versionInputs.forEach(inputId => {
        const input = document.getElementById(inputId);
        if (input) {
            input.addEventListener('input', updateVersionPreview);
            input.addEventListener('blur', updateVersionPreview);
        }
    });
    
    // 初始化版本预览
    updateVersionPreview();
}

// 处理文件选择
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        if (!file.name.toLowerCase().endsWith('.bin')) {
            showToast('请选择.bin格式的固件文件', 'warning');
            event.target.value = '';
            return;
        }
        
        // 尝试从文件名提取版本号
        const versionMatch = file.name.match(/v?(\d+\.\d+\.\d+|\d+\.\d+|\d+)/i);
        if (versionMatch && !document.getElementById('firmware-version').value) {
            document.getElementById('firmware-version').value = versionMatch[1];
        }
        
        showToast(`已选择文件: ${file.name} (${formatFileSize(file.size)})`, 'info');
    }
}

// 处理上传表单中的加密类型变化
function handleUploadEncryptionTypeChange() {
    const selectedType = document.querySelector('input[name="upload-encryption-type"]:checked').value;
    const keySection = document.getElementById('upload-encryption-key-section');
    const passwordSection = document.getElementById('upload-password-section');
    const manualKeySection = document.getElementById('upload-manual-key-section');
    
    if (selectedType === 'none') {
        keySection.style.display = 'none';
        passwordSection.style.display = 'none';
        manualKeySection.style.display = 'none';
    } else {
        keySection.style.display = 'block';
        // 默认选择密码方式
        document.getElementById('upload-key-password').checked = true;
        passwordSection.style.display = 'block';
        manualKeySection.style.display = 'none';
    }
}

// 处理上传表单中的密钥方式变化
function handleUploadKeyMethodChange() {
    const selectedMethod = document.querySelector('input[name="upload-key-method"]:checked').value;
    const passwordSection = document.getElementById('upload-password-section');
    const manualKeySection = document.getElementById('upload-manual-key-section');
    
    if (selectedMethod === 'password') {
        passwordSection.style.display = 'block';
        manualKeySection.style.display = 'none';
    } else {
        passwordSection.style.display = 'none';
        manualKeySection.style.display = 'block';
    }
}

// 生成上传表单的随机密钥
async function generateUploadRandomKey() {
    const encryptionTypeElement = document.querySelector('input[name="upload-encryption-type"]:checked');
    
    if (!encryptionTypeElement) {
        showToast('请先选择加密算法', 'warning');
        return;
    }
    
    const encryptionType = encryptionTypeElement.value;
    
    if (encryptionType === 'none') {
        showToast('请先选择加密算法', 'warning');
        return;
    }
    
    try {
        console.log('正在生成密钥，算法:', encryptionType);
        showToast('正在生成密钥...', 'info');
        
        const response = await fetch(`${API_BASE}/crypto/key/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                algorithm: encryptionType
            })
        });
        
        console.log('API响应状态:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log('API响应结果:', result);
        
        if (result.success) {
            const keyInput = document.getElementById('upload-encryption-key');
            if (keyInput) {
                keyInput.value = result.data.key;
                showToast(`已生成随机密钥 (${result.data.key_length}字节)`, 'success');
            } else {
                showToast('未找到密钥输入框', 'error');
            }
        } else {
            showToast(`生成密钥失败: ${result.error}`, 'error');
        }
        
    } catch (error) {
        console.error('生成密钥出错:', error);
        showToast(`生成密钥失败: ${error.message}`, 'error');
    }
}

// 生成上传表单的随机密码
function generateUploadRandomPassword() {
    // 生成强随机密码：包含大小写字母、数字、特殊字符，长度16位
    const upperCase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    const lowerCase = 'abcdefghijklmnopqrstuvwxyz';
    const numbers = '0123456789';
    const symbols = '!@#$%^&*()_+-=[]{}|;:,.<>?';
    
    const allChars = upperCase + lowerCase + numbers + symbols;
    let password = '';
    
    // 确保至少包含每种类型的字符
    password += upperCase.charAt(Math.floor(Math.random() * upperCase.length));
    password += lowerCase.charAt(Math.floor(Math.random() * lowerCase.length));
    password += numbers.charAt(Math.floor(Math.random() * numbers.length));
    password += symbols.charAt(Math.floor(Math.random() * symbols.length));
    
    // 生成剩余的12个字符
    for (let i = 4; i < 16; i++) {
        password += allChars.charAt(Math.floor(Math.random() * allChars.length));
    }
    
    // 打乱密码字符顺序
    password = password.split('').sort(() => 0.5 - Math.random()).join('');
    
    document.getElementById('upload-encryption-password').value = password;
    showToast('已生成强随机密码（长度16位，包含大小写字母、数字和特殊字符）', 'success');
}

// 处理固件上传
async function handleFirmwareUpload(event) {
    event.preventDefault();
    
    console.log('开始处理固件上传...');
    
    const fileInput = document.getElementById('firmware-file');
    const versionInput = document.getElementById('firmware-version');
    const targetDeviceSelect = document.getElementById('target-device');
    
    if (!fileInput.files[0]) {
        showToast('请选择固件文件', 'warning');
        return;
    }
    
    // 验证版本号输入（允许使用默认值）
    if (!validateVersionInputs()) {
        // 如果验证失败，尝试使用默认值
        const majorInput = document.getElementById('version-major');
        const minorInput = document.getElementById('version-minor');
        const patchInput = document.getElementById('version-patch');
        const buildInput = document.getElementById('version-build');
        
        if (!majorInput.value) majorInput.value = '1';
        if (!minorInput.value) minorInput.value = '0';
        if (!patchInput.value) patchInput.value = '0';
        if (!buildInput.value) buildInput.value = '2025';
        
        updateVersionPreview();
        
        // 再次验证，如果还是失败就提示
        if (!validateVersionInputs()) {
            showToast('请填写完整的版本号信息', 'warning');
            return;
        }
        
        showToast('已使用默认版本号 v1.0.0.2025', 'info');
    }
    
    // 收集加密参数
    const encryptionTypeElement = document.querySelector('input[name="upload-encryption-type"]:checked');
    if (!encryptionTypeElement) {
        showToast('请选择加密类型', 'warning');
        console.error('未找到选中的加密类型');
        return;
    }
    const encryptionType = encryptionTypeElement.value;
    console.log('选择的加密类型:', encryptionType);
    
    // 验证加密参数
    if (encryptionType !== 'none') {
        const keyMethod = document.querySelector('input[name="upload-key-method"]:checked').value;
        
        if (keyMethod === 'password') {
            const password = document.getElementById('upload-encryption-password').value;
            if (!password) {
                showToast('请输入加密密码', 'warning');
                return;
            }
        } else if (keyMethod === 'manual') {
            const manualKey = document.getElementById('upload-encryption-key').value;
            if (!manualKey) {
                showToast('请输入加密密钥', 'warning');
                return;
            }
        }
    }
    
    const formData = new FormData();
    formData.append('firmware', fileInput.files[0]);
    formData.append('version', versionInput.value || 'auto');
    formData.append('target_device', targetDeviceSelect.value);
    
    // 添加加密参数
    formData.append('encryption_type', encryptionType);
    
    if (encryptionType !== 'none') {
        const keyMethod = document.querySelector('input[name="upload-key-method"]:checked').value;
        formData.append('key_method', keyMethod);
        
        if (keyMethod === 'password') {
            formData.append('password', document.getElementById('upload-encryption-password').value);
        } else if (keyMethod === 'manual') {
            formData.append('encryption_key', document.getElementById('upload-encryption-key').value);
        }
    }
    
    // 显示上传进度
    showUploadProgress(true);
    updateUploadProgress(0, '准备上传...');
    
    try {
        console.log('发送上传请求到:', `${API_BASE}/firmwares`);
        console.log('FormData内容:', Array.from(formData.entries()));
        
        const response = await fetch(`${API_BASE}/firmwares`, {
            method: 'POST',
            body: formData
        });
        
        console.log('服务器响应状态:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log('服务器响应结果:', result);
        
        if (result.success) {
            showToast('固件上传成功！', 'success');
            
            // 重置表单
            document.getElementById('upload-form').reset();
            
            // 重置版本输入框
            resetVersionInputs();
            
            // 刷新固件列表和系统状态
            await loadFirmwareList();
            await loadSystemStats();
            
            // 自动选择刚上传的固件
            const firmwareSelect = document.getElementById('selected-firmware');
            if (firmwareSelect) {
                const newOption = Array.from(firmwareSelect.options).find(
                    option => option.textContent.includes(result.data.original_filename)
                );
                if (newOption) {
                    newOption.selected = true;
                }
            }
            
        } else {
            showToast(`上传失败: ${result.error}`, 'error');
        }
        
    } catch (error) {
        console.error('上传出错:', error);
        showToast(`上传失败: ${error.message}`, 'error');
    } finally {
        console.log('上传过程结束');
        showUploadProgress(false);
    }
}



// 加载固件列表
async function loadFirmwareList() {
    try {
        const response = await fetch(`${API_BASE}/firmwares`);
        const result = await response.json();
        
        if (result.success) {
            firmwareList = result.data.firmwares;
            updateFirmwareTable();
        } else {
            console.error('加载固件列表失败:', result.error);
            showToast(`加载固件列表失败: ${result.error}`, 'error');
        }
        
    } catch (error) {
        console.error('加载固件列表异常:', error);
        showToast(`加载固件列表失败: ${error.message}`, 'error');
    }
}

// 更新固件表格
function updateFirmwareTable() {
    const tbody = document.getElementById('firmware-list');
    
    if (!tbody) {
        console.error('未找到firmware-list元素');
        return;
    }
    
    if (firmwareList.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center text-muted py-4">
                    <i class="bi bi-inbox"></i><br>
                    暂无固件文件<br>
                    <small>请上传.bin格式的固件文件</small>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = firmwareList.map(firmware => {
        
        const encryptionBadge = firmware.is_encrypted 
            ? `<span class="badge bg-warning">${firmware.encryption_algorithm.toUpperCase()}</span>`
            : `<span class="badge bg-secondary">无</span>`;
        
        // 版本号显示，最新版本用特殊样式
        const versionBadge = firmware.is_latest
            ? `<span class="badge bg-success position-relative">
                 <i class="bi bi-star-fill"></i> ${formatVersion(firmware.version)}
                 <span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">
                   最新
                 </span>
               </span>`
            : `<span class="badge bg-info">${formatVersion(firmware.version)}</span>`;
        
        // 行样式，最新版本高亮
        const rowClass = firmware.is_latest ? 'table-success' : '';
            
        return `
            <tr class="${rowClass}">
                <td>
                    <div class="fw-bold d-flex align-items-center">
                        ${firmware.is_latest ? '<i class="bi bi-star-fill text-warning me-2" title="最新版本"></i>' : ''}
                        ${firmware.original_filename}
                    </div>
                    <small class="text-muted">ID: ${firmware.id}</small>
                </td>
                <td>${versionBadge}</td>
                <td>
                    <span class="fw-bold">${formatFileSize(firmware.size)}</span>
                </td>
                <td>${encryptionBadge}</td>
                <td>
                    <div class="btn-group-vertical btn-group-sm">
                        <button class="btn btn-outline-info btn-sm" 
                                onclick="showFirmwareDetails('${firmware.id}')" title="查看详情">
                            <i class="bi bi-info-circle"></i>
                        </button>
                        <button class="btn btn-outline-success btn-sm" 
                                onclick="downloadFirmware('${firmware.id}')" title="下载">
                            <i class="bi bi-download"></i>
                        </button>
                        <button class="btn btn-outline-danger btn-sm" 
                                onclick="deleteFirmware('${firmware.id}')" title="删除">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

// 显示固件详情
async function showFirmwareDetails(firmwareId) {
    try {
        const response = await fetch(`${API_BASE}/firmwares/${firmwareId}`);
        const result = await response.json();
        
        if (result.success) {
            const firmware = result.data;
            const detailsCard = document.getElementById('firmware-details');
            const detailsContent = document.getElementById('firmware-details-content');
            
            const versionInfo = parseVersionMeaning(firmware.version);
            const isLatest = firmware.is_latest;
            
            detailsContent.innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <h6 class="text-primary"><i class="bi bi-info-circle"></i> 基本信息</h6>
                        <table class="table table-sm table-borderless">
                            <tr><td class="fw-bold">文件名:</td><td>${firmware.original_filename}</td></tr>
                            <tr>
                                <td class="fw-bold">版本:</td>
                                <td>
                                    <span class="badge ${isLatest ? 'bg-success' : 'bg-info'} me-2">
                                        ${isLatest ? '<i class="bi bi-star-fill"></i> ' : ''}${formatVersion(firmware.version)}
                                    </span>
                                    ${isLatest ? '<span class="badge bg-warning">最新</span>' : ''}
                                </td>
                            </tr>
                            <tr><td class="fw-bold">大小:</td><td><span class="badge bg-secondary">${formatFileSize(firmware.size)}</span></td></tr>
                            <tr><td class="fw-bold">目标设备:</td><td><span class="badge bg-dark">${firmware.target_device}</span></td></tr>
                            <tr><td class="fw-bold">上传时间:</td><td>${formatDateTime(firmware.upload_time)}</td></tr>
                        </table>
                        
                        <h6 class="text-success mt-3"><i class="bi bi-tag"></i> 版本详情</h6>
                        <div class="bg-light p-3 rounded">
                            <div class="small">
                                <div><strong>格式:</strong> v<span class="text-primary">Major</span>.<span class="text-info">Minor</span>.<span class="text-warning">Patch</span>.<span class="text-danger">Build</span></div>
                                <div class="mt-2">${versionInfo.display}</div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <h6 class="text-warning"><i class="bi bi-shield-lock"></i> 安全信息</h6>
                        <table class="table table-sm table-borderless">
                            <tr>
                                <td class="fw-bold">加密状态:</td>
                                <td>
                                    <span class="badge ${firmware.is_encrypted ? 'bg-warning' : 'bg-secondary'}">
                                        <i class="bi ${firmware.is_encrypted ? 'bi-shield-lock' : 'bi-shield'}"></i>
                                        ${firmware.is_encrypted ? '已加密' : '未加密'}
                                    </span>
                                </td>
                            </tr>
                            <tr><td class="fw-bold">加密算法:</td><td><span class="badge bg-info">${firmware.encryption_algorithm.toUpperCase()}</span></td></tr>
                            <tr><td class="fw-bold">校验和:</td><td><code class="small">${firmware.checksum}</code></td></tr>
                        </table>
                        
                        ${firmware.is_encrypted && firmware.encryption_metadata.iv ? 
                            `<h6 class="text-danger mt-3"><i class="bi bi-key"></i> 加密参数</h6>
                            <div class="bg-light p-3 rounded">
                                <div class="small">
                                    <strong>IV:</strong><br>
                                    <code class="user-select-all">${firmware.encryption_metadata.iv}</code>
                                </div>
                            </div>` : ''
                        }
                        
                        <div class="mt-3">
                            <div class="d-grid gap-2">
                                <button class="btn btn-outline-primary btn-sm" onclick="downloadFirmware('${firmware.id}')">
                                    <i class="bi bi-download"></i> 下载固件
                                </button>
                                ${!firmware.is_encrypted ? 
                                    `<button class="btn btn-outline-warning btn-sm" onclick="encryptSelectedFirmware('${firmware.id}')">
                                        <i class="bi bi-shield-lock"></i> 加密此固件
                                    </button>` : ''
                                }
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            detailsCard.style.display = 'block';
        } else {
            showToast(`获取固件详情失败: ${result.error}`, 'error');
        }
        
    } catch (error) {
        showToast(`获取固件详情失败: ${error.message}`, 'error');
    }
}

// 下载固件
function downloadFirmware(firmwareId) {
    const firmware = firmwareList.find(f => f.id === firmwareId);
    if (!firmware) return;
    
    const link = document.createElement('a');
    link.href = `${API_BASE}/firmwares/${firmwareId}/download`;
    link.download = firmware.original_filename;
    link.click();
    
    showToast('开始下载固件', 'info');
}

// 删除固件
function deleteFirmware(firmwareId) {
    const firmware = firmwareList.find(f => f.id === firmwareId);
    if (!firmware) return;
    
    showConfirmDialog(
        '删除固件',
        `确定要删除固件 "${firmware.original_filename}" 吗？此操作无法撤销。`,
        async () => {
            try {
                const response = await fetch(`${API_BASE}/firmwares/${firmwareId}`, {
                    method: 'DELETE'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showToast('固件删除成功', 'success');
                    await loadFirmwareList();
                    await loadSystemStats();
                    
                    // 如果删除的固件正在被选择，清除选择
                    const select = document.getElementById('selected-firmware');
                    if (select && select.value === firmwareId) {
                        select.value = '';
                    }
                } else {
                    showToast(`删除失败: ${result.error}`, 'error');
                }
                
            } catch (error) {
                showToast(`删除失败: ${error.message}`, 'error');
            }
        }
    );
}

// 刷新固件列表
async function refreshFirmwareList() {
    showToast('正在刷新固件列表...', 'info');
    await loadFirmwareList();
    await loadSystemStats();
    showToast('固件列表已更新', 'success');
}

// 显示存储信息
async function showStorageInfo() {
    try {
        const response = await fetch(`${API_BASE}/firmwares/storage`);
        const result = await response.json();
        
        if (result.success) {
            const storage = result.data;
            showConfirmDialog(
                '存储信息',
                `
                <div class="text-start">
                    <p><strong>固件存储统计：</strong></p>
                    <ul>
                        <li>固件数量: ${storage.firmware_count}</li>
                        <li>占用空间: ${formatFileSize(storage.total_firmware_size)}</li>
                        <li>存储目录: ${storage.upload_directory}</li>
                    </ul>
                    ${storage.disk_total_space ? `
                    <p><strong>磁盘使用情况：</strong></p>
                    <ul>
                        <li>总空间: ${formatFileSize(storage.disk_total_space)}</li>
                        <li>可用空间: ${formatFileSize(storage.disk_free_space)}</li>
                        <li>使用率: ${storage.disk_usage_percent.toFixed(1)}%</li>
                    </ul>
                    ` : ''}
                </div>
                `,
                null,
                '关闭'
            );
        } else {
            showToast(`获取存储信息失败: ${result.error}`, 'error');
        }
        
    } catch (error) {
        showToast(`获取存储信息失败: ${error.message}`, 'error');
    }
}

// 加载系统统计信息
async function loadSystemStats() {
    try {
        const response = await fetch(`${API_BASE}/system/stats`);
        const result = await response.json();
        
        if (result.success) {
            const stats = result.data;
            
            // 更新统计显示
            document.getElementById('firmware-count').textContent = stats.firmwares.total;
            document.getElementById('encrypted-count').textContent = stats.firmwares.encrypted;
            document.getElementById('storage-used').textContent = formatFileSize(stats.firmwares.total_size);
        }
        
    } catch (error) {
        console.warn('加载系统统计失败:', error);
    }
}

// 显示上传进度
function showUploadProgress(show) {
    const progressDiv = document.getElementById('upload-progress');
    if (progressDiv) {
        progressDiv.style.display = show ? 'block' : 'none';
    }
}

// 更新上传进度
function updateUploadProgress(percent, message) {
    const progressBar = document.getElementById('upload-progress-bar');
    const messageElement = document.getElementById('upload-message');
    
    if (progressBar) {
        progressBar.style.width = percent + '%';
        progressBar.setAttribute('aria-valuenow', percent);
    }
    
    if (messageElement) {
        messageElement.textContent = message;
    }
}

// 显示确认对话框 
function showConfirmDialog(title, body, onConfirm, confirmButtonText = '确定') {
    // 对于删除操作，使用美观的自定义对话框
    if (title === '删除固件') {
        showDeleteConfirmDialog(body, onConfirm);
        return;
    }
    
    // 对于其他操作，使用简单的Toast提示
    showToast(body, 'info');
    if (onConfirm) {
        setTimeout(onConfirm, 1000);
    }
}

// 显示删除确认对话框
function showDeleteConfirmDialog(message, onConfirm) {
    const dialog = document.getElementById('deleteConfirmDialog');
    const backdrop = document.getElementById('deleteBackdrop');
    const messageEl = document.getElementById('deleteMessage');
    const confirmBtn = document.getElementById('deleteConfirmBtn');
    const cancelBtn = document.getElementById('deleteCancelBtn');
    
    // 设置消息
    messageEl.innerHTML = message;
    
    // 显示对话框
    backdrop.style.display = 'block';
    dialog.style.display = 'block';
    
    // 添加动画效果
    setTimeout(() => {
        backdrop.style.opacity = '1';
        dialog.style.transform = 'translate(-50%, -50%) scale(1)';
        dialog.style.opacity = '1';
    }, 10);
    
    // 关闭对话框函数
    const closeDialog = () => {
        dialog.style.transform = 'translate(-50%, -50%) scale(0.9)';
        dialog.style.opacity = '0';
        backdrop.style.opacity = '0';
        
        setTimeout(() => {
            dialog.style.display = 'none';
            backdrop.style.display = 'none';
        }, 200);
    };
    
    // 事件处理
    const handleConfirm = () => {
        closeDialog();
        if (onConfirm) onConfirm();
    };
    
    const handleCancel = () => {
        closeDialog();
    };
    
    // 移除之前的事件监听器
    const newConfirmBtn = confirmBtn.cloneNode(true);
    const newCancelBtn = cancelBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
    cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);
    
    // 添加新的事件监听器
    newConfirmBtn.addEventListener('click', handleConfirm);
    newCancelBtn.addEventListener('click', handleCancel);
    backdrop.addEventListener('click', handleCancel);
    
    // ESC键关闭
    const handleKeydown = (e) => {
        if (e.key === 'Escape') {
            handleCancel();
            document.removeEventListener('keydown', handleKeydown);
        }
    };
    document.addEventListener('keydown', handleKeydown);
}

// 显示Toast通知
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastBody = document.getElementById('toast-body');
    
    // 设置消息内容
    toastBody.textContent = message;
    
    // 设置图标和颜色
    const toastHeader = toast.querySelector('.toast-header i');
    toastHeader.className = `bi me-2 ${getToastIcon(type)}`;
    
    // 显示Toast
    const toastInstance = new bootstrap.Toast(toast);
    toastInstance.show();
}

// 获取Toast图标
function getToastIcon(type) {
    switch (type) {
        case 'success': return 'bi-check-circle text-success';
        case 'error': return 'bi-exclamation-triangle text-danger';
        case 'warning': return 'bi-exclamation-triangle text-warning';
        default: return 'bi-info-circle text-primary';
    }
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// 格式化日期时间
function formatDateTime(isoString) {
    const date = new Date(isoString);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// 格式化版本号显示
function formatVersion(version) {
    if (!version || version === 'unknown') {
        return '未知版本';
    }
    
    // 移除可能存在的v前缀，然后重新添加
    const cleanVersion = version.replace(/^v/, '');
    
    // 解析版本号各部分
    const parts = cleanVersion.split('.');
    if (parts.length >= 4) {
        const [major, minor, patch, build] = parts;
        return `v${major}.${minor}.${patch}.${build}`;
    }
    
    // 如果不是标准4段格式，直接返回带v前缀的版本
    return `v${cleanVersion}`;
}

// 解析版本号含义
function parseVersionMeaning(version) {
    const parts = version.replace('v', '').split('.');
    if (parts.length >= 4) {
        const [major, minor, patch, build] = parts;
        return {
            major: parseInt(major),
            minor: parseInt(minor), 
            patch: parseInt(patch),
            build: build,
            display: `主版本: ${major} | 功能版本: ${minor} | 修复版本: ${patch} | 构建号: ${build}`
        };
    }
    return { display: version };
}

// 快速加密选中的固件
function encryptSelectedFirmware(firmwareId) {
    // 自动选择固件
    const firmwareSelect = document.getElementById('selected-firmware');
    if (firmwareSelect) {
        firmwareSelect.value = firmwareId;
    }
    
    // 选择AES-128加密
    const aes128Radio = document.getElementById('aes128-encryption');
    if (aes128Radio) {
        aes128Radio.checked = true;
        handleEncryptionTypeChange({ target: aes128Radio });
    }
    
    // 滚动到加密配置区域
    document.getElementById('encryption-form').scrollIntoView({ 
        behavior: 'smooth',
        block: 'center'
    });
    
    showToast('已为您选择此固件并推荐AES-128加密', 'info');
}

// 更新版本预览和隐藏字段
function updateVersionPreview() {
    const major = document.getElementById('version-major').value || '0';
    const minor = document.getElementById('version-minor').value || '0';
    const patch = document.getElementById('version-patch').value || '0';
    const build = document.getElementById('version-build').value || '0';
    
    // 更新预览显示
    document.getElementById('preview-major').textContent = major;
    document.getElementById('preview-minor').textContent = minor;
    document.getElementById('preview-patch').textContent = patch;
    document.getElementById('preview-build').textContent = build;
    
    // 更新隐藏字段用于表单提交
    const versionString = `v${major}.${minor}.${patch}.${build}`;
    document.getElementById('firmware-version').value = versionString;
    
    // 验证所有字段是否填写
    validateVersionInputs();
}

// 验证版本输入
function validateVersionInputs() {
    const inputs = ['version-major', 'version-minor', 'version-patch', 'version-build'];
    const errorElement = document.getElementById('version-error');
    
    let isValid = true;
    let emptyFields = [];
    
    inputs.forEach(inputId => {
        const input = document.getElementById(inputId);
        const value = input.value.trim();
        
        if (!value) {
            input.classList.add('is-invalid');
            isValid = false;
            const label = input.previousElementSibling.textContent;
            emptyFields.push(label);
        } else {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
        }
    });
    
    if (!isValid) {
        errorElement.textContent = `请填写：${emptyFields.join('、')}`;
        errorElement.style.display = 'block';
    } else {
        errorElement.style.display = 'none';
    }
    
    return isValid;
}

// 重置版本输入框
function resetVersionInputs() {
    // 重置数字输入框
    ['version-major', 'version-minor', 'version-patch'].forEach(inputId => {
        const input = document.getElementById(inputId);
        if (input) {
            input.value = '';
            input.classList.remove('is-valid', 'is-invalid');
        }
    });
    
    // 重置年份选择器为当前年份
    const yearSelect = document.getElementById('version-build');
    if (yearSelect) {
        const currentYear = new Date().getFullYear();
        yearSelect.value = currentYear;
        yearSelect.classList.remove('is-valid', 'is-invalid');
    }
    
    // 重置预览
    updateVersionPreview();
    
    // 隐藏错误信息
    const errorElement = document.getElementById('version-error');
    if (errorElement) {
        errorElement.style.display = 'none';
    }
}

// 自动格式化版本号输入
function formatVersionInput() {
    const versionInput = document.getElementById('firmware-version');
    if (!versionInput) return;
    
    let value = versionInput.value.trim();
    
    // 如果用户只输入了数字和点，自动添加v前缀
    if (value && !value.startsWith('v') && /^[\d.]+$/.test(value)) {
        // 检查是否是完整的4段格式
        const parts = value.split('.');
        if (parts.length === 4 && parts.every(part => /^\d+$/.test(part))) {
            versionInput.value = 'v' + value;
            validateVersionFormat();
        }
    }
}