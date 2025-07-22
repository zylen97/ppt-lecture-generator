"""
讲稿生成模块 - Web版本

整合PPT处理、AI分析和上下文管理，生成完整的课程讲稿。
"""

import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Callable
from pathlib import Path
import json
import logging

from .ppt_processor import PPTProcessor, SlideInfo
from .ai_client import AIClient, APIResponse


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
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.ai_client = AIClient(api_key, api_base, model)
        self.ppt_processor: Optional[PPTProcessor] = None
        
        # 生成配置
        self.generation_config = {
            'total_duration': 90,  # 默认90分钟
            'include_interaction': False,  # 禁用互动
            'include_examples': True,
            'language': 'zh-CN',
            'style': 'lecture_only',  # 纯讲授模式
            'no_questions': True,  # 不包含提问
            'no_blackboard': True  # 不包含板书
        }
        
        # 进度回调
        self.progress_callback: Optional[Callable[[int, int, str], None]] = None
        
        # 统计信息
        self.stats = {
            'start_time': 0,
            'total_time': 0,
            'total_slides': 0,
            'successful_analyses': 0,
            'failed_analyses': 0,
            'total_tokens': 0,
            'total_length': 0
        }
        
        self.logger.info("讲稿生成器初始化完成")
    
    def set_generation_config(self, config: Dict[str, Any]):
        """设置生成配置"""
        self.generation_config.update(config)
        self.logger.info(f"更新生成配置: {config}")
    
    def set_progress_callback(self, callback: Callable[[int, int, str], None]):
        """设置进度回调函数"""
        self.progress_callback = callback
    
    def _update_progress(self, current: int, total: int, message: str):
        """更新进度"""
        if self.progress_callback:
            self.progress_callback(current, total, message)
    
    def generate_from_ppt(self, ppt_path: str, output_path: str = None) -> Tuple[bool, str]:
        """
        从PPT生成讲稿
        
        Args:
            ppt_path: PPT文件路径
            output_path: 输出文件路径（可选）
            
        Returns:
            Tuple[bool, str]: (是否成功, 结果信息或错误信息)
        """
        try:
            self.stats['start_time'] = time.time()
            self._update_progress(0, 100, "开始处理PPT文件")
            
            # 1. 初始化PPT处理器
            self.ppt_processor = PPTProcessor(ppt_path)
            self.stats['total_slides'] = 0
            
            # 2. 处理PPT文件
            self._update_progress(10, 100, "解析PPT文件结构")
            if not self.ppt_processor.process():
                return False, "PPT文件处理失败"
            
            slides_info = self.ppt_processor.get_slides_info()
            self.stats['total_slides'] = len(slides_info)
            
            if not slides_info:
                return False, "未找到有效的幻灯片内容"
            
            # 3. 分析幻灯片内容
            self._update_progress(30, 100, "分析幻灯片内容")
            analysis_results = self._analyze_slides(slides_info)
            
            # 4. 生成讲稿
            self._update_progress(70, 100, "生成讲稿内容")
            script_content = self._generate_complete_script(analysis_results, slides_info)
            
            # 5. 保存讲稿
            if output_path:
                self._update_progress(90, 100, "保存讲稿文件")
                self._save_script(script_content, output_path)
            
            # 更新统计信息
            self.stats['total_time'] = time.time() - self.stats['start_time']
            self.stats['total_length'] = len(script_content)
            
            self._update_progress(100, 100, "讲稿生成完成")
            
            if output_path:
                return True, output_path
            else:
                return True, script_content
                
        except Exception as e:
            self.logger.error(f"讲稿生成失败: {e}")
            return False, str(e)
        
        finally:
            # 清理资源
            if self.ppt_processor:
                self.ppt_processor.cleanup()
    
    def _analyze_slides(self, slides_info: List[SlideInfo]) -> List[Dict[str, Any]]:
        """分析幻灯片内容"""
        analysis_results = []
        total_slides = len(slides_info)
        
        for i, slide in enumerate(slides_info):
            try:
                self._update_progress(
                    30 + int(40 * i / total_slides), 100,
                    f"分析第{i+1}张幻灯片"
                )
                
                # 如果有图片，使用视觉分析
                if slide.image_path and Path(slide.image_path).exists():
                    context = self._build_context(analysis_results[-3:] if len(analysis_results) >= 3 else analysis_results)
                    response = self.ai_client.analyze_slide_image(slide.image_path, context)
                    
                    if response.success:
                        analysis_result = {
                            'slide_number': slide.slide_number,
                            'ai_analysis': response.content,
                            'extracted_text': slide.content,
                            'title': slide.title,
                            'slide_type': slide.slide_type,
                            'usage': response.usage
                        }
                        self.stats['successful_analyses'] += 1
                        if response.usage:
                            self.stats['total_tokens'] += response.usage.get('total_tokens', 0)
                    else:
                        # AI分析失败，使用文本内容
                        analysis_result = {
                            'slide_number': slide.slide_number,
                            'ai_analysis': "",
                            'extracted_text': slide.content,
                            'title': slide.title,
                            'slide_type': slide.slide_type,
                            'error': response.error_message
                        }
                        self.stats['failed_analyses'] += 1
                else:
                    # 没有图片，仅使用文本内容
                    analysis_result = {
                        'slide_number': slide.slide_number,
                        'ai_analysis': "",
                        'extracted_text': slide.content,
                        'title': slide.title,
                        'slide_type': slide.slide_type
                    }
                
                analysis_results.append(analysis_result)
                
            except Exception as e:
                self.logger.error(f"分析第{i+1}张幻灯片失败: {e}")
                analysis_results.append({
                    'slide_number': slide.slide_number,
                    'ai_analysis': "",
                    'extracted_text': slide.content,
                    'title': slide.title,
                    'slide_type': slide.slide_type,
                    'error': str(e)
                })
                self.stats['failed_analyses'] += 1
        
        return analysis_results
    
    def _build_context(self, previous_results: List[Dict[str, Any]]) -> str:
        """构建上下文信息"""
        context_parts = []
        
        for result in previous_results:
            title = result.get('title', '')
            content = result.get('ai_analysis') or ' '.join(result.get('extracted_text', []))
            
            if title or content:
                context_parts.append(f"第{result['slide_number']}张: {title}\n{content[:200]}...")
        
        return '\n\n'.join(context_parts)
    
    def _generate_complete_script(self, analysis_results: List[Dict[str, Any]], 
                                slides_info: List[SlideInfo]) -> str:
        """生成完整讲稿"""
        try:
            # 计算每张幻灯片的建议时长
            time_per_slide = self.generation_config['total_duration'] / len(slides_info)
            
            # 构建讲稿各部分
            script_parts = []
            
            # 1. 讲稿头部信息
            header = self._generate_script_header(slides_info[0] if slides_info else None)
            script_parts.append(header)
            
            # 2. 内容导航
            navigation = self._generate_content_navigation(analysis_results)
            script_parts.append(navigation)
            
            # 3. 逐张幻灯片的讲稿
            for i, result in enumerate(analysis_results):
                try:
                    # 构建幻灯片内容
                    slide_content = self._build_slide_content(result)
                    
                    # 构建上下文
                    context = self._build_context(analysis_results[:i])
                    
                    # 生成这张幻灯片的讲稿
                    response = self.ai_client.generate_script(
                        slide_content=slide_content,
                        context=context,
                        duration=max(1, int(time_per_slide)),
                        target_audience=self.generation_config.get('target_audience', 'undergraduate')
                    )
                    
                    if response.success:
                        slide_script = f"\n## 第{result['slide_number']}张 - {result.get('title', '无标题')}\n\n"
                        slide_script += response.content
                        script_parts.append(slide_script)
                        
                        if response.usage:
                            self.stats['total_tokens'] += response.usage.get('total_tokens', 0)
                    else:
                        # 生成失败，使用简单模板
                        slide_script = self._generate_fallback_script(result, time_per_slide)
                        script_parts.append(slide_script)
                        
                except Exception as e:
                    self.logger.error(f"生成第{result['slide_number']}张讲稿失败: {e}")
                    # 使用简单模板
                    slide_script = self._generate_fallback_script(result, time_per_slide)
                    script_parts.append(slide_script)
            
            # 4. 讲稿结尾
            footer = self._generate_script_footer()
            script_parts.append(footer)
            
            return '\n\n'.join(script_parts)
            
        except Exception as e:
            self.logger.error(f"生成完整讲稿失败: {e}")
            raise
    
    def _generate_script_header(self, first_slide: Optional[SlideInfo]) -> str:
        """生成讲稿头部"""
        title = first_slide.title if first_slide else "课程讲稿"
        timestamp = datetime.now().strftime("%Y年%m月%d日")
        
        return f"""# {title}

> 🎓 **教师提示**
> - 📖 **准备**: 提前预览本节内容，准备相关材料
> - ⏱️ **时间**: 注意把控各环节时间，确保教学节奏
> - 💡 **重点**: 关注⭐标记的重点内容
> - 📢 **讲解**: 纯讲授模式，连贯流畅地进行知识传授

**生成时间**: {timestamp}  
**预计时长**: {self.generation_config['total_duration']}分钟  
**幻灯片数量**: {self.stats['total_slides']}张"""
    
    def _generate_content_navigation(self, analysis_results: List[Dict[str, Any]]) -> str:
        """生成内容导航"""
        nav_items = []
        for result in analysis_results:
            title = result.get('title', f"第{result['slide_number']}张")
            nav_items.append(f"{result['slide_number']}. {title}")
        
        navigation = "## 📋 内容导航\n\n"
        navigation += '\n'.join(nav_items)
        return navigation
    
    def _build_slide_content(self, result: Dict[str, Any]) -> str:
        """构建幻灯片内容描述"""
        content_parts = []
        
        if result.get('title'):
            content_parts.append(f"标题：{result['title']}")
        
        if result.get('ai_analysis'):
            content_parts.append(f"内容分析：{result['ai_analysis']}")
        
        if result.get('extracted_text'):
            text_content = ' '.join(result['extracted_text'])
            if text_content:
                content_parts.append(f"文本内容：{text_content}")
        
        return '\n\n'.join(content_parts)
    
    def _generate_fallback_script(self, result: Dict[str, Any], duration: float) -> str:
        """生成备用讲稿（当AI生成失败时）"""
        title = result.get('title', '无标题')
        content = result.get('extracted_text', [])
        
        script = f"\n## 第{result['slide_number']}张 - {title}\n\n"
        script += f"### 🎯 内容概述：\n\n"
        
        if content:
            for item in content:
                script += f"- {item}\n"
        else:
            script += "（此幻灯片内容需要根据实际展示进行讲解）\n"
        
        script += f"\n⏱️ **建议讲解时长**: {duration:.0f}分钟\n"
        
        return script
    
    def _generate_script_footer(self) -> str:
        """生成讲稿结尾"""
        return """
---

## 📝 讲稿总结

本次课程内容到此结束，感谢大家的学习。

**重要提醒**：
- 请大家复习今天的重点内容
- 有疑问可以课后交流
- 下节课我们将继续学习相关内容

---
*本讲稿由PPT讲稿生成器自动生成*"""
    
    def _save_script(self, content: str, output_path: str):
        """保存讲稿到文件"""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"讲稿已保存: {output_path}")
            
        except Exception as e:
            self.logger.error(f"保存讲稿失败: {e}")
            raise
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """获取生成统计信息"""
        return self.stats.copy()
    
    def cleanup(self):
        """清理资源"""
        if self.ai_client:
            self.ai_client.close()
        if self.ppt_processor:
            self.ppt_processor.cleanup()