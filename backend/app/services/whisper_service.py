"""
Whisper语音转录服务

基于faster-whisper库的高性能语音转文本服务。
支持多种语言、多种模型大小，可配置精度和性能平衡。

Features:
    - 多语言识别支持
    - 实时进度回调
    - GPU加速支持
    - 词级时间戳
    - 语音活动检测
    - 模型缓存管理

Examples:
    >>> service = WhisperService(model_size="base")
    >>> result = await service.transcribe_file("audio.wav", language="zh")
    >>> print(result["text"])
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Iterator, Callable, Any, Union
import tempfile
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

from ..models.task import Task
from .media_service import MediaService, MediaProcessingError

logger = logging.getLogger(__name__)


class WhisperTranscriptionError(Exception):
    """
    Whisper转录异常
    
    当Whisper语音转录过程中发生错误时抛出此异常。
    包括但不限于：
    - 模型加载失败
    - 音频文件无效或损坏
    - 转录过程中断（GPU内存不足等）
    - 不支持的语言或模型
    """
    pass


class WhisperService:
    """
    Whisper语音转录服务
    
    高效的语音转文本服务，支持多种模型大小和语言。
    使用faster-whisper库提供比OpenAI Whisper更快的推理速度。
    
    Attributes:
        model_size: 当前使用的模型大小
        device: 计算设备 (cpu/cuda/auto)
        compute_type: 计算精度 (int8/float16/float32/auto)
        model: 加载的Whisper模型实例
    
    Note:
        模型会在首次使用时懒加载，并缓存以供后续使用。
        支持多线程并发调用，但共享同一个模型实例。
    """
    
    # 可用的模型大小及其特性
    AVAILABLE_MODELS: List[str] = [
        "tiny",      # ~37 MB, 最快但准确度较低, 适合实时应用
        "base",      # ~142 MB, 较好的平衡, 推荐默认选择
        "small",     # ~466 MB, 更好的准确度, 适合一般用途
        "medium",    # ~1.5 GB, 很好的准确度, 需要较多内存
        "large-v2",  # ~3.1 GB, 最高准确度, 需要大内存
        "large-v3",  # ~3.1 GB, 最新版本, 更好的多语言支持
    ]
    
    # 支持的语言码和显示名称的映射
    SUPPORTED_LANGUAGES: Dict[str, str] = {
        "auto": "自动检测",
        "zh": "中文",
        "en": "英语", 
        "ja": "日语",
        "ko": "韩语",
        "es": "西班牙语",
        "fr": "法语",
        "de": "德语",
        "ru": "俄语",
        "ar": "阿拉伯语",
        "it": "意大利语",
        "pt": "葡萄牙语",
        "nl": "荷兰语",
        "pl": "波兰语",
        "tr": "土耳其语",
    }
    
    def __init__(self, 
                 model_size: str = "base",
                 device: str = "auto",
                 compute_type: str = "auto") -> None:
        """
        初始化Whisper服务
        
        Args:
            model_size: 模型大小，必须在AVAILABLE_MODELS中
            device: 计算设备 ("cpu", "cuda", "auto")
            compute_type: 计算类型 ("int8", "float16", "float32", "auto")
            
        Raises:
            WhisperTranscriptionError: faster-whisper库不可用或模型大小无效
            
        Note:
            模型不会在初始化时立即加载，而是在首次调用时懒加载。
        """
        if not WHISPER_AVAILABLE:
            logger.error("faster-whisper library is not available. Please install it first.")
            raise WhisperTranscriptionError("faster-whisper not available")
        
        if model_size not in self.AVAILABLE_MODELS:
            logger.error(f"Invalid model size: {model_size}. Available: {self.AVAILABLE_MODELS}")
            raise WhisperTranscriptionError(f"Invalid model size: {model_size}")
        
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model: Optional[Any] = None
        self._model_loading = False
        
        logger.info(f"WhisperService initialized: model={model_size}, device={device}, compute_type={compute_type}")
    
    async def load_model(self) -> Any:
        """
        异步加载模型
        
        使用懒加载策略，只在首次需要时加载模型。
        支持并发安全，多个协程同时调用时只会加载一次。
        
        Returns:
            Any: 加载的WhisperModel实例
            
        Raises:
            WhisperTranscriptionError: 模型加载失败
        """
        if self.model is not None:
            logger.debug(f"Model {self.model_size} already loaded, reusing")
            return self.model
        
        if self._model_loading:
            logger.debug("Model loading in progress, waiting...")
            # 等待其他协程完成模型加载
            while self._model_loading:
                await asyncio.sleep(0.1)
            return self.model
        
        self._model_loading = True
        
        try:
            logger.info(f"Loading Whisper model: {self.model_size} (device: {self.device}, compute_type: {self.compute_type})")
            start_time = asyncio.get_event_loop().time()
            
            # 在线程池中加载模型，避免阻塞主线程
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=1) as executor:
                self.model = await loop.run_in_executor(
                    executor,
                    self._load_model_sync
                )
            
            load_time = asyncio.get_event_loop().time() - start_time
            logger.info(f"Whisper model {self.model_size} loaded successfully in {load_time:.2f}s")
            return self.model
            
        except Exception as e:
            logger.error(f"Failed to load Whisper model {self.model_size}: {e}", exc_info=True)
            raise WhisperTranscriptionError(f"Model loading failed: {e}")
        finally:
            self._model_loading = False
    
    def _load_model_sync(self) -> Any:
        """同步加载模型"""
        # 确定设备
        device = self.device
        if device == "auto":
            device = "cuda" if self._is_cuda_available() else "cpu"
        
        # 确定计算类型
        compute_type = self.compute_type
        if compute_type == "auto":
            if device == "cuda":
                compute_type = "float16"
            else:
                compute_type = "int8"  # CPU上使用int8更快
        
        logger.info(f"Loading model with device={device}, compute_type={compute_type}")
        
        return WhisperModel(
            self.model_size,
            device=device,
            compute_type=compute_type,
            download_root=self._get_model_cache_dir()
        )
    
    @staticmethod
    def _is_cuda_available() -> bool:
        """检查CUDA是否可用"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    @staticmethod
    def _get_model_cache_dir() -> str:
        """获取模型缓存目录"""
        cache_dir = Path.home() / ".cache" / "ppt_generator" / "whisper_models"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return str(cache_dir)
    
    async def transcribe_file(self,
                             audio_file: str,
                             language: str = "auto",
                             task_id: Optional[int] = None,
                             progress_callback: Optional[Callable[[int, str], None]] = None) -> Dict:
        """
        转录音频文件
        
        Args:
            audio_file: 音频文件路径
            language: 语言代码
            task_id: 任务ID（用于进度回调）
            progress_callback: 进度回调函数
            
        Returns:
            转录结果字典
        """
        if not os.path.exists(audio_file):
            raise WhisperTranscriptionError(f"Audio file not found: {audio_file}")
        
        try:
            # 加载模型
            if progress_callback:
                progress_callback(10, "正在加载语音识别模型...")
            
            model = await self.load_model()
            
            if progress_callback:
                progress_callback(20, "开始语音转录...")
            
            # 在线程池中执行转录，避免阻塞
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(
                    executor,
                    self._transcribe_sync,
                    model,
                    audio_file,
                    language,
                    progress_callback
                )
            
            if progress_callback:
                progress_callback(100, "转录完成")
            
            return result
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            if progress_callback:
                progress_callback(-1, f"转录失败: {str(e)}")
            raise WhisperTranscriptionError(f"Transcription failed: {e}")
    
    def _transcribe_sync(self,
                        model: Any,
                        audio_file: str,
                        language: str,
                        progress_callback: Optional[Callable[[int, str], None]]) -> Dict:
        """同步执行转录"""
        try:
            # 设置转录参数
            transcribe_options = {
                "beam_size": 5,
                "best_of": 5,
                "temperature": 0.0,
                "condition_on_previous_text": True,
                "initial_prompt": None,
                "word_timestamps": True,  # 启用词级时间戳
                "vad_filter": True,      # 启用语音活动检测
                "vad_parameters": dict(
                    threshold=0.5,
                    min_speech_duration_ms=250,
                    max_speech_duration_s=float('inf'),
                    min_silence_duration_ms=2000,
                    speech_pad_ms=400,
                ),
            }
            
            # 语言设置 - 避免空语言检测导致的错误
            if language and language != "auto":
                transcribe_options["language"] = language
            else:
                # 对于"auto"或空语言，默认使用中文以避免语言检测失败
                transcribe_options["language"] = "zh"
                logger.info("Using default language 'zh' to avoid language detection failures")
            
            logger.info(f"Starting transcription with options: {transcribe_options}")
            
            # 执行转录
            segments, info = model.transcribe(audio_file, **transcribe_options)
            
            # 收集结果
            transcript_segments = []
            full_text = []
            
            # 将segments转换为列表，避免迭代器被消耗
            segments_list = list(segments)
            total_segments = len(segments_list) if segments_list else 1  # 避免除以0
            
            for i, segment in enumerate(segments_list):
                segment_data = {
                    "id": segment.id,
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                    "confidence": getattr(segment, 'avg_logprob', None),
                }
                
                # 词级时间戳
                if hasattr(segment, 'words') and segment.words:
                    segment_data["words"] = [
                        {
                            "start": word.start,
                            "end": word.end,
                            "word": word.word,
                            "confidence": getattr(word, 'probability', None)
                        }
                        for word in segment.words
                    ]
                
                transcript_segments.append(segment_data)
                full_text.append(segment.text.strip())
                
                # 更新进度
                if progress_callback and i % 5 == 0:  # 更频繁的进度更新
                    progress = min(20 + int((i / total_segments) * 70), 90)
                    progress_callback(progress, f"转录进度: {i}/{total_segments}段已完成")
            
            # 构建结果
            result = {
                "text": " ".join(full_text),
                "segments": transcript_segments,
                "language": info.language,
                "language_confidence": info.language_probability,
                "duration": info.duration,
                "model_size": self.model_size,
                "device": self.device,
                "compute_type": self.compute_type,
            }
            
            logger.info(f"Transcription completed: {len(transcript_segments)} segments, "
                       f"language={info.language}, duration={info.duration:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Sync transcription failed: {e}")
            raise
    
    def get_model_info(self) -> Dict:
        """获取模型信息"""
        return {
            "model_size": self.model_size,
            "device": self.device,
            "compute_type": self.compute_type,
            "available_models": self.AVAILABLE_MODELS,
            "supported_languages": self.SUPPORTED_LANGUAGES,
            "model_loaded": self.model is not None,
            "whisper_available": WHISPER_AVAILABLE,
        }
    
    @classmethod
    def get_recommended_model(cls, file_duration: float) -> str:
        """根据文件时长推荐模型"""
        if file_duration < 300:  # 5分钟以下
            return "base"
        elif file_duration < 1800:  # 30分钟以下
            return "small"
        else:  # 长文件
            return "medium"
    
    @classmethod
    def estimate_transcription_time(cls, duration_seconds: float, model_size: str) -> int:
        """估算转录时间（秒）"""
        # 基础时间比例（实际播放时长的倍数）
        time_ratios = {
            "tiny": 0.1,
            "base": 0.15,
            "small": 0.25,
            "medium": 0.4,
            "large-v2": 0.6,
            "large-v3": 0.6,
        }
        
        ratio = time_ratios.get(model_size, 0.25)
        return max(10, int(duration_seconds * ratio))  # 最少10秒
    
    async def cleanup(self):
        """清理资源"""
        if self.model is not None:
            # Whisper模型不需要显式清理
            logger.info("Whisper service cleanup completed")


# 全局Whisper服务实例
_whisper_service: Optional[WhisperService] = None


def get_whisper_service(model_size: str = "base") -> WhisperService:
    """获取Whisper服务实例（单例模式）"""
    global _whisper_service
    
    if _whisper_service is None or _whisper_service.model_size != model_size:
        _whisper_service = WhisperService(model_size=model_size)
    
    return _whisper_service