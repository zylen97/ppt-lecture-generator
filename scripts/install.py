#!/usr/bin/env python3
"""
安装脚本

自动安装PPT讲稿生成器和依赖。
"""

import sys
import subprocess
import os
import platform
from pathlib import Path


def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version < (3, 8):
        print("❌ 错误：需要Python 3.8或更高版本")
        print(f"当前版本：{version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python版本检查通过：{version.major}.{version.minor}.{version.micro}")
    return True


def check_system_requirements():
    """检查系统要求"""
    print("🔍 检查系统要求...")
    
    system = platform.system()
    print(f"操作系统：{system} {platform.release()}")
    
    # 检查内存
    try:
        if system == "Darwin":  # macOS
            import resource
            memory_limit = resource.getrlimit(resource.RLIMIT_RSS)[0]
            if memory_limit > 0:
                print(f"内存限制：{memory_limit // (1024*1024)} MB")
        elif system == "Linux":
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if 'MemTotal' in line:
                        memory = int(line.split()[1]) // 1024
                        print(f"总内存：{memory} MB")
                        break
    except:
        pass
    
    return True


def install_dependencies():
    """安装依赖"""
    print("📦 安装Python依赖...")
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    requirements_file = project_root / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ 错误：找不到requirements.txt文件")
        return False
    
    try:
        # 升级pip
        subprocess.run([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ], check=True)
        print("✅ pip已升级")
        
        # 安装依赖
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True)
        print("✅ Python依赖安装完成")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败：{e}")
        return False


def install_optional_dependencies():
    """安装可选依赖"""
    print("🎯 安装可选依赖...")
    
    optional_packages = [
        ("spire.presentation", "PPT处理增强"),
        ("pdf2image", "PDF转图片支持"),
        ("aiohttp", "异步HTTP客户端"),
    ]
    
    for package, description in optional_packages:
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], check=True, capture_output=True)
            print(f"✅ {package} ({description}) 安装成功")
        except subprocess.CalledProcessError:
            print(f"⚠️ {package} ({description}) 安装失败，将跳过")


def setup_desktop_shortcut():
    """创建桌面快捷方式"""
    print("🖥️ 创建桌面快捷方式...")
    
    try:
        system = platform.system()
        project_root = Path(__file__).parent.parent
        
        if system == "Darwin":  # macOS
            # 创建macOS应用程序包
            app_name = "PPT讲稿生成器.app"
            desktop_path = Path.home() / "Desktop" / app_name
            
            # 这里可以创建macOS应用程序包
            print("ℹ️ macOS快捷方式创建功能待实现")
            
        elif system == "Windows":
            # 创建Windows快捷方式
            desktop_path = Path.home() / "Desktop" / "PPT讲稿生成器.lnk"
            
            # 这里可以创建Windows快捷方式
            print("ℹ️ Windows快捷方式创建功能待实现")
            
        else:  # Linux
            # 创建Linux桌面文件
            desktop_path = Path.home() / "Desktop" / "ppt-lecture-generator.desktop"
            
            desktop_content = f"""[Desktop Entry]
Name=PPT讲稿生成器
Comment=基于AI的PPT讲稿自动生成工具
Exec={sys.executable} {project_root}/src/main.py --gui
Icon={project_root}/resources/icons/app.png
Terminal=false
Type=Application
Categories=Education;Office;
"""
            
            with open(desktop_path, 'w', encoding='utf-8') as f:
                f.write(desktop_content)
            
            # 设置可执行权限
            os.chmod(desktop_path, 0o755)
            print(f"✅ 桌面快捷方式已创建：{desktop_path}")
    
    except Exception as e:
        print(f"⚠️ 创建桌面快捷方式失败：{e}")


def create_start_script():
    """创建启动脚本"""
    print("📜 创建启动脚本...")
    
    project_root = Path(__file__).parent.parent
    
    # 创建启动脚本
    if platform.system() == "Windows":
        script_path = project_root / "start.bat"
        script_content = f"""@echo off
cd /d "{project_root}"
python src/main.py --gui
pause
"""
    else:
        script_path = project_root / "start.sh"
        script_content = f"""#!/bin/bash
cd "{project_root}"
python3 src/main.py --gui
"""
    
    try:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        if platform.system() != "Windows":
            os.chmod(script_path, 0o755)
        
        print(f"✅ 启动脚本已创建：{script_path}")
        
    except Exception as e:
        print(f"⚠️ 创建启动脚本失败：{e}")


def run_tests():
    """运行测试"""
    print("🧪 运行测试...")
    
    project_root = Path(__file__).parent.parent
    
    try:
        # 运行基础测试
        subprocess.run([
            sys.executable, "-m", "pytest", 
            str(project_root / "tests"), 
            "-v"
        ], cwd=project_root, check=True)
        print("✅ 测试通过")
        return True
        
    except subprocess.CalledProcessError:
        print("⚠️ 测试失败，但不影响安装")
        return False
    except FileNotFoundError:
        print("ℹ️ 未找到pytest，跳过测试")
        return True


def main():
    """主函数"""
    print("🚀 开始安装PPT讲稿生成器...")
    print("=" * 50)
    
    # 检查Python版本
    if not check_python_version():
        return 1
    
    # 检查系统要求
    if not check_system_requirements():
        return 1
    
    # 安装依赖
    if not install_dependencies():
        return 1
    
    # 安装可选依赖
    install_optional_dependencies()
    
    # 创建启动脚本
    create_start_script()
    
    # 创建桌面快捷方式
    setup_desktop_shortcut()
    
    # 运行测试
    run_tests()
    
    print("=" * 50)
    print("🎉 安装完成！")
    print("\\n使用方法：")
    print("1. 运行GUI界面：python src/main.py --gui")
    print("2. 命令行模式：python src/main.py --cli --input your_file.pptx")
    print("3. 使用启动脚本：./start.sh (Linux/macOS) 或 start.bat (Windows)")
    print("\\n如有问题，请查看README.md或提交Issue")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())