#!/usr/bin/env python3
"""
PPT讲稿生成器主程序入口

提供命令行和GUI两种使用方式。
"""

import sys
import argparse
from pathlib import Path
import os

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.script_generator import ScriptGenerator
from src.config.settings import Settings
from src.utils.logger import init_logger, get_logger
from src.utils.validators import Validators


def setup_logging():
    """设置日志"""
    logger = init_logger("ppt_lecture_generator", "INFO")
    return logger


def create_argument_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="PPT讲稿生成器 - 基于AI的PPT讲稿自动生成工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 启动GUI界面
  python main.py --gui
  
  # 命令行生成讲稿
  python main.py --input presentation.pptx --output lecture.md
  
  # 使用自定义API配置
  python main.py --input presentation.pptx --api-key sk-xxx --api-base https://api.example.com
  
  # 设置课程时长
  python main.py --input presentation.pptx --duration 120
        """
    )
    
    # 运行模式
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--gui", 
        action="store_true",
        help="启动图形界面（默认）"
    )
    mode_group.add_argument(
        "--cli", 
        action="store_true",
        help="使用命令行模式"
    )
    
    # 文件参数
    parser.add_argument(
        "--input", "-i",
        type=str,
        help="输入PPT文件路径"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="输出讲稿文件路径"
    )
    
    # API配置
    parser.add_argument(
        "--api-key", "-k",
        type=str,
        help="API密钥"
    )
    parser.add_argument(
        "--api-base", "-b",
        type=str,
        help="API基础URL"
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        help="使用的模型"
    )
    
    # 生成配置
    parser.add_argument(
        "--duration", "-d",
        type=int,
        default=90,
        help="课程时长（分钟，默认90）"
    )
    parser.add_argument(
        "--language", "-l",
        type=str,
        default="zh-CN",
        choices=["zh-CN", "zh-TW", "en-US"],
        help="语言设置（默认zh-CN）"
    )
    
    # 其他选项
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细日志"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="静默模式"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="指定配置文件路径"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="PPT讲稿生成器 v1.0.0"
    )
    
    return parser


def validate_arguments(args):
    """验证命令行参数"""
    logger = get_logger()
    
    # 如果是CLI模式，需要输入文件
    if args.cli and not args.input:
        logger.error("命令行模式需要指定输入文件")
        return False
    
    # 验证输入文件
    if args.input:
        is_valid, error = Validators.validate_ppt_file(args.input)
        if not is_valid:
            logger.error(f"输入文件验证失败: {error}")
            return False
    
    # 验证API密钥
    if args.api_key:
        is_valid, error = Validators.validate_api_key(args.api_key)
        if not is_valid:
            logger.error(f"API密钥验证失败: {error}")
            return False
    
    # 验证API端点
    if args.api_base:
        is_valid, error = Validators.validate_api_endpoint(args.api_base)
        if not is_valid:
            logger.error(f"API端点验证失败: {error}")
            return False
    
    # 验证时长
    if args.duration:
        is_valid, error = Validators.validate_duration(args.duration)
        if not is_valid:
            logger.error(f"时长验证失败: {error}")
            return False
    
    return True


def run_gui_mode():
    """运行GUI模式"""
    logger = get_logger()
    
    try:
        logger.info("启动GUI模式")
        
        # 检查GUI依赖
        try:
            import tkinter as tk
        except ImportError:
            logger.error("GUI模式需要tkinter支持")
            print("错误：GUI模式需要tkinter支持")
            return False
        
        # 导入并运行GUI
        from src.gui.main_window import MainWindow
        
        app = MainWindow()
        app.run()
        
        logger.info("GUI模式正常退出")
        return True
        
    except Exception as e:
        logger.error(f"GUI模式运行失败: {e}")
        print(f"错误：GUI模式运行失败: {e}")
        return False


def run_cli_mode(args):
    """运行CLI模式"""
    logger = get_logger()
    
    try:
        logger.info("启动CLI模式")
        
        # 加载配置
        settings = Settings(args.config) if args.config else Settings()
        
        # 获取API配置
        api_key = args.api_key or settings.get('api', 'api_key')
        api_base = args.api_base or settings.get('api', 'endpoint')
        model = args.model or settings.get('api', 'model')
        
        if not all([api_key, api_base, model]):
            logger.error("缺少必要的API配置")
            print("错误：缺少必要的API配置（api_key, api_base, model）")
            return False
        
        # 创建脚本生成器
        generator = ScriptGenerator(
            api_key=api_key,
            api_base=api_base,
            model=model
        )
        
        # 设置生成配置
        generation_config = {
            'total_duration': args.duration,
            'language': args.language,
            'include_interaction': True,
            'include_examples': True
        }
        generator.set_generation_config(generation_config)
        
        # 设置进度回调
        def progress_callback(current, total, message):
            if not args.quiet:
                percentage = (current / total) * 100 if total > 0 else 0
                print(f"\\r进度: {percentage:.1f}% - {message}", end="", flush=True)
        
        generator.set_progress_callback(progress_callback)
        
        # 开始生成
        print(f"正在处理文件: {args.input}")
        
        success, result = generator.generate_from_ppt(
            args.input,
            args.output
        )
        
        if not args.quiet:
            print()  # 换行
        
        if success:
            print(f"✅ 讲稿生成成功: {result}")
            
            # 显示统计信息
            if args.verbose:
                stats = generator.get_generation_stats()
                print("\\n📊 生成统计:")
                print(f"  处理时间: {stats.get('total_time', 0):.1f}秒")
                print(f"  处理幻灯片: {stats.get('total_slides', 0)}张")
                print(f"  讲稿长度: {stats.get('total_length', 0):,}字符")
            
            logger.info(f"CLI模式成功完成: {result}")
            return True
        else:
            print(f"❌ 讲稿生成失败: {result}")
            logger.error(f"CLI模式失败: {result}")
            return False
            
    except KeyboardInterrupt:
        print("\\n⏹️ 用户中断")
        logger.info("用户中断CLI模式")
        return False
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        logger.error(f"CLI模式异常: {e}")
        return False
    finally:
        # 清理资源
        try:
            generator.cleanup()
        except:
            pass


def main():
    """主函数"""
    # 设置日志
    logger = setup_logging()
    
    try:
        # 解析命令行参数
        parser = create_argument_parser()
        args = parser.parse_args()
        
        # 设置日志级别
        if args.verbose:
            logger.set_level("DEBUG")
        elif args.quiet:
            logger.set_level("ERROR")
        
        # 验证参数
        if not validate_arguments(args):
            return 1
        
        # 确定运行模式
        if args.cli:
            # CLI模式
            success = run_cli_mode(args)
        else:
            # GUI模式（默认）
            success = run_gui_mode()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("用户中断程序")
        print("\\n程序被用户中断")
        return 1
    except Exception as e:
        logger.error(f"程序运行失败: {e}")
        print(f"错误：程序运行失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())