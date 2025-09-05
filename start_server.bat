@echo off
chcp 65001 > nul
setlocal EnableDelayedExpansion

:: STM32 OTA Server 一键启动脚本 (Windows)
:: 支持后台运行，关闭命令行不会影响服务

:: 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: 目录定义
set "LOG_DIR=%SCRIPT_DIR%logs"
set "PID_DIR=%SCRIPT_DIR%pids"
set "BACKEND_PID_FILE=%PID_DIR%\backend.pid"
set "FRONTEND_PID_FILE=%PID_DIR%\frontend.pid"

:: 创建必要目录
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
if not exist "%PID_DIR%" mkdir "%PID_DIR%"
if not exist "storage\firmware" mkdir "storage\firmware"
if not exist "storage\uploads" mkdir "storage\uploads"
if not exist "storage\logs" mkdir "storage\logs"

:: 获取当前时间
for /f "tokens=1-4 delims=/ " %%i in ('date /t') do set mydate=%%i-%%j-%%k
for /f "tokens=1-2 delims=: " %%i in ('time /t') do set mytime=%%i:%%j

goto :main

:print_message
    echo [%mydate% %mytime%] %~1
    goto :eof

:print_success
    echo [92m[%mydate% %mytime%] %~1[0m
    goto :eof

:print_warning
    echo [93m[%mydate% %mytime%] %~1[0m
    goto :eof

:print_error
    echo [91m[%mydate% %mytime%] %~1[0m
    goto :eof

:check_port
    netstat -an | findstr ":%~1 " | findstr "LISTENING" > nul
    if !errorlevel! equ 0 (
        exit /b 0
    ) else (
        exit /b 1
    )

:stop_services
    call :print_message "停止服务..."
    
    :: 停止后端服务
    if exist "%BACKEND_PID_FILE%" (
        set /p BACKEND_PID=<"%BACKEND_PID_FILE%"
        taskkill /PID !BACKEND_PID! /F > nul 2>&1
        del "%BACKEND_PID_FILE%" > nul 2>&1
        call :print_message "后端服务已停止"
    )
    
    :: 停止前端服务
    if exist "%FRONTEND_PID_FILE%" (
        set /p FRONTEND_PID=<"%FRONTEND_PID_FILE%"
        taskkill /PID !FRONTEND_PID! /F > nul 2>&1
        del "%FRONTEND_PID_FILE%" > nul 2>&1
        call :print_message "前端服务已停止"
    )
    
    :: 强制停止可能残留的进程
    taskkill /F /IM python.exe /FI "WINDOWTITLE eq *app.py*" > nul 2>&1
    taskkill /F /IM python.exe /FI "WINDOWTITLE eq *http.server*" > nul 2>&1
    
    call :print_success "所有服务已停止"
    goto :eof

:check_status
    call :print_message "检查服务状态..."
    
    set "backend_running=false"
    set "frontend_running=false"
    
    :: 检查后端
    if exist "%BACKEND_PID_FILE%" (
        set /p BACKEND_PID=<"%BACKEND_PID_FILE%"
        tasklist /PID !BACKEND_PID! > nul 2>&1
        if !errorlevel! equ 0 (
            call :print_success "后端服务运行中 (PID: !BACKEND_PID!, 端口: 5000)"
            set "backend_running=true"
        ) else (
            call :print_warning "后端PID文件存在但进程未运行"
            del "%BACKEND_PID_FILE%" > nul 2>&1
        )
    )
    
    if "!backend_running!"=="false" (
        call :check_port 5000
        if !errorlevel! equ 0 (
            call :print_warning "端口5000被占用，但不是本脚本启动的服务"
        ) else (
            call :print_error "后端服务未运行"
        )
    )
    
    :: 检查前端
    if exist "%FRONTEND_PID_FILE%" (
        set /p FRONTEND_PID=<"%FRONTEND_PID_FILE%"
        tasklist /PID !FRONTEND_PID! > nul 2>&1
        if !errorlevel! equ 0 (
            call :print_success "前端服务运行中 (PID: !FRONTEND_PID!, 端口: 3000)"
            set "frontend_running=true"
        ) else (
            call :print_warning "前端PID文件存在但进程未运行"
            del "%FRONTEND_PID_FILE%" > nul 2>&1
        )
    )
    
    if "!frontend_running!"=="false" (
        call :check_port 3000
        if !errorlevel! equ 0 (
            call :print_warning "端口3000被占用，但不是本脚本启动的服务"
        ) else (
            call :print_error "前端服务未运行"
        )
    )
    
    :: 显示访问地址
    if "!backend_running!"=="true" if "!frontend_running!"=="true" (
        echo.
        call :print_success "服务正在运行:"
        echo   前端地址: http://localhost:3000
        echo   后端API: http://localhost:5000/api/v1
        echo   日志目录: %LOG_DIR%
    )
    goto :eof

:start_services
    call :print_message "启动 STM32 OTA Server..."
    
    :: 检查Python环境
    python --version > nul 2>&1
    if !errorlevel! neq 0 (
        call :print_error "未找到Python环境"
        exit /b 1
    )
    
    :: 检查依赖
    python -c "import flask" > nul 2>&1
    if !errorlevel! neq 0 (
        call :print_warning "Flask未安装，尝试安装依赖..."
        if exist "requirements.txt" (
            pip install -r requirements.txt
        ) else (
            call :print_error "requirements.txt文件不存在"
            exit /b 1
        )
    )
    
    :: 检查端口占用
    call :check_port 5000
    if !errorlevel! equ 0 (
        call :print_error "端口5000已被占用，请先停止占用该端口的服务"
        exit /b 1
    )
    
    call :check_port 3000
    if !errorlevel! equ 0 (
        call :print_error "端口3000已被占用，请先停止占用该端口的服务"
        exit /b 1
    )
    
    call :print_message "启动后端服务 (端口: 5000)..."
    
    :: 启动后端 - 使用start /B 确保后台运行
    start /B "" cmd /c "python server\app.py > %LOG_DIR%\backend.log 2>&1"
    
    :: 等待一下让进程启动
    timeout /t 3 /nobreak > nul
    
    :: 获取后端进程PID (简单方法)
    for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *app.py*" /FO CSV ^| find /V "PID"') do (
        set "BACKEND_PID=%%i"
        set "BACKEND_PID=!BACKEND_PID:"=!"
    )
    
    if defined BACKEND_PID (
        echo !BACKEND_PID! > "%BACKEND_PID_FILE%"
        call :print_success "后端服务启动成功 (PID: !BACKEND_PID!)"
    ) else (
        call :print_error "后端启动失败，请查看日志: %LOG_DIR%\backend.log"
        exit /b 1
    )
    
    call :print_message "启动前端服务 (端口: 3000)..."
    
    :: 启动前端
    pushd client\public
    start /B "" cmd /c "python -m http.server 3000 > %LOG_DIR%\frontend.log 2>&1"
    popd
    
    :: 等待前端启动
    timeout /t 2 /nobreak > nul
    
    :: 获取前端进程PID
    for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *http.server*" /FO CSV ^| find /V "PID"') do (
        set "FRONTEND_PID=%%i"
        set "FRONTEND_PID=!FRONTEND_PID:"=!"
    )
    
    if defined FRONTEND_PID (
        echo !FRONTEND_PID! > "%FRONTEND_PID_FILE%"
        call :print_success "前端服务启动成功 (PID: !FRONTEND_PID!)"
    ) else (
        call :print_error "前端启动失败，请查看日志: %LOG_DIR%\frontend.log"
        exit /b 1
    )
    
    echo.
    call :print_success "所有服务启动完成!"
    echo   前端地址: http://localhost:3000
    echo   后端API: http://localhost:5000/api/v1
    echo   日志目录: %LOG_DIR%
    echo.
    call :print_message "服务已在后台运行，关闭命令行不会影响服务"
    call :print_message "使用 'start_server.bat stop' 停止服务"
    call :print_message "使用 'start_server.bat status' 查看服务状态"
    
    goto :eof

:show_logs
    set "service=%~2"
    if "!service!"=="" set "service=all"
    
    if "!service!"=="backend" (
        if exist "%LOG_DIR%\backend.log" (
            type "%LOG_DIR%\backend.log"
            call :print_message "使用 'tail -f %LOG_DIR%\backend.log' 查看实时日志"
        ) else (
            call :print_error "后端日志文件不存在"
        )
    ) else if "!service!"=="frontend" (
        if exist "%LOG_DIR%\frontend.log" (
            type "%LOG_DIR%\frontend.log"
            call :print_message "使用 'tail -f %LOG_DIR%\frontend.log' 查看实时日志"
        ) else (
            call :print_error "前端日志文件不存在"
        )
    ) else (
        call :print_message "显示所有服务日志..."
        if exist "%LOG_DIR%\backend.log" (
            echo ===== 后端日志 =====
            type "%LOG_DIR%\backend.log"
            echo.
        )
        if exist "%LOG_DIR%\frontend.log" (
            echo ===== 前端日志 =====
            type "%LOG_DIR%\frontend.log"
        )
        if not exist "%LOG_DIR%\backend.log" if not exist "%LOG_DIR%\frontend.log" (
            call :print_error "日志文件不存在"
        )
    )
    goto :eof

:restart_services
    call :print_message "重启服务..."
    call :stop_services
    timeout /t 2 /nobreak > nul
    call :start_services
    goto :eof

:show_help
    echo STM32 OTA Server 管理脚本 (Windows)
    echo.
    echo 用法: %~nx0 [COMMAND] [OPTIONS]
    echo.
    echo 命令:
    echo   start         启动服务（默认）
    echo   stop          停止服务
    echo   restart       重启服务
    echo   status        查看服务状态
    echo   logs [TYPE]   查看日志 (TYPE: backend/frontend/all，默认all)
    echo   help          显示帮助信息
    echo.
    echo 示例:
    echo   %~nx0              # 启动服务
    echo   %~nx0 start        # 启动服务
    echo   %~nx0 stop         # 停止服务
    echo   %~nx0 status       # 查看状态
    echo   %~nx0 logs         # 查看所有日志
    echo   %~nx0 logs backend # 只查看后端日志
    goto :eof

:main
    set "command=%~1"
    if "!command!"=="" set "command=start"
    
    if "!command!"=="start" (
        call :start_services
    ) else if "!command!"=="stop" (
        call :stop_services
    ) else if "!command!"=="restart" (
        call :restart_services
    ) else if "!command!"=="status" (
        call :check_status
    ) else if "!command!"=="logs" (
        call :show_logs %*
    ) else if "!command!"=="help" (
        call :show_help
    ) else if "!command!"=="-h" (
        call :show_help
    ) else if "!command!"=="--help" (
        call :show_help
    ) else (
        call :print_error "未知命令: !command!"
        call :show_help
        exit /b 1
    )

pause