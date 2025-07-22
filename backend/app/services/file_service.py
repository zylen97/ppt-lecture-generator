"""
文件服务
"""

from pathlib import Path
import zipfile
from typing import Optional


class FileService:
    """文件处理服务"""
    
    @staticmethod
    def get_slide_count(file_path: Path) -> int:
        """
        获取PPT文件的幻灯片数量
        """
        try:
            file_path = Path(file_path)
            
            if file_path.suffix.lower() == '.pptx':
                # PPTX是ZIP格式，可以直接读取
                with zipfile.ZipFile(file_path, 'r') as pptx:
                    # 计算slide文件数量
                    slide_files = [name for name in pptx.namelist() 
                                 if name.startswith('ppt/slides/slide') and name.endswith('.xml')]
                    return len(slide_files)
            
            elif file_path.suffix.lower() == '.ppt':
                # 对于旧格式的PPT，返回0或者使用其他方法
                # 这里需要更复杂的处理，可能需要使用python-pptx或其他库
                return 0
                
        except Exception as e:
            print(f"获取幻灯片数量失败: {e}")
            return 0
        
        return 0
    
    @staticmethod
    def validate_ppt_file(file_path: Path) -> tuple[bool, str]:
        """
        验证PPT文件是否有效
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return False, "文件不存在"
            
            if file_path.suffix.lower() not in ['.ppt', '.pptx']:
                return False, "不支持的文件格式"
            
            # 检查文件是否损坏
            if file_path.suffix.lower() == '.pptx':
                try:
                    with zipfile.ZipFile(file_path, 'r') as pptx:
                        # 验证ZIP文件完整性
                        bad_files = pptx.testzip()
                        if bad_files:
                            return False, f"文件损坏: {bad_files}"
                except zipfile.BadZipFile:
                    return False, "文件格式损坏"
            
            return True, "文件验证通过"
            
        except Exception as e:
            return False, f"文件验证失败: {str(e)}"
    
    @staticmethod
    def get_file_info(file_path: Path) -> dict:
        """
        获取文件详细信息
        """
        try:
            file_path = Path(file_path)
            
            info = {
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "extension": file_path.suffix.lower(),
                "slide_count": 0,
                "is_valid": False
            }
            
            # 验证文件
            is_valid, message = FileService.validate_ppt_file(file_path)
            info["is_valid"] = is_valid
            info["validation_message"] = message
            
            if is_valid:
                info["slide_count"] = FileService.get_slide_count(file_path)
            
            return info
            
        except Exception as e:
            return {
                "error": f"获取文件信息失败: {str(e)}"
            }