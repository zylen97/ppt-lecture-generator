"""
讲稿生成模块

整合PPT处理、AI分析和上下文管理，生成完整的课程讲稿。
"""

import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Callable
from pathlib import Path
import json

from .ppt_processor import PPTProcessor, SlideInfo
from .ai_client import AIClient, APIResponse
from .context_manager import ContextManager
from ..utils.logger import get_logger
from ..utils.file_utils import FileUtils
from ..config.constants import LECTURE_GENERATION


class ScriptGenerator:
    """讲稿生成器"""
    
    def __init__(self, api_key: str, api_base: str = "https://api.openai.com/v1", 
                 model: str = "gpt-4-vision-preview"):
        """
        初始化讲稿生成器
        
        Args:
            api_key: API密钥
            api_base: API基础URL
            model: 使用的模型
        """
        self.logger = get_logger()
        
        # 初始化组件
        self.ai_client = AIClient(api_key, api_base, model)
        self.context_manager = ContextManager()
        self.ppt_processor: Optional[PPTProcessor] = None
        
        # 生成配置
        self.generation_config = {
            'total_duration': LECTURE_GENERATION['default_duration'],
            'include_interaction': True,
            'include_examples': True,
            'language': 'zh-CN',
            'style': 'academic'
        }
        
        # 进度回调
        self.progress_callback: Optional[Callable[[int, int, str], None]] = None
        
        # 生成结果
        self.generated_scripts: List[Dict[str, Any]] = []
        self.generation_stats: Dict[str, Any] = {}
        
        self.logger.info("初始化讲稿生成器")
    
    def set_progress_callback(self, callback: Callable[[int, int, str], None]):
        """
        设置进度回调函数
        
        Args:
            callback: 进度回调函数 (current, total, message)
        """
        self.progress_callback = callback
    
    def set_generation_config(self, config: Dict[str, Any]):
        """
        设置生成配置
        
        Args:
            config: 配置字典
        """
        self.generation_config.update(config)
        self.logger.info(f"更新生成配置: {config}")
    
    def generate_from_ppt(self, ppt_path: str, output_path: str = None) -> Tuple[bool, str]:
        """
        从PPT文件生成讲稿
        
        Args:
            ppt_path: PPT文件路径
            output_path: 输出文件路径
            
        Returns:
            Tuple[bool, str]: (是否成功, 结果信息)
        """
        try:
            start_time = time.time()
            
            # 步骤1: 处理PPT文件
            self._report_progress(0, 100, "正在处理PPT文件...")
            
            if not self._process_ppt_file(ppt_path):
                return False, "PPT文件处理失败"
            
            # 步骤2: 初始化上下文
            self._report_progress(20, 100, "正在初始化上下文...")
            
            ppt_info = self.ppt_processor.get_presentation_info()
            course_title = Path(ppt_path).stem
            
            self.context_manager.initialize_course(
                course_title=course_title,
                total_slides=ppt_info['slide_count'],
                total_duration=self.generation_config['total_duration']
            )
            
            # 步骤3: 批量分析幻灯片
            self._report_progress(30, 100, "正在分析幻灯片内容...")
            
            if not self._analyze_all_slides():
                return False, "幻灯片分析失败"
            
            # 步骤4: 生成讲稿
            self._report_progress(60, 100, "正在生成讲稿...")
            
            if not self._generate_all_scripts():
                return False, "讲稿生成失败"
            
            # 步骤5: 整合并输出
            self._report_progress(90, 100, "正在整合讲稿...")
            
            final_script = self._integrate_scripts()
            
            # 保存结果
            if output_path:
                output_file = output_path
            else:
                output_file = self._get_default_output_path(ppt_path)
            
            if not FileUtils.write_text_file(output_file, final_script):
                return False, "保存讲稿失败"
            
            # 记录统计信息
            self.generation_stats = {
                'total_time': time.time() - start_time,
                'total_slides': len(self.generated_scripts),
                'total_length': len(final_script),
                'output_file': output_file,
                'generation_time': datetime.now().isoformat()
            }
            
            self._report_progress(100, 100, "讲稿生成完成!")
            
            self.logger.info(f"讲稿生成完成: {output_file}")
            return True, output_file
            
        except Exception as e:
            self.logger.error(f"讲稿生成失败: {e}")
            return False, str(e)
        
        finally:
            # 清理资源
            if self.ppt_processor:
                self.ppt_processor.cleanup()
    
    def _process_ppt_file(self, ppt_path: str) -> bool:
        """
        处理PPT文件
        
        Args:
            ppt_path: PPT文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            self.ppt_processor = PPTProcessor(ppt_path)
            return self.ppt_processor.process()
        except Exception as e:
            self.logger.error(f"PPT处理失败: {e}")
            return False
    
    def _analyze_all_slides(self) -> bool:
        """
        分析所有幻灯片
        
        Returns:
            bool: 是否成功
        """
        try:
            slides_info = self.ppt_processor.get_all_slides_info()
            total_slides = len(slides_info)
            
            for i, slide_info in enumerate(slides_info):
                self._report_progress(
                    30 + (i * 30) // total_slides,
                    100,
                    f"正在分析第{slide_info.slide_number}张幻灯片..."
                )
                
                # 获取前文上下文
                context = self.context_manager.get_previous_context(slide_info.slide_number)
                
                # 分析幻灯片
                if slide_info.image_path:
                    # 使用图片分析
                    response = self.ai_client.analyze_slide_image(slide_info.image_path, context)
                else:
                    # 使用文本分析
                    response = self._analyze_slide_text(slide_info, context)
                
                if not response.success:
                    self.logger.error(f"分析幻灯片{slide_info.slide_number}失败: {response.error_message}")
                    continue
                
                # 添加到上下文
                self.context_manager.add_slide_context(
                    slide_number=slide_info.slide_number,
                    title=slide_info.title,
                    content=self._format_slide_content(slide_info),
                    analysis_result=response.content
                )
                
                # 添加延迟避免频率限制
                time.sleep(0.5)
            
            return True
            
        except Exception as e:
            self.logger.error(f"分析幻灯片失败: {e}")
            return False
    
    def _analyze_slide_text(self, slide_info: SlideInfo, context: str) -> APIResponse:
        """
        分析幻灯片文本内容
        
        Args:
            slide_info: 幻灯片信息
            context: 上下文
            
        Returns:
            APIResponse: 分析结果
        """
        # 构建文本分析消息
        content_text = self._format_slide_content(slide_info)
        
        prompt = f"""请分析以下幻灯片内容，提供详细的教学分析：

