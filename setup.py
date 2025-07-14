"""
安装脚本

用于安装PPT讲稿生成器。
"""

from setuptools import setup, find_packages
import os
from pathlib import Path

# 读取README文件
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# 读取requirements文件
requirements_path = this_directory / "requirements.txt"
if requirements_path.exists():
    with open(requirements_path, 'r', encoding='utf-8') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
else:
    requirements = [
        'requests>=2.31.0',
        'Pillow>=10.1.0',
        'python-pptx>=0.6.23',
        'configparser>=6.0.0',
        'tqdm>=4.66.1',
        'colorama>=0.4.6',
        'loguru>=0.7.2'
    ]

setup(
    name="ppt-lecture-generator",
    version="1.0.0",
    author="PPT Lecture Generator Team",
    author_email="zylenw97@gmail.com",
    description="一个基于AI的PPT讲稿自动生成工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zylen97/ppt-lecture-generator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Education",
        "Topic :: Office/Business :: Office Suites",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Markup :: Markdown",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=7.4.3',
            'pytest-cov>=4.1.0',
            'black>=23.11.0',
            'flake8>=6.1.0',
            'mypy>=1.7.1',
        ],
        'gui': [
            'tkinter-tooltip>=3.0.0',
        ],
        'full': [
            'spire.presentation>=9.2.0',
            'pdf2image>=1.16.3',
            'aiohttp>=3.8.0',
        ]
    },
    entry_points={
        'console_scripts': [
            'ppt-lecture-generator=src.main:main',
            'plg=src.main:main',
        ],
    },
    include_package_data=True,
    package_data={
        'src': ['config/default_config.json'],
        'resources': ['templates/*', 'icons/*'],
    },
    zip_safe=False,
    keywords=[
        'ppt', 'powerpoint', 'lecture', 'script', 'ai', 'generation', 
        'education', 'teaching', 'presentation', 'automation'
    ],
    project_urls={
        'Bug Reports': 'https://github.com/zylen97/ppt-lecture-generator/issues',
        'Source': 'https://github.com/zylen97/ppt-lecture-generator',
        'Documentation': 'https://github.com/zylen97/ppt-lecture-generator/blob/main/README.md',
    },
)