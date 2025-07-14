"""
文件操作工具模块

提供文件和目录操作的通用功能。
"""

import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import List, Optional, Union, Tuple
import hashlib
import mimetypes

from ..config.constants import SUPPORTED_PPT_FORMATS, SUPPORTED_IMAGE_FORMATS, TEMP_DIR
from .logger import get_logger


class FileUtils:
    """文件操作工具类"""
    
    @staticmethod
    def ensure_dir(path: Union[str, Path]) -> bool:
        """
        确保目录存在
        
        Args:
            path: 目录路径
            
        Returns:
            bool: 是否成功
        """
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            get_logger().error(f"创建目录失败: {path}, 错误: {e}")
            return False
    
    @staticmethod
    def get_file_size(path: Union[str, Path]) -> int:
        """
        获取文件大小
        
        Args:
            path: 文件路径
            
        Returns:
            int: 文件大小（字节）
        """
        try:
            return Path(path).stat().st_size
        except Exception as e:
            get_logger().error(f"获取文件大小失败: {path}, 错误: {e}")
            return 0
    
    @staticmethod
    def get_file_hash(path: Union[str, Path], algorithm: str = 'md5') -> str:
        """
        计算文件哈希值
        
        Args:
            path: 文件路径
            algorithm: 哈希算法（md5, sha1, sha256）
            
        Returns:
            str: 哈希值
        """
        try:
            hash_obj = hashlib.new(algorithm)
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            get_logger().error(f"计算文件哈希失败: {path}, 错误: {e}")
            return ""
    
    @staticmethod
    def is_ppt_file(path: Union[str, Path]) -> bool:
        """
        检查是否为PPT文件
        
        Args:
            path: 文件路径
            
        Returns:
            bool: 是否为PPT文件
        """
        try:
            suffix = Path(path).suffix.lower()
            return suffix in SUPPORTED_PPT_FORMATS
        except Exception:
            return False
    
    @staticmethod
    def is_image_file(path: Union[str, Path]) -> bool:
        """
        检查是否为图片文件
        
        Args:
            path: 文件路径
            
        Returns:
            bool: 是否为图片文件
        """
        try:
            suffix = Path(path).suffix.lower()
            return suffix in SUPPORTED_IMAGE_FORMATS
        except Exception:
            return False
    
    @staticmethod
    def get_file_info(path: Union[str, Path]) -> dict:
        """
        获取文件信息
        
        Args:
            path: 文件路径
            
        Returns:
            dict: 文件信息
        """
        try:
            file_path = Path(path)
            stat = file_path.stat()
            
            return {
                'name': file_path.name,
                'stem': file_path.stem,
                'suffix': file_path.suffix,
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'is_file': file_path.is_file(),
                'is_dir': file_path.is_dir(),
                'exists': file_path.exists(),
                'mime_type': mimetypes.guess_type(str(file_path))[0]
            }
        except Exception as e:
            get_logger().error(f"获取文件信息失败: {path}, 错误: {e}")
            return {}
    
    @staticmethod
    def create_temp_dir(prefix: str = "ppt_lecture_") -> str:
        """
        创建临时目录
        
        Args:
            prefix: 目录前缀
            
        Returns:
            str: 临时目录路径
        """
        try:
            temp_dir = tempfile.mkdtemp(prefix=prefix, dir=TEMP_DIR)
            get_logger().debug(f"创建临时目录: {temp_dir}")
            return temp_dir
        except Exception as e:
            get_logger().error(f"创建临时目录失败: {e}")
            return ""
    
    @staticmethod
    def clean_temp_dir(temp_dir: str) -> bool:
        """
        清理临时目录
        
        Args:
            temp_dir: 临时目录路径
            
        Returns:
            bool: 是否成功
        """
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                get_logger().debug(f"清理临时目录: {temp_dir}")
            return True
        except Exception as e:
            get_logger().error(f"清理临时目录失败: {temp_dir}, 错误: {e}")
            return False
    
    @staticmethod
    def copy_file(src: Union[str, Path], dst: Union[str, Path]) -> bool:
        """
        复制文件
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            # 确保目标目录存在
            FileUtils.ensure_dir(Path(dst).parent)
            
            shutil.copy2(src, dst)
            get_logger().debug(f"复制文件: {src} -> {dst}")
            return True
        except Exception as e:
            get_logger().error(f"复制文件失败: {src} -> {dst}, 错误: {e}")
            return False
    
    @staticmethod
    def move_file(src: Union[str, Path], dst: Union[str, Path]) -> bool:
        """
        移动文件
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            # 确保目标目录存在
            FileUtils.ensure_dir(Path(dst).parent)
            
            shutil.move(src, dst)
            get_logger().debug(f"移动文件: {src} -> {dst}")
            return True
        except Exception as e:
            get_logger().error(f"移动文件失败: {src} -> {dst}, 错误: {e}")
            return False
    
    @staticmethod
    def delete_file(path: Union[str, Path]) -> bool:
        """
        删除文件
        
        Args:
            path: 文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            file_path = Path(path)
            if file_path.exists():
                if file_path.is_file():
                    file_path.unlink()
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
                get_logger().debug(f"删除文件: {path}")
            return True
        except Exception as e:
            get_logger().error(f"删除文件失败: {path}, 错误: {e}")
            return False
    
    @staticmethod
    def find_files(directory: Union[str, Path], pattern: str = "*", 
                   recursive: bool = True) -> List[Path]:
        """
        查找文件
        
        Args:
            directory: 搜索目录
            pattern: 匹配模式
            recursive: 是否递归搜索
            
        Returns:
            List[Path]: 匹配的文件列表
        """
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                return []
            
            if recursive:
                return list(dir_path.rglob(pattern))
            else:
                return list(dir_path.glob(pattern))
        except Exception as e:
            get_logger().error(f"查找文件失败: {directory}, 错误: {e}")
            return []
    
    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """
        获取安全的文件名（移除特殊字符）
        
        Args:
            filename: 原始文件名
            
        Returns:
            str: 安全的文件名
        """
        # 移除或替换不安全的字符
        import re
        safe_chars = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # 移除多余的空格和点
        safe_chars = re.sub(r'[\s.]+', '_', safe_chars)
        
        # 确保不为空
        if not safe_chars:
            safe_chars = "unnamed_file"
        
        return safe_chars
    
    @staticmethod
    def get_unique_filename(directory: Union[str, Path], 
                           filename: str) -> str:
        """
        获取唯一的文件名（避免重复）
        
        Args:
            directory: 目录路径
            filename: 原始文件名
            
        Returns:
            str: 唯一的文件名
        """
        try:
            dir_path = Path(directory)
            file_path = dir_path / filename
            
            if not file_path.exists():
                return filename
            
            # 分离文件名和扩展名
            stem = file_path.stem
            suffix = file_path.suffix
            
            # 添加数字后缀
            counter = 1
            while file_path.exists():
                new_name = f"{stem}_{counter}{suffix}"
                file_path = dir_path / new_name
                counter += 1
            
            return file_path.name
        except Exception as e:
            get_logger().error(f"获取唯一文件名失败: {filename}, 错误: {e}")
            return filename
    
    @staticmethod
    def read_text_file(path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """
        读取文本文件
        
        Args:
            path: 文件路径
            encoding: 编码格式
            
        Returns:
            str: 文件内容
        """
        try:
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        except Exception as e:
            get_logger().error(f"读取文本文件失败: {path}, 错误: {e}")
            return ""
    
    @staticmethod
    def write_text_file(path: Union[str, Path], content: str, 
                       encoding: str = 'utf-8') -> bool:
        """
        写入文本文件
        
        Args:
            path: 文件路径
            content: 文件内容
            encoding: 编码格式
            
        Returns:
            bool: 是否成功
        """
        try:
            # 确保目录存在
            FileUtils.ensure_dir(Path(path).parent)
            
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
            return True
        except Exception as e:
            get_logger().error(f"写入文本文件失败: {path}, 错误: {e}")
            return False
    
    @staticmethod
    def compress_files(files: List[Union[str, Path]], 
                      output_path: Union[str, Path]) -> bool:
        """
        压缩文件
        
        Args:
            files: 要压缩的文件列表
            output_path: 输出ZIP文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_path in files:
                    file_path = Path(file_path)
                    if file_path.exists():
                        zf.write(file_path, file_path.name)
            
            get_logger().info(f"压缩文件完成: {output_path}")
            return True
        except Exception as e:
            get_logger().error(f"压缩文件失败: {output_path}, 错误: {e}")
            return False
    
    @staticmethod
    def extract_zip(zip_path: Union[str, Path], 
                   extract_to: Union[str, Path]) -> bool:
        """
        解压ZIP文件
        
        Args:
            zip_path: ZIP文件路径
            extract_to: 解压目录
            
        Returns:
            bool: 是否成功
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(extract_to)
            
            get_logger().info(f"解压文件完成: {zip_path} -> {extract_to}")
            return True
        except Exception as e:
            get_logger().error(f"解压文件失败: {zip_path}, 错误: {e}")
            return False