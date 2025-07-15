"""
PPT转换工具
支持将PPT转换为PDF，然后转换为图片
"""

import os
import subprocess
import platform
from pathlib import Path
from typing import List, Optional
import logging

# 尝试导入PDF处理库
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


class PPTConverter:
    """PPT转换器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.system = platform.system()
        
    def convert_ppt_to_pdf_using_unoconv(self, ppt_path: str, pdf_path: str) -> bool:
        """使用unoconv转换PPT到PDF"""
        try:
            cmd = ['unoconv', '-f', 'pdf', '-o', pdf_path, ppt_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"使用unoconv成功转换为PDF: {pdf_path}")
                return True
            else:
                self.logger.error(f"unoconv转换失败: {result.stderr}")
                return False
        except FileNotFoundError:
            self.logger.error("未找到unoconv命令")
            return False
        except Exception as e:
            self.logger.error(f"unoconv转换异常: {e}")
            return False
    
    def convert_ppt_to_pdf_using_libreoffice(self, ppt_path: str, output_dir: str) -> Optional[str]:
        """使用LibreOffice转换PPT到PDF"""
        try:
            # 尝试不同的LibreOffice命令
            commands = [
                # LibreOffice with better options for Chinese text
                ['soffice', '--headless', '--infilter=impress_pdf_Export', '--convert-to', 'pdf:impress_pdf_Export', '--outdir', output_dir, ppt_path],
                ['libreoffice', '--headless', '--infilter=impress_pdf_Export', '--convert-to', 'pdf:impress_pdf_Export', '--outdir', output_dir, ppt_path],
                ['/Applications/LibreOffice.app/Contents/MacOS/soffice', '--headless', '--infilter=impress_pdf_Export', '--convert-to', 'pdf:impress_pdf_Export', '--outdir', output_dir, ppt_path],
                # 标准命令作为备选
                ['soffice', '--headless', '--convert-to', 'pdf', '--outdir', output_dir, ppt_path],
                ['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', output_dir, ppt_path],
                ['/Applications/LibreOffice.app/Contents/MacOS/soffice', '--headless', '--convert-to', 'pdf', '--outdir', output_dir, ppt_path],
                # 添加WPS Office支持
                ['/Applications/wpsoffice.app/Contents/MacOS/wps', '--headless', '--convert-to', 'pdf', '--outdir', output_dir, ppt_path],
                ['/Applications/wpsoffice.app/Contents/MacOS/et', '--headless', '--convert-to', 'pdf', ppt_path],
                ['/Applications/wpsoffice.app/Contents/MacOS/wpp', '--headless', '--convert-to', 'pdf', ppt_path]
            ]
            
            for cmd in commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        # 构建输出PDF路径
                        ppt_name = Path(ppt_path).stem
                        pdf_path = os.path.join(output_dir, f"{ppt_name}.pdf")
                        if os.path.exists(pdf_path):
                            self.logger.info(f"使用LibreOffice成功转换为PDF: {pdf_path}")
                            return pdf_path
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
                    
            self.logger.error("所有LibreOffice命令都失败了")
            return None
            
        except Exception as e:
            self.logger.error(f"LibreOffice转换异常: {e}")
            return None
    
    def convert_ppt_to_pdf_using_applescript(self, ppt_path: str, pdf_path: str) -> bool:
        """在macOS上使用AppleScript和Keynote/PowerPoint转换"""
        if self.system != "Darwin":
            return False
            
        try:
            # 尝试使用Keynote
            applescript = f'''
            tell application "Keynote"
                activate
                open POSIX file "{ppt_path}"
                delay 2
                export front document to POSIX file "{pdf_path}" as PDF
                close front document
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', applescript], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(pdf_path):
                self.logger.info(f"使用Keynote成功转换为PDF: {pdf_path}")
                return True
            
            # 如果Keynote失败，尝试PowerPoint
            applescript_ppt = f'''
            tell application "Microsoft PowerPoint"
                activate
                open POSIX file "{ppt_path}"
                delay 2
                save active presentation in POSIX file "{pdf_path}" as save as PDF
                close active presentation
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', applescript_ppt], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(pdf_path):
                self.logger.info(f"使用PowerPoint成功转换为PDF: {pdf_path}")
                return True
                
        except Exception as e:
            self.logger.error(f"AppleScript转换异常: {e}")
            
        return False
    
    def convert_ppt_to_pdf(self, ppt_path: str, output_dir: str) -> Optional[str]:
        """转换PPT到PDF，尝试多种方法"""
        ppt_path = os.path.abspath(ppt_path)
        output_dir = os.path.abspath(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        ppt_name = Path(ppt_path).stem
        pdf_path = os.path.join(output_dir, f"{ppt_name}.pdf")
        
        # 方法1: 尝试LibreOffice
        result = self.convert_ppt_to_pdf_using_libreoffice(ppt_path, output_dir)
        if result:
            return result
        
        # 方法2: 尝试unoconv
        if self.convert_ppt_to_pdf_using_unoconv(ppt_path, pdf_path):
            return pdf_path
        
        # 方法3: 在macOS上尝试AppleScript
        if self.system == "Darwin":
            if self.convert_ppt_to_pdf_using_applescript(ppt_path, pdf_path):
                return pdf_path
        
        self.logger.error("所有PPT转PDF方法都失败了")
        return None
    
    def convert_pdf_to_images(self, pdf_path: str, output_dir: str, dpi: int = 300) -> List[str]:
        """将PDF转换为图片"""
        os.makedirs(output_dir, exist_ok=True)
        image_paths = []
        
        # 优先使用PyMuPDF，因为它通常有更好的渲染质量
        if PYMUPDF_AVAILABLE:
            try:
                pdf_document = fitz.open(pdf_path)
                for i, page in enumerate(pdf_document):
                    # 使用更高质量的渲染设置
                    mat = fitz.Matrix(dpi/72, dpi/72)  # 设置DPI
                    pix = page.get_pixmap(matrix=mat, alpha=False)  # 不需要透明通道
                    image_path = os.path.join(output_dir, f"slide_{i+1:03d}.png")
                    pix.save(image_path)
                    image_paths.append(image_path)
                    self.logger.debug(f"生成图片: {image_path}")
                pdf_document.close()
                self.logger.info(f"使用PyMuPDF成功生成{len(image_paths)}张图片")
                return image_paths
            except Exception as e:
                self.logger.error(f"PyMuPDF转换失败: {e}")
        
        # 备选方案: 使用pdf2image
        if PDF2IMAGE_AVAILABLE:
            try:
                # 使用pdftocairo可能有更好的渲染效果
                images = convert_from_path(
                    pdf_path, 
                    dpi=dpi, 
                    fmt='png',
                    use_pdftocairo=True,  # 使用cairo渲染器
                    thread_count=1  # 单线程更稳定
                )
                for i, image in enumerate(images):
                    image_path = os.path.join(output_dir, f"slide_{i+1:03d}.png")
                    image.save(image_path, 'PNG', quality=95, optimize=True)
                    image_paths.append(image_path)
                    self.logger.debug(f"生成图片: {image_path}")
                self.logger.info(f"使用pdf2image成功生成{len(image_paths)}张图片")
                return image_paths
            except Exception as e:
                self.logger.error(f"pdf2image转换失败: {e}")
        
        self.logger.error("没有可用的PDF转图片库")
        return image_paths
    
    def convert_ppt_to_images(self, ppt_path: str, output_dir: str, dpi: int = 300) -> List[str]:
        """完整的PPT转图片流程"""
        # 创建临时目录
        temp_dir = os.path.join(output_dir, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        # 步骤1: PPT转PDF
        self.logger.info("步骤1: 转换PPT到PDF...")
        pdf_path = self.convert_ppt_to_pdf(ppt_path, temp_dir)
        if not pdf_path:
            self.logger.error("PPT转PDF失败")
            return []
        
        # 步骤2: PDF转图片
        self.logger.info("步骤2: 转换PDF到图片...")
        image_paths = self.convert_pdf_to_images(pdf_path, output_dir, dpi)
        
        # 清理临时文件
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except:
            pass
        
        self.logger.info(f"转换完成，生成了{len(image_paths)}张图片")
        return image_paths