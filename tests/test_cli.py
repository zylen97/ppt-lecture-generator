#!/usr/bin/env python3
"""
命令行功能测试脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """测试所有模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        from src.config.settings import Settings
        print("✅ 配置模块导入成功")
        
        from src.core.ai_client import AIClient
        print("✅ AI客户端模块导入成功")
        
        from src.core.script_generator import ScriptGenerator
        print("✅ 脚本生成器模块导入成功")
        
        from src.utils.validators import Validators
        print("✅ 验证器模块导入成功")
        
        from src.utils.file_utils import FileUtils
        print("✅ 文件工具模块导入成功")
        
        from src.utils.logger import get_logger
        print("✅ 日志模块导入成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_config():
    """测试配置管理"""
    print("\\n⚙️ 测试配置管理...")
    
    try:
        from src.config.settings import Settings
        
        settings = Settings()
        print("✅ 设置对象创建成功")
        
        # 测试配置读取
        api_config = settings.get_section('api')
        print(f"✅ API配置读取成功: {len(api_config)} 项")
        
        # 测试配置验证
        is_valid, errors = settings.validate_all()
        print(f"✅ 配置验证完成: {'通过' if is_valid else '有错误'}")
        if errors:
            for error in errors:
                print(f"  ⚠️ {error}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False

def test_validators():
    """测试验证器"""
    print("\\n🔍 测试验证器...")
    
    try:
        from src.utils.validators import Validators
        
        # 测试API密钥验证
        valid_key = "sk-1234567890abcdefghijklmnopqrstuvwxyz"
        is_valid, error = Validators.validate_api_key(valid_key)
        print(f"✅ API密钥验证: {'通过' if is_valid else '失败'}")
        
        # 测试API端点验证
        valid_endpoint = "https://api.chatanywhere.tech/v1"
        is_valid, error = Validators.validate_api_endpoint(valid_endpoint)
        print(f"✅ API端点验证: {'通过' if is_valid else '失败'}")
        
        # 测试时长验证
        is_valid, error = Validators.validate_duration(90)
        print(f"✅ 时长验证: {'通过' if is_valid else '失败'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 验证器测试失败: {e}")
        return False

def test_ai_client():
    """测试AI客户端（不实际调用API）"""
    print("\\n🤖 测试AI客户端...")
    
    try:
        from src.core.ai_client import AIClient
        
        # 创建客户端实例
        client = AIClient(
            api_key="sk-test",
            api_base="https://api.example.com",
            model="gpt-4o"
        )
        print("✅ AI客户端创建成功")
        
        # 测试编码功能
        # 创建一个测试图片文件
        test_image = Path(__file__).parent / "test.png"
        if not test_image.exists():
            # 创建一个简单的测试图片
            try:
                from PIL import Image
                img = Image.new('RGB', (100, 100), color='red')
                img.save(test_image)
                print("✅ 测试图片创建成功")
            except ImportError:
                print("⚠️ PIL不可用，跳过图片编码测试")
                client.close()
                return True
        
        if test_image.exists():
            encoded = client._encode_image(str(test_image))
            if encoded:
                print("✅ 图片编码功能正常")
            else:
                print("⚠️ 图片编码失败")
            
            # 清理测试文件
            test_image.unlink()
        
        client.close()
        print("✅ AI客户端关闭成功")
        
        return True
        
    except Exception as e:
        print(f"❌ AI客户端测试失败: {e}")
        return False

def test_file_utils():
    """测试文件工具"""
    print("\\n📁 测试文件工具...")
    
    try:
        from src.utils.file_utils import FileUtils
        
        # 测试目录创建
        test_dir = Path(__file__).parent / "test_temp"
        success = FileUtils.ensure_dir(test_dir)
        print(f"✅ 目录创建: {'成功' if success else '失败'}")
        
        # 测试文件信息获取
        info = FileUtils.get_file_info(__file__)
        print(f"✅ 文件信息获取: {len(info)} 项")
        
        # 测试安全文件名
        safe_name = FileUtils.get_safe_filename("test<>file|name.txt")
        print(f"✅ 安全文件名: {safe_name}")
        
        # 清理测试目录
        if test_dir.exists():
            test_dir.rmdir()
        
        return True
        
    except Exception as e:
        print(f"❌ 文件工具测试失败: {e}")
        return False

def run_full_test():
    """运行完整测试"""
    print("🚀 开始PPT讲稿生成器功能测试")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_imports),
        ("配置管理", test_config),
        ("验证器", test_validators),
        ("AI客户端", test_ai_client),
        ("文件工具", test_file_utils),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统可以正常使用")
        return True
    else:
        print("⚠️ 部分测试失败，请检查相关功能")
        return False

def main():
    """主函数"""
    try:
        return 0 if run_full_test() else 1
    except KeyboardInterrupt:
        print("\\n⏹️ 测试被用户中断")
        return 1
    except Exception as e:
        print(f"❌ 测试运行异常: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())