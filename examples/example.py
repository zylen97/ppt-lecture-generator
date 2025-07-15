#!/usr/bin/env python3
"""
PPT讲稿生成器使用示例
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.script_generator import ScriptGenerator
from src.config.settings import Settings

def example_basic():
    """基本使用示例"""
    print("=== 基本使用示例 ===")
    
    # 初始化设置
    settings = Settings()
    
    # 创建讲稿生成器
    generator = ScriptGenerator(settings)
    
    # 配置生成参数
    config = {
        'total_duration': 90,  # 90分钟
        'language': 'zh-CN',
        'include_interaction': True,
        'include_examples': True
    }
    generator.update_config(config)
    
    # 生成讲稿
    ppt_file = "presentation.pptx"
    output_file = "lecture_script.md"
    
    try:
        success = generator.generate(ppt_file, output_file)
        if success:
            print(f"✅ 讲稿生成成功: {output_file}")
        else:
            print("❌ 讲稿生成失败")
    except Exception as e:
        print(f"❌ 错误: {e}")

def example_custom_api():
    """自定义API配置示例"""
    print("\n=== 自定义API配置示例 ===")
    
    from src.core.ai_client import AIClient
    
    # 创建自定义AI客户端
    client = AIClient(
        api_key="your-api-key",
        api_base="https://api.example.com/v1",
        model="gpt-4o"
    )
    
    # 测试连接
    if client.test_connection():
        print("✅ API连接成功")
    else:
        print("❌ API连接失败")
    
    client.close()

def example_batch_processing():
    """批量处理示例"""
    print("\n=== 批量处理示例 ===")
    
    import glob
    
    # 获取所有PPT文件
    ppt_files = glob.glob("*.pptx")
    
    # 初始化
    settings = Settings()
    generator = ScriptGenerator(settings)
    
    # 批量处理
    for ppt_file in ppt_files:
        output_file = Path(ppt_file).stem + "_讲稿.md"
        print(f"处理: {ppt_file} -> {output_file}")
        
        try:
            generator.generate(ppt_file, output_file)
            print(f"  ✅ 成功")
        except Exception as e:
            print(f"  ❌ 失败: {e}")

def example_progress_callback():
    """进度回调示例"""
    print("\n=== 进度回调示例 ===")
    
    def progress_callback(progress: float, message: str):
        """进度回调函数"""
        bar_length = 30
        filled = int(bar_length * progress / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"\r[{bar}] {progress:.1f}% - {message}", end='', flush=True)
    
    # 使用回调
    settings = Settings()
    generator = ScriptGenerator(settings)
    
    # 设置回调（实际使用时需要修改ScriptGenerator支持回调）
    # generator.set_progress_callback(progress_callback)
    
    print("\n进度回调功能需要在实际项目中实现")

def example_ppt_to_images():
    """PPT转图片示例"""
    print("\n=== PPT转图片示例 ===")
    
    from src.utils.ppt_converter import PPTConverter
    
    converter = PPTConverter()
    
    # 转换PPT到图片
    ppt_file = "presentation.pptx"
    output_dir = "output_images"
    
    print(f"转换 {ppt_file} 到图片...")
    image_paths = converter.convert_ppt_to_images(ppt_file, output_dir)
    
    if image_paths:
        print(f"✅ 成功生成 {len(image_paths)} 张图片:")
        for path in image_paths[:3]:  # 只显示前3个
            print(f"  - {path}")
    else:
        print("❌ 转换失败")

def main():
    """主函数"""
    print("PPT讲稿生成器 - 使用示例")
    print("=" * 50)
    
    # 运行各种示例
    try:
        example_basic()
    except Exception as e:
        print(f"基本示例失败: {e}")
    
    try:
        example_custom_api()
    except Exception as e:
        print(f"自定义API示例失败: {e}")
    
    try:
        example_batch_processing()
    except Exception as e:
        print(f"批量处理示例失败: {e}")
    
    try:
        example_progress_callback()
    except Exception as e:
        print(f"进度回调示例失败: {e}")
    
    try:
        example_ppt_to_images()
    except Exception as e:
        print(f"PPT转图片示例失败: {e}")
    
    print("\n" + "=" * 50)
    print("示例运行完成！")

if __name__ == "__main__":
    main()