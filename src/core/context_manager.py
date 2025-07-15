"""
上下文管理模块

负责管理讲稿生成过程中的上下文信息，确保内容连贯性。
"""

import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

from ..utils.logger import get_logger
from ..utils.file_utils import FileUtils


@dataclass
class SlideContext:
    """单张幻灯片上下文"""
    slide_number: int
    title: str
    content: str
    analysis_result: str
    generated_script: str
    timestamp: float
    duration: int
    key_concepts: List[str]
    teaching_points: List[str]


@dataclass
class CourseContext:
    """整个课程上下文"""
    course_title: str
    total_slides: int
    current_slide: int
    total_duration: int
    elapsed_time: int
    key_concepts: List[str]
    teaching_progression: List[str]
    # interaction_points: List[int]  # 纯讲授模式，无需互动点
    example_slides: List[int]


class ContextManager:
    """上下文管理器"""
    
    def __init__(self, course_title: str = "", total_duration: int = 90):
        """
        初始化上下文管理器
        
        Args:
            course_title: 课程标题
            total_duration: 总时长（分钟）
        """
        self.logger = get_logger()
        
        # 课程上下文
        self.course_context = CourseContext(
            course_title=course_title,
            total_slides=0,
            current_slide=0,
            total_duration=total_duration,
            elapsed_time=0,
            key_concepts=[],
            teaching_progression=[],
            # interaction_points=[],  # 纯讲授模式，无需互动点
            example_slides=[]
        )
        
        # 幻灯片上下文列表
        self.slide_contexts: List[SlideContext] = []
        
        # 上下文摘要缓存
        self.context_summaries: Dict[str, str] = {}
        
        # 概念关系图
        self.concept_relationships: Dict[str, List[str]] = {}
        
        self.logger.info(f"初始化上下文管理器: {course_title}")
    
    def initialize_course(self, course_title: str, total_slides: int, 
                         total_duration: int):
        """
        初始化课程信息
        
        Args:
            course_title: 课程标题
            total_slides: 总幻灯片数
            total_duration: 总时长
        """
        self.course_context.course_title = course_title
        self.course_context.total_slides = total_slides
        self.course_context.total_duration = total_duration
        
        # 预计算互动点和示例点
        # self._calculate_interaction_points()  # 纯讲授模式，无需计算互动点
        self._calculate_example_points()
        
        self.logger.info(f"初始化课程: {course_title}, {total_slides}张幻灯片, {total_duration}分钟")
    
    def add_slide_context(self, slide_number: int, title: str, content: str,
                         analysis_result: str, duration: int = 3) -> SlideContext:
        """
        添加幻灯片上下文
        
        Args:
            slide_number: 幻灯片编号
            title: 幻灯片标题
            content: 幻灯片内容
            analysis_result: AI分析结果
            duration: 讲解时长
            
        Returns:
            SlideContext: 幻灯片上下文
        """
        # 提取关键概念
        key_concepts = self._extract_key_concepts(analysis_result)
        
        # 提取教学要点
        teaching_points = self._extract_teaching_points(analysis_result)
        
        # 创建幻灯片上下文
        slide_context = SlideContext(
            slide_number=slide_number,
            title=title,
            content=content,
            analysis_result=analysis_result,
            generated_script="",
            timestamp=time.time(),
            duration=duration,
            key_concepts=key_concepts,
            teaching_points=teaching_points
        )
        
        # 添加到列表
        self.slide_contexts.append(slide_context)
        
        # 更新课程上下文
        self._update_course_context(slide_context)
        
        self.logger.debug(f"添加幻灯片上下文: {slide_number} - {title}")
        return slide_context
    
    def update_slide_script(self, slide_number: int, generated_script: str):
        """
        更新幻灯片的生成脚本
        
        Args:
            slide_number: 幻灯片编号
            generated_script: 生成的脚本
        """
        for slide_context in self.slide_contexts:
            if slide_context.slide_number == slide_number:
                slide_context.generated_script = generated_script
                self.logger.debug(f"更新幻灯片脚本: {slide_number}")
                break
    
    def get_previous_context(self, slide_number: int, context_length: int = 3) -> str:
        """
        获取前文上下文
        
        Args:
            slide_number: 当前幻灯片编号
            context_length: 上下文长度（前几张幻灯片）
            
        Returns:
            str: 前文上下文摘要
        """
        if slide_number <= 1:
            return ""
        
        # 获取前面的幻灯片
        previous_slides = []
        for slide_context in self.slide_contexts:
            if slide_context.slide_number < slide_number:
                previous_slides.append(slide_context)
        
        # 限制上下文长度
        if len(previous_slides) > context_length:
            previous_slides = previous_slides[-context_length:]
        
        # 构建上下文摘要
        context_parts = []
        
        # 添加课程整体信息
        context_parts.append(f"课程: {self.course_context.course_title}")
        context_parts.append(f"当前进度: {slide_number}/{self.course_context.total_slides}")
        
        # 添加关键概念
        if self.course_context.key_concepts:
            context_parts.append(f"已涉及概念: {', '.join(self.course_context.key_concepts[-10:])}")
        
        # 添加前文摘要
        context_parts.append("\\n前文内容摘要:")
        for slide_context in previous_slides:
            summary = self._get_slide_summary(slide_context)
            context_parts.append(f"第{slide_context.slide_number}张 - {slide_context.title}: {summary}")
        
        # 添加教学进度
        if self.course_context.teaching_progression:
            context_parts.append(f"\\n教学进度: {' → '.join(self.course_context.teaching_progression[-5:])}")
        
        return "\\n".join(context_parts)
    
    def get_teaching_suggestions(self, slide_number: int) -> Dict[str, Any]:
        """
        获取教学建议
        
        Args:
            slide_number: 幻灯片编号
            
        Returns:
            Dict[str, Any]: 教学建议
        """
        suggestions = {
            'interaction_needed': False,  # 纯讲授模式，无需互动
            'example_needed': slide_number in self.course_context.example_slides,
            'time_allocation': self._calculate_time_allocation(slide_number),
            'difficulty_level': self._assess_difficulty(slide_number),
            'connection_points': self._find_connection_points(slide_number)
        }
        
        return suggestions
    
    def get_course_summary(self) -> Dict[str, Any]:
        """
        获取课程摘要
        
        Returns:
            Dict[str, Any]: 课程摘要
        """
        return {
            'course_info': asdict(self.course_context),
            'slides_count': len(self.slide_contexts),
            'total_concepts': len(self.course_context.key_concepts),
            'average_duration': self._calculate_average_duration(),
            'progress_percentage': (self.course_context.current_slide / self.course_context.total_slides) * 100 if self.course_context.total_slides > 0 else 0
        }
    
    def export_context(self, output_path: str) -> bool:
        """
        导出上下文信息
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            export_data = {
                'course_context': asdict(self.course_context),
                'slide_contexts': [asdict(slide) for slide in self.slide_contexts],
                'context_summaries': self.context_summaries,
                'concept_relationships': self.concept_relationships,
                'export_timestamp': time.time()
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"导出上下文信息: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出上下文失败: {e}")
            return False
    
    def import_context(self, input_path: str) -> bool:
        """
        导入上下文信息
        
        Args:
            input_path: 输入文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # 恢复课程上下文
            self.course_context = CourseContext(**import_data['course_context'])
            
            # 恢复幻灯片上下文
            self.slide_contexts = []
            for slide_data in import_data['slide_contexts']:
                self.slide_contexts.append(SlideContext(**slide_data))
            
            # 恢复其他数据
            self.context_summaries = import_data.get('context_summaries', {})
            self.concept_relationships = import_data.get('concept_relationships', {})
            
            self.logger.info(f"导入上下文信息: {input_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导入上下文失败: {e}")
            return False
    
    def _extract_key_concepts(self, analysis_result: str) -> List[str]:
        """
        从分析结果中提取关键概念
        
        Args:
            analysis_result: AI分析结果
            
        Returns:
            List[str]: 关键概念列表
        """
        concepts = []
        
        # 简单的关键词提取（实际应用中可以使用更复杂的NLP技术）
        lines = analysis_result.split('\\n')
        for line in lines:
            if '概念：' in line or '关键词：' in line:
                # 提取概念
                concept_text = line.split('：', 1)[1] if '：' in line else line
                concepts.extend([c.strip() for c in concept_text.split('、') if c.strip()])
        
        return concepts
    
    def _extract_teaching_points(self, analysis_result: str) -> List[str]:
        """
        从分析结果中提取教学要点
        
        Args:
            analysis_result: AI分析结果
            
        Returns:
            List[str]: 教学要点列表
        """
        points = []
        
        lines = analysis_result.split('\\n')
        for line in lines:
            if '要点：' in line or '重点：' in line:
                # 提取要点
                point_text = line.split('：', 1)[1] if '：' in line else line
                points.extend([p.strip() for p in point_text.split('；') if p.strip()])
        
        return points
    
    def _update_course_context(self, slide_context: SlideContext):
        """
        更新课程上下文
        
        Args:
            slide_context: 幻灯片上下文
        """
        # 更新当前幻灯片
        self.course_context.current_slide = slide_context.slide_number
        
        # 更新已用时间
        self.course_context.elapsed_time += slide_context.duration
        
        # 更新关键概念
        for concept in slide_context.key_concepts:
            if concept not in self.course_context.key_concepts:
                self.course_context.key_concepts.append(concept)
        
        # 更新教学进度
        if slide_context.title not in self.course_context.teaching_progression:
            self.course_context.teaching_progression.append(slide_context.title)
    
    def _calculate_interaction_points(self):
        """计算互动点 - 已禁用，纯讲授模式无需互动"""
        # 纯讲授模式，不计算互动点
        pass
    
    def _calculate_example_points(self):
        """计算示例点"""
        if self.course_context.total_slides == 0:
            return
        
        # 每5-8张幻灯片安排一个示例
        example_interval = max(5, self.course_context.total_slides // 8)
        
        for i in range(example_interval, self.course_context.total_slides, example_interval):
            self.course_context.example_slides.append(i)
    
    def _get_slide_summary(self, slide_context: SlideContext) -> str:
        """
        获取幻灯片摘要
        
        Args:
            slide_context: 幻灯片上下文
            
        Returns:
            str: 幻灯片摘要
        """
        # 检查缓存
        cache_key = f"slide_{slide_context.slide_number}_summary"
        if cache_key in self.context_summaries:
            return self.context_summaries[cache_key]
        
        # 生成摘要
        summary_parts = []
        
        # 添加主要概念
        if slide_context.key_concepts:
            summary_parts.append(f"涉及{', '.join(slide_context.key_concepts[:3])}")
        
        # 添加教学要点
        if slide_context.teaching_points:
            summary_parts.append(f"重点: {slide_context.teaching_points[0]}")
        
        summary = "; ".join(summary_parts)
        
        # 缓存摘要
        self.context_summaries[cache_key] = summary
        
        return summary
    
    def _calculate_time_allocation(self, slide_number: int) -> Dict[str, int]:
        """
        计算时间分配
        
        Args:
            slide_number: 幻灯片编号
            
        Returns:
            Dict[str, int]: 时间分配建议
        """
        remaining_slides = self.course_context.total_slides - slide_number + 1
        remaining_time = self.course_context.total_duration - self.course_context.elapsed_time
        
        if remaining_slides <= 0:
            return {'suggested_time': 0, 'remaining_time': remaining_time}
        
        average_time = int(remaining_time / remaining_slides)
        
        return {
            'suggested_time': max(2, min(8, average_time)),
            'remaining_time': remaining_time,
            'average_time': average_time
        }
    
    def _assess_difficulty(self, slide_number: int) -> str:
        """
        评估难度级别
        
        Args:
            slide_number: 幻灯片编号
            
        Returns:
            str: 难度级别
        """
        if slide_number <= 1:
            return "简单"
        
        # 根据概念数量和教学点数量评估
        slide_context = None
        for ctx in self.slide_contexts:
            if ctx.slide_number == slide_number:
                slide_context = ctx
                break
        
        if not slide_context:
            return "中等"
        
        concept_count = len(slide_context.key_concepts)
        point_count = len(slide_context.teaching_points)
        
        if concept_count <= 2 and point_count <= 2:
            return "简单"
        elif concept_count <= 4 and point_count <= 4:
            return "中等"
        else:
            return "困难"
    
    def _find_connection_points(self, slide_number: int) -> List[str]:
        """
        找到关联点
        
        Args:
            slide_number: 幻灯片编号
            
        Returns:
            List[str]: 关联点列表
        """
        connections = []
        
        # 查找当前幻灯片的概念
        current_concepts = []
        for ctx in self.slide_contexts:
            if ctx.slide_number == slide_number:
                current_concepts = ctx.key_concepts
                break
        
        # 查找与前面幻灯片的关联
        for ctx in self.slide_contexts:
            if ctx.slide_number < slide_number:
                # 查找共同概念
                common_concepts = set(current_concepts) & set(ctx.key_concepts)
                if common_concepts:
                    connections.append(f"与第{ctx.slide_number}张幻灯片的共同概念: {', '.join(common_concepts)}")
        
        return connections
    
    def _calculate_average_duration(self) -> float:
        """
        计算平均时长
        
        Returns:
            float: 平均时长
        """
        if not self.slide_contexts:
            return 0.0
        
        total_duration = sum(ctx.duration for ctx in self.slide_contexts)
        return int(total_duration / len(self.slide_contexts)) if len(self.slide_contexts) > 0 else 0
    
    def clear_context(self):
        """清理上下文"""
        self.slide_contexts.clear()
        self.context_summaries.clear()
        self.concept_relationships.clear()
        
        # 重置课程上下文
        self.course_context = CourseContext(
            course_title="",
            total_slides=0,
            current_slide=0,
            total_duration=90,
            elapsed_time=0,
            key_concepts=[],
            teaching_progression=[],
            # interaction_points=[],  # 纯讲授模式，无需互动点
            example_slides=[]
        )
        
        self.logger.info("清理上下文完成")