幻灯片标题: {slide_info.title}
幻灯片内容: {content_text}

请提供：
1. 标题：核心主题
2. 要点：主要知识点
3. 概念：关键概念和术语
4. 重点：教学重点和难点
5. 建议：教学建议

上下文信息：
{context}
"""
        
        return self.ai_client.generate_script(prompt, "", 0)
    
    def _generate_all_scripts(self) -> bool:
        """
        生成所有讲稿
        
        Returns:
            bool: 是否成功
        """
        try:
            slides_info = self.ppt_processor.get_all_slides_info()
            total_slides = len(slides_info)
            
            for i, slide_info in enumerate(slides_info):
                self._report_progress(
                    60 + (i * 25) // total_slides,
                    100,
                    f"正在生成第{slide_info.slide_number}张幻灯片讲稿..."
                )
                
                # 获取教学建议
                suggestions = self.context_manager.get_teaching_suggestions(slide_info.slide_number)
                
                # 计算时间分配
                duration = suggestions['time_allocation']['suggested_time']
                
                # 获取前文上下文
                context = self.context_manager.get_previous_context(slide_info.slide_number)
                
                # 构建幻灯片内容
                slide_content = self._build_slide_content_for_generation(slide_info, suggestions)
                
                # 生成讲稿
                response = self.ai_client.generate_script(slide_content, context, duration)
                
                if not response.success:
                    self.logger.error(f"生成讲稿{slide_info.slide_number}失败: {response.error_message}")
                    continue
                
                # 更新上下文
                self.context_manager.update_slide_script(slide_info.slide_number, response.content)
                
                # 保存生成结果
                script_data = {
                    'slide_number': slide_info.slide_number,
                    'title': slide_info.title,
                    'duration': duration,
                    'content': response.content,
                    'suggestions': suggestions,
                    'usage': response.usage,
                    'response_time': response.response_time
                }
                
                self.generated_scripts.append(script_data)
                
                # 添加延迟
                time.sleep(0.5)
            
            return True
            
        except Exception as e:
            self.logger.error(f"生成讲稿失败: {e}")
            return False
    
    def _build_slide_content_for_generation(self, slide_info: SlideInfo, 
                                          suggestions: Dict[str, Any]) -> str:
        """
        构建用于生成的幻灯片内容
        
        Args:
            slide_info: 幻灯片信息
            suggestions: 教学建议
            
        Returns:
            str: 格式化的内容
        """
        content_parts = []
        
        # 基本信息
        content_parts.append(f"幻灯片标题: {slide_info.title}")
        content_parts.append(f"幻灯片类型: {slide_info.slide_type}")
        content_parts.append(f"建议时长: {suggestions['time_allocation']['suggested_time']}分钟")
        content_parts.append(f"难度级别: {suggestions['difficulty_level']}")
        
        # 内容要点
        if slide_info.content:
            content_parts.append("\\n主要内容:")
            for content in slide_info.content:
                content_parts.append(f"- {content}")
        
        # 项目符号
        if slide_info.bullet_points:
            content_parts.append("\\n要点:")
            for point in slide_info.bullet_points:
                indent = "  " * point['level']
                content_parts.append(f"{indent}- {point['text']}")
        
        # 多媒体元素
        if slide_info.image_count > 0:
            content_parts.append(f"\\n包含{slide_info.image_count}张图片")
        
        if slide_info.chart_count > 0:
            content_parts.append(f"包含{slide_info.chart_count}个图表")
        
        if slide_info.table_count > 0:
            content_parts.append(f"包含{slide_info.table_count}个表格")
        
        # 教学建议
        if suggestions['interaction_needed']:
            content_parts.append("\\n需要安排互动环节")
        
        if suggestions['example_needed']:
            content_parts.append("需要提供具体例子")
        
        if suggestions['connection_points']:
            content_parts.append("\\n关联点:")
            for connection in suggestions['connection_points']:
                content_parts.append(f"- {connection}")
        
        # 备注
        if slide_info.notes:
            content_parts.append(f"\\n备注: {slide_info.notes}")
        
        return "\\n".join(content_parts)
    
    def _integrate_scripts(self) -> str:
        """
        整合所有讲稿
        
        Returns:
            str: 完整讲稿
        """
        script_parts = []
        
        # 添加标题和概览
        course_info = self.context_manager.get_course_summary()
        
        script_parts.append(f"# {course_info['course_info']['course_title']} - 课程讲稿")
        script_parts.append("")
        script_parts.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        script_parts.append(f"**课程时长**: {course_info['course_info']['total_duration']}分钟")
        script_parts.append(f"**幻灯片数量**: {course_info['course_info']['total_slides']}张")
        script_parts.append(f"**涉及概念**: {course_info['total_concepts']}个")
        script_parts.append("")
        script_parts.append("---")
        script_parts.append("")
        
        # 添加课程大纲
        script_parts.append("## 📋 课程大纲")
        script_parts.append("")
        
        cumulative_time = 0
        for script_data in self.generated_scripts:
            slide_num = script_data['slide_number']
            title = script_data['title']
            duration = script_data['duration']
            
            script_parts.append(f"{slide_num}. **{title}** ({duration}分钟) - {cumulative_time}~{cumulative_time + duration}分钟")
            cumulative_time += duration
        
        script_parts.append("")
        script_parts.append("---")
        script_parts.append("")
        
        # 添加详细讲稿
        script_parts.append("## 📖 详细讲稿")
        script_parts.append("")
        
        for script_data in self.generated_scripts:
            slide_num = script_data['slide_number']
            title = script_data['title']
            duration = script_data['duration']
            content = script_data['content']
            
            script_parts.append(f"### 第{slide_num}张 - {title}")
            script_parts.append(f"**建议时长**: {duration}分钟")
            script_parts.append("")
            script_parts.append(content)
            script_parts.append("")
            script_parts.append("---")
            script_parts.append("")
        
        # 添加教学建议
        script_parts.append("## 💡 教学建议")
        script_parts.append("")
        script_parts.append("### 课前准备")
        script_parts.append("- 提前15分钟到达教室，检查设备")
        script_parts.append("- 准备好相关案例和补充材料")
        script_parts.append("- 熟悉讲稿内容，预演关键部分")
        script_parts.append("")
        script_parts.append("### 课堂管理")
        script_parts.append("- 注意观察学生反应，适时调整节奏")
        script_parts.append("- 鼓励学生提问和参与讨论")
        script_parts.append("- 合理分配时间，预留答疑时间")
        script_parts.append("")
        script_parts.append("### 课后跟进")
        script_parts.append("- 收集学生反馈，改进教学内容")
        script_parts.append("- 布置相关作业或阅读材料")
        script_parts.append("- 预告下节课内容")
        script_parts.append("")
        
        # 添加统计信息
        if self.generation_stats:
            script_parts.append("## 📊 生成统计")
            script_parts.append("")
            script_parts.append(f"- 总耗时: {self.generation_stats['total_time']:.1f}秒")
            script_parts.append(f"- 处理幻灯片: {self.generation_stats['total_slides']}张")
            script_parts.append(f"- 讲稿长度: {self.generation_stats['total_length']:,}字符")
            script_parts.append(f"- 生成时间: {self.generation_stats['generation_time']}")
        
        return "\\n".join(script_parts)
    
    def _format_slide_content(self, slide_info: SlideInfo) -> str:
        """
        格式化幻灯片内容
        
        Args:
            slide_info: 幻灯片信息
            
        Returns:
            str: 格式化的内容
        """
        content_parts = []
        
        if slide_info.content:
            content_parts.extend(slide_info.content)
        
        if slide_info.bullet_points:
            for point in slide_info.bullet_points:
                indent = "  " * point['level']
                content_parts.append(f"{indent}- {point['text']}")
        
        return "\\n".join(content_parts)
    
    def _get_default_output_path(self, ppt_path: str) -> str:
        """
        获取默认输出路径
        
        Args:
            ppt_path: PPT文件路径
            
        Returns:
            str: 输出路径
        """
        ppt_file = Path(ppt_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"{ppt_file.stem}_讲稿_{timestamp}.md"
        return str(ppt_file.parent / output_name)
    
    def _report_progress(self, current: int, total: int, message: str):
        """
        报告进度
        
        Args:
            current: 当前进度
            total: 总进度
            message: 进度消息
        """
        if self.progress_callback:
            self.progress_callback(current, total, message)
        
        self.logger.info(f"进度 {current}/{total}: {message}")
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """
        获取生成统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return self.generation_stats.copy()
    
    def export_results(self, output_dir: str) -> bool:
        """
        导出生成结果
        
        Args:
            output_dir: 输出目录
            
        Returns:
            bool: 是否成功
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 导出讲稿脚本
            scripts_file = output_path / "scripts.json"
            with open(scripts_file, 'w', encoding='utf-8') as f:
                json.dump(self.generated_scripts, f, ensure_ascii=False, indent=2)
            
            # 导出上下文信息
            context_file = output_path / "context.json"
            self.context_manager.export_context(str(context_file))
            
            # 导出统计信息
            stats_file = output_path / "stats.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.generation_stats, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"导出结果完成: {output_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出结果失败: {e}")
            return False
    
    def cleanup(self):
        """清理资源"""
        if self.ppt_processor:
            self.ppt_processor.cleanup()
        
        if self.ai_client:
            self.ai_client.close()
        
        self.context_manager.clear_context()
        
        self.logger.info("资源清理完成")