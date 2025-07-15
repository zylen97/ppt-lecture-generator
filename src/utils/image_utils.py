"""
图片处理工具模块

提供图片格式转换、压缩和处理功能。
"""

import os
from pathlib import Path
from typing import Tuple, Optional, Union
import base64

try:
    from PIL import Image, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from .logger import get_logger


class ImageUtils:
    """图片处理工具类"""
    
    @staticmethod
    def is_image_file(file_path: Union[str, Path]) -> bool:
        """
        检查是否为图片文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否为图片文件
        """
        try:
            image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
            extension = Path(file_path).suffix.lower()
            return extension in image_extensions
        except Exception:
            return False
    
    @staticmethod
    def get_image_info(file_path: Union[str, Path]) -> dict:
        """
        获取图片信息
        
        Args:
            file_path: 图片文件路径
            
        Returns:
            dict: 图片信息
        """
        if not PIL_AVAILABLE:
            return {'error': 'PIL not available'}
        
        try:
            with Image.open(file_path) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'size': os.path.getsize(file_path)
                }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def resize_image(input_path: Union[str, Path], output_path: Union[str, Path],
                    size: Tuple[int, int], keep_aspect: bool = True) -> bool:
        """
        调整图片大小
        
        Args:
            input_path: 输入图片路径
            output_path: 输出图片路径
            size: 目标尺寸 (width, height)
            keep_aspect: 是否保持宽高比
            
        Returns:
            bool: 是否成功
        """
        if not PIL_AVAILABLE:
            get_logger().error("PIL未安装，无法调整图片大小")
            return False
        
        try:
            with Image.open(input_path) as img:
                if keep_aspect:
                    img.thumbnail(size, Image.Resampling.LANCZOS)
                else:
                    img = img.resize(size, Image.Resampling.LANCZOS)
                
                img.save(output_path)
                return True
                
        except Exception as e:
            get_logger().error(f"调整图片大小失败: {e}")
            return False
    
    @staticmethod
    def convert_format(input_path: Union[str, Path], output_path: Union[str, Path],
                      format: str = 'PNG') -> bool:
        """
        转换图片格式
        
        Args:
            input_path: 输入图片路径
            output_path: 输出图片路径
            format: 目标格式
            
        Returns:
            bool: 是否成功
        """
        if not PIL_AVAILABLE:
            get_logger().error("PIL未安装，无法转换图片格式")
            return False
        
        try:
            with Image.open(input_path) as img:
                # 转换为RGB模式（某些格式需要）
                if format.upper() in ['JPEG', 'JPG'] and img.mode in ['RGBA', 'P']:
                    img = img.convert('RGB')
                
                img.save(output_path, format=format.upper())
                return True
                
        except Exception as e:
            get_logger().error(f"转换图片格式失败: {e}")
            return False
    
    @staticmethod
    def compress_image(input_path: Union[str, Path], output_path: Union[str, Path],
                      quality: int = 85) -> bool:
        """
        压缩图片
        
        Args:
            input_path: 输入图片路径
            output_path: 输出图片路径
            quality: 压缩质量 (1-100)
            
        Returns:
            bool: 是否成功
        """
        if not PIL_AVAILABLE:
            get_logger().error("PIL未安装，无法压缩图片")
            return False
        
        try:
            with Image.open(input_path) as img:
                # 优化图片
                img = ImageOps.exif_transpose(img)
                
                # 保存时应用压缩
                save_kwargs = {'optimize': True}
                if img.format in ['JPEG', 'JPG']:
                    save_kwargs['quality'] = quality
                
                img.save(output_path, **save_kwargs)
                return True
                
        except Exception as e:
            get_logger().error(f"压缩图片失败: {e}")
            return False
    
    @staticmethod
    def encode_image_to_base64(image_path: Union[str, Path]) -> str:
        """
        将图片编码为base64
        
        Args:
            image_path: 图片路径
            
        Returns:
            str: base64编码的图片数据
        """
        try:
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
                base64_data = base64.b64encode(image_data).decode('utf-8')
                
                # 获取图片格式
                image_format = Path(image_path).suffix.lower().lstrip('.')
                if image_format == 'jpg':
                    image_format = 'jpeg'
                
                return f"data:image/{image_format};base64,{base64_data}"
                
        except Exception as e:
            get_logger().error(f"图片base64编码失败: {image_path}, 错误: {e}")
            return ""
    
    @staticmethod
    def create_thumbnail(input_path: Union[str, Path], output_path: Union[str, Path],
                        size: Tuple[int, int] = (128, 128)) -> bool:
        """
        创建缩略图
        
        Args:
            input_path: 输入图片路径
            output_path: 输出缩略图路径
            size: 缩略图尺寸
            
        Returns:
            bool: 是否成功
        """
        if not PIL_AVAILABLE:
            get_logger().error("PIL未安装，无法创建缩略图")
            return False
        
        try:
            with Image.open(input_path) as img:
                img.thumbnail(size, Image.Resampling.LANCZOS)
                img.save(output_path)
                return True
                
        except Exception as e:
            get_logger().error(f"创建缩略图失败: {e}")
            return False
    
    @staticmethod
    def get_dominant_colors(image_path: Union[str, Path], num_colors: int = 5) -> list:
        """
        获取图片主要颜色
        
        Args:
            image_path: 图片路径
            num_colors: 返回颜色数量
            
        Returns:
            list: 主要颜色列表
        """
        if not PIL_AVAILABLE:
            return []
        
        try:
            with Image.open(image_path) as img:
                # 转换为RGB模式
                img = img.convert('RGB')
                
                # 缩小图片以提高处理速度
                img.thumbnail((150, 150))
                
                # 获取颜色数据
                colors = img.getcolors(maxcolors=256*256*256)
                if not colors:
                    return []
                
                # 按频率排序并返回前N个颜色
                colors.sort(key=lambda x: x[0], reverse=True)
                return [color[1] for color in colors[:num_colors]]
                
        except Exception as e:
            get_logger().error(f"获取主要颜色失败: {e}")
            return []