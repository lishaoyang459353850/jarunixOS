@echo off
rem ============================================================
rem  jarunixOS 安装程序 —— Windows 构建脚本
rem  依赖：Python 3.9+（自带 tkinter）、PyInstaller
rem  产物：dist\jarunixOS-USB-Setup.exe（独立安装器）
rem        dist\jarunixOS-USB-Setup-2in1.exe（内嵌两个版本镜像）
rem ============================================================
setlocal
cd /d "%~dp0"

echo.
echo ============================================================
echo   jarunixOS 安装程序 - 构建
echo ============================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 找不到 python。请先安装 Python 3.9 或更高版本，
    echo        并在安装时勾选 "Add python.exe to PATH"。
    goto :fail
)

echo [1/3] 检查 PyInstaller ...
python -m PyInstaller --version >nul 2>nul
if errorlevel 1 (
    echo       未安装，正在通过 pip 安装 ...
    python -m pip install --upgrade pyinstaller
    if errorlevel 1 (
        echo [错误] PyInstaller 安装失败。请检查网络，或手动执行：
        echo        python -m pip install pyinstaller
        goto :fail
    )
)
for /f "delims=" %%v in ('python -m PyInstaller --version') do echo       PyInstaller %%v

echo.
echo [2/3] 编译独立安装器 ...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
python -m PyInstaller --noconfirm --clean --onefile --noconsole ^
    --name jarunixOS-USB-Setup ^
    --hidden-import disks --hidden-import editions --hidden-import wizard ^
    main.py
if errorlevel 1 (
    echo [错误] 编译失败。
    goto :fail
)

echo.
echo [3/3] 合成内嵌镜像的单文件安装程序 ...
set "ISO_P=jarunixOS-1.0-personal-amd64.iso"
if not exist "%ISO_P%" set "ISO_P=payload\jarunixOS-1.0-personal-amd64.iso"
set "ISO_R=jarunixOS-1.0-professional-amd64.iso"
if not exist "%ISO_R%" set "ISO_R=payload\jarunixOS-1.0-professional-amd64.iso"

if not exist "%ISO_P%" goto :noiso
if not exist "%ISO_R%" goto :noiso

python pack_payload.py "dist\jarunixOS-USB-Setup.exe" "dist\jarunixOS-USB-Setup-2in1.exe" "%ISO_P%" "%ISO_R%"
if errorlevel 1 (
    echo [错误] 载荷合成失败。
    goto :fail
)
echo.
echo 完成。内嵌双版本镜像的安装程序：
echo   dist\jarunixOS-USB-Setup-2in1.exe
goto :end

:noiso
echo.
echo [提示] 当前目录没有找到两个版本的 .iso 镜像，已跳过单文件合成。
echo        只生成独立安装器：dist\jarunixOS-USB-Setup.exe
echo.
echo        如需生成内嵌镜像的单文件版本，请把下列两个文件放到本目录
echo        （或本目录的 payload\ 子目录）后重新运行本脚本：
echo          jarunixOS-1.0-personal-amd64.iso
echo          jarunixOS-1.0-professional-amd64.iso
goto :end

:fail
echo.
echo 构建未完成。
pause
exit /b 1

:end
echo.
pause
exit /b 0
