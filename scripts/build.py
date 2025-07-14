#!/usr/bin/env python3
"""
构建脚本

用于构建可执行文件和发布包。
"""

import sys
import subprocess
import os
import shutil
from pathlib import Path
import zipfile
import tarfile
import platform


def get_project_info():
    """获取项目信息"""
    project_root = Path(__file__).parent.parent
    
    # 读取版本信息
    init_file = project_root / "src" / "__init__.py"
    version = "1.0.0"  # 默认版本
    
    if init_file.exists():
        with open(init_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('__version__'):
                    version = line.split('=')[1].strip().strip('"\'')
                    break
    
    return {
        'name': 'ppt-lecture-generator',
        'version': version,
        'root': project_root
    }


def clean_build():
    """清理构建目录"""
    print("🧹 清理构建目录...")
    
    project_info = get_project_info()
    build_dirs = [
        project_info['root'] / "build",
        project_info['root'] / "dist",
        project_info['root'] / "*.egg-info",
        project_info['root'] / "__pycache__",
    ]
    
    for build_dir in build_dirs:
        if build_dir.exists():
            if build_dir.is_dir():
                shutil.rmtree(build_dir)
            else:
                build_dir.unlink()
    
    # 清理Python缓存
    for root, dirs, files in os.walk(project_info['root']):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                shutil.rmtree(Path(root) / dir_name)
        for file_name in files:
            if file_name.endswith('.pyc'):
                (Path(root) / file_name).unlink()
    
    print("✅ 构建目录清理完成")


def build_executable():
    """构建可执行文件"""
    print("🔨 构建可执行文件...")
    
    project_info = get_project_info()
    
    try:
        # 检查是否安装了PyInstaller
        subprocess.run([sys.executable, "-c", "import PyInstaller"], check=True)
    except (subprocess.CalledProcessError, ImportError):
        print("⚠️ PyInstaller未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # PyInstaller配置
    main_script = project_info['root'] / "src" / "main.py"
    icon_file = project_info['root'] / "resources" / "icons" / "app.ico"
    
    pyinstaller_args = [
        sys.executable, "-m", "PyInstaller",
        "--name", f"PPT讲稿生成器-{project_info['version']}",
        "--onefile",
        "--windowed",
        "--add-data", f"{project_info['root']}/src/config:config",
        "--add-data", f"{project_info['root']}/resources:resources",
        "--hidden-import", "tkinter",
        "--hidden-import", "PIL",
        "--hidden-import", "requests",
        str(main_script)
    ]
    
    if icon_file.exists():
        pyinstaller_args.extend(["--icon", str(icon_file)])
    
    try:
        subprocess.run(pyinstaller_args, cwd=project_info['root'], check=True)
        print("✅ 可执行文件构建完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 可执行文件构建失败：{e}")
        return False


def build_package():
    """构建Python包"""
    print("📦 构建Python包...")
    
    project_info = get_project_info()
    
    try:
        # 构建源码包
        subprocess.run([
            sys.executable, "setup.py", "sdist"
        ], cwd=project_info['root'], check=True)
        
        # 构建wheel包
        subprocess.run([
            sys.executable, "setup.py", "bdist_wheel"
        ], cwd=project_info['root'], check=True)
        
        print("✅ Python包构建完成")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Python包构建失败：{e}")
        return False


def create_release_archive():
    """创建发布归档"""
    print("📋 创建发布归档...")
    
    project_info = get_project_info()
    
    # 创建归档目录
    archive_name = f"{project_info['name']}-{project_info['version']}"
    archive_dir = project_info['root'] / "dist" / archive_name
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # 复制文件
    files_to_copy = [
        "src/",
        "resources/",
        "scripts/",
        "tests/",
        "README.md",
        "LICENSE",
        "requirements.txt",
        "setup.py",
        "项目结构设计.md"
    ]
    
    for file_path in files_to_copy:
        src_path = project_info['root'] / file_path
        dst_path = archive_dir / file_path
        
        if src_path.exists():
            if src_path.is_dir():
                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
            else:
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dst_path)
    
    # 创建zip归档
    zip_path = project_info['root'] / "dist" / f"{archive_name}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(archive_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(archive_dir.parent)
                zipf.write(file_path, arcname)
    
    # 创建tar.gz归档
    tar_path = project_info['root'] / "dist" / f"{archive_name}.tar.gz"
    with tarfile.open(tar_path, 'w:gz') as tarf:
        tarf.add(archive_dir, arcname=archive_name)
    
    # 清理临时目录
    shutil.rmtree(archive_dir)
    
    print(f"✅ 发布归档创建完成：")
    print(f"  - {zip_path}")
    print(f"  - {tar_path}")
    
    return True


def run_quality_checks():
    """运行代码质量检查"""
    print("🔍 运行代码质量检查...")
    
    project_info = get_project_info()
    src_dir = project_info['root'] / "src"
    
    checks = [
        {
            'name': 'flake8',
            'command': [sys.executable, '-m', 'flake8', str(src_dir)],
            'install': 'flake8'
        },
        {
            'name': 'mypy',
            'command': [sys.executable, '-m', 'mypy', str(src_dir)],
            'install': 'mypy'
        },
        {
            'name': 'black',
            'command': [sys.executable, '-m', 'black', '--check', str(src_dir)],
            'install': 'black'
        }
    ]
    
    passed = 0
    for check in checks:
        try:
            subprocess.run(check['command'], check=True, capture_output=True)
            print(f"✅ {check['name']} 检查通过")
            passed += 1
        except subprocess.CalledProcessError:
            print(f"❌ {check['name']} 检查失败")
        except FileNotFoundError:
            print(f"⚠️ {check['name']} 未安装，跳过检查")
    
    print(f"📊 代码质量检查完成：{passed}/{len(checks)} 项通过")
    return passed == len(checks)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PPT讲稿生成器构建脚本")
    parser.add_argument("--clean", action="store_true", help="清理构建目录")
    parser.add_argument("--executable", action="store_true", help="构建可执行文件")
    parser.add_argument("--package", action="store_true", help="构建Python包")
    parser.add_argument("--archive", action="store_true", help="创建发布归档")
    parser.add_argument("--quality", action="store_true", help="运行代码质量检查")
    parser.add_argument("--all", action="store_true", help="执行所有构建步骤")
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        parser.print_help()
        return 1
    
    print("🏗️ PPT讲稿生成器构建脚本")
    print("=" * 50)
    
    success = True
    
    if args.clean or args.all:
        clean_build()
    
    if args.quality or args.all:
        if not run_quality_checks():
            success = False
    
    if args.package or args.all:
        if not build_package():
            success = False
    
    if args.executable or args.all:
        if not build_executable():
            success = False
    
    if args.archive or args.all:
        if not create_release_archive():
            success = False
    
    print("=" * 50)
    if success:
        print("🎉 构建完成！")
    else:
        print("❌ 构建过程中出现错误")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())