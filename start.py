#!/usr/bin/env python3
"""
快速启动脚本

提供简单的启动方式。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    # 导入主程序
    from src.main import main
    
    # 运行主程序
    if __name__ == "__main__":
        # 如果没有命令行参数，默认启动GUI
        if len(sys.argv) == 1:
            sys.argv.append("--gui")
        
        sys.exit(main())
        
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保已安装所有依赖，运行：pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ 运行错误: {e}")
    sys.exit(1)