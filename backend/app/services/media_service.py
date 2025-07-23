"""
音视频文件处理服务

提供音视频文件的检测、验证、信息提取和转换功能。
支持多种音视频格式，使用FFmpeg和Pydub作为处理后端。

Examples:
    >>> media_type = MediaService.detect_media_type("test.mp4")
    >>> if media_type:
    ...     info = MediaService.get_media_info("test.mp4")
    ...     print(f"Duration: {info['duration']}s")
"""

import os
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, Any, Set, Union, List
import hashlib
import tempfile
from dataclasses import dataclass

try:
    import ffmpeg
    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False
    
try:
    from pydub import AudioSegment
    from pydub.utils import mediainfo
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

from ..models.file import FileType

logger = logging.getLogger(__name__)


class MediaProcessingError(Exception):
    """
    媒体处理异常
    
    当媒体文件处理过程中发生错误时抛出此异常。
    包括但不限于：
    - 文件不存在或损坏
    - 不支持的文件格式
    - FFmpeg/Pydub处理失败
    - 音频转换错误
    """
    pass


class MediaService:
    """
    音视频文件处理服务
    
    提供统一的音视频文件处理功能，包括：
    - 文件类型检测和验证
    - 媒体信息提取
    - 音视频格式转换
    - 音频提取和处理
    
    Attributes:
        AUDIO_EXTENSIONS: 支持的音频文件扩展名集合
        VIDEO_EXTENSIONS: 支持的视频文件扩展名集合
    """
    
    # 支持的文件格式
    AUDIO_EXTENSIONS: Set[str] = {
        '.mp3', '.wav', '.m4a', '.flac', '.ogg', '.wma', '.aac',
        '.opus', '.webm', '.3gp', '.amr'  # 新增支持
    }
    VIDEO_EXTENSIONS: Set[str] = {
        '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v',
        '.3gp', '.ogv', '.ts', '.mts', '.m2ts'  # 新增支持
    }
    
    @classmethod
    def detect_media_type(cls, file_path: str) -> Optional[FileType]:
        """
        检测媒体文件类型
        
        Args:
            file_path: 文件路径，可以是绝对路径或文件名
            
        Returns:
            FileType.AUDIO: 音频文件
            FileType.VIDEO: 视频文件
            None: 不支持的文件类型
            
        Examples:
            >>> MediaService.detect_media_type("song.mp3")
            <FileType.AUDIO: 'audio'>
            >>> MediaService.detect_media_type("video.mp4") 
            <FileType.VIDEO: 'video'>
            >>> MediaService.detect_media_type("doc.txt")
            None
        """
        if not file_path:
            logger.warning("Empty file path provided to detect_media_type")
            return None
            
        ext = Path(file_path).suffix.lower()
        
        logger.debug(f"Detecting media type for extension: {ext}")
        
        if ext in cls.AUDIO_EXTENSIONS:
            logger.debug(f"Detected audio file type: {ext}")
            return FileType.AUDIO
        elif ext in cls.VIDEO_EXTENSIONS:
            logger.debug(f"Detected video file type: {ext}")
            return FileType.VIDEO
        else:
            logger.info(f"Unsupported file extension: {ext}")
            return None
    
    @classmethod
    def validate_media_file(cls, file_path: str) -> bool:
        """
        验证媒体文件是否有效
        
        检查文件是否存在、类型是否支持、是否可以正常读取。
        
        Args:
            file_path: 媒体文件路径
            
        Returns:
            bool: 文件有效返回true，否则返回false
            
        Note:
            此方法会尝试读取文件元数据来验证完整性，
            可能会有一定的性能开销。
        """
        logger.debug(f"Validating media file: {file_path}")
        
        if not file_path or not os.path.exists(file_path):
            logger.warning(f"Media file does not exist: {file_path}")
            return False
        
        file_type = cls.detect_media_type(file_path)
        if not file_type:
            logger.warning(f"Unsupported media file type: {file_path}")
            return False
        
        try:
            # 尝试获取文件信息来验证文件完整性
            info = cls.get_media_info(file_path)
            is_valid = info is not None and info.get('duration', 0) > 0
            
            if is_valid:
                logger.info(f"Media file validated successfully: {file_path} ({info.get('duration', 0):.2f}s)")
            else:
                logger.warning(f"Media file validation failed: invalid or zero duration - {file_path}")
                
            return is_valid
            
        except Exception as e:
            logger.error(f"Media file validation error for {file_path}: {e}", exc_info=True)
            return False
    
    @classmethod
    def get_media_info(cls, file_path: str) -> Optional[Dict[str, Any]]:
        """
        获取媒体文件详细信息
        
        使用FFmpeg（优先）或Pydub获取文件的元数据信息。
        
        Args:
            file_path: 媒体文件路径
            
        Returns:
            Dict[str, Any]: 包含文件信息的字典，包括：
                - duration: 时长（秒）
                - size: 文件大小（字节）
                - bitrate: 码率（bps）
                - sample_rate: 采样率（仅音频）
                - channels: 声道数（仅音频）
                - resolution: 分辨率（仅视频）
                - fps: 帧率（仅视频）
                
        Raises:
            MediaProcessingError: 文件不存在或没有可用的媒体处理库
            
        Examples:
            >>> info = MediaService.get_media_info("test.mp4")
            >>> print(f"Duration: {info['duration']}s")
            >>> print(f"Resolution: {info.get('resolution', 'N/A')}")
        """
        if not file_path or not os.path.exists(file_path):
            logger.error(f"Media file not found: {file_path}")
            raise MediaProcessingError(f"File not found: {file_path}")
        
        logger.info(f"Extracting media info from: {file_path}")
        
        try:
            # 尝试使用ffmpeg获取信息（优先选择）
            if FFMPEG_AVAILABLE:
                logger.debug("Using FFmpeg for media info extraction")
                return cls._get_info_with_ffmpeg(file_path)
            # 备选方案：使用pydub
            elif PYDUB_AVAILABLE:
                logger.debug("Using Pydub for media info extraction")
                return cls._get_info_with_pydub(file_path)
            else:
                logger.error("No media processing library available (FFmpeg or Pydub)")
                raise MediaProcessingError("No media processing library available")
                
        except MediaProcessingError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting media info for {file_path}: {e}", exc_info=True)
            return None
    
    @classmethod
    def _get_info_with_ffmpeg(cls, file_path: str) -> Dict[str, Any]:
        """使用ffmpeg获取媒体信息"""
        try:
            probe = ffmpeg.probe(file_path)
            
            # 查找音频和视频流
            audio_stream = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)
            video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
            
            info = {
                'duration': float(probe['format'].get('duration', 0)),
                'size': int(probe['format'].get('size', 0)),
                'bitrate': int(probe['format'].get('bit_rate', 0)),
                'format_name': probe['format'].get('format_name', ''),
            }
            
            if audio_stream:
                info.update({
                    'sample_rate': int(audio_stream.get('sample_rate', 0)),
                    'channels': int(audio_stream.get('channels', 0)),
                    'audio_codec': audio_stream.get('codec_name', ''),
                })
            
            if video_stream:
                info.update({
                    'width': int(video_stream.get('width', 0)),
                    'height': int(video_stream.get('height', 0)),
                    'fps': eval(video_stream.get('r_frame_rate', '0/1')),
                    'video_codec': video_stream.get('codec_name', ''),
                })
                info['resolution'] = f"{info['width']}x{info['height']}"
            
            return info
            
        except Exception as e:
            logger.error(f"FFmpeg probe failed: {e}")
            raise MediaProcessingError(f"Failed to probe media file: {e}")
    
    @classmethod
    def _get_info_with_pydub(cls, file_path: str) -> Dict[str, Any]:
        """使用pydub获取媒体信息（备选方案）"""
        try:
            # 使用pydub的mediainfo
            info_dict = mediainfo(file_path)
            
            info = {
                'duration': float(info_dict.get('duration', 0)),
                'size': os.path.getsize(file_path),
                'bitrate': int(info_dict.get('bit_rate', 0)),
                'sample_rate': int(info_dict.get('sample_rate', 0)),
                'channels': int(info_dict.get('channels', 0)),
                'audio_codec': info_dict.get('codec_name', ''),
                'format_name': info_dict.get('format_name', ''),
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Pydub mediainfo failed: {e}")
            raise MediaProcessingError(f"Failed to get media info: {e}")
    
    @classmethod
    def extract_audio_from_video(cls, video_path: str, output_path: str) -> str:
        """从视频文件中提取音频"""
        if not FFMPEG_AVAILABLE:
            raise MediaProcessingError("FFmpeg not available for audio extraction")
        
        try:
            logger.info(f"Extracting audio from {video_path} to {output_path}")
            
            # 使用ffmpeg提取音频
            (
                ffmpeg
                .input(video_path)
                .audio
                .output(output_path, acodec='pcm_s16le', ar=16000, ac=1)  # 单声道，16kHz，适合Whisper
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            if not os.path.exists(output_path):
                raise MediaProcessingError("Audio extraction failed - output file not created")
            
            logger.info(f"Audio extracted successfully: {output_path}")
            return output_path
            
        except ffmpeg.Error as e:
            stderr = e.stderr.decode() if e.stderr else "Unknown error"
            logger.error(f"FFmpeg extraction failed: {stderr}")
            raise MediaProcessingError(f"Audio extraction failed: {stderr}")
    
    @classmethod
    def convert_audio_for_whisper(cls, input_path: str, output_path: str) -> str:
        """将音频转换为适合Whisper处理的格式"""
        if not FFMPEG_AVAILABLE:
            raise MediaProcessingError("FFmpeg not available for audio conversion")
        
        try:
            logger.info(f"Converting audio {input_path} for Whisper processing")
            
            # 转换为Whisper推荐格式：16kHz单声道WAV
            (
                ffmpeg
                .input(input_path)
                .output(output_path, acodec='pcm_s16le', ar=16000, ac=1)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            if not os.path.exists(output_path):
                raise MediaProcessingError("Audio conversion failed - output file not created")
            
            logger.info(f"Audio converted successfully: {output_path}")
            return output_path
            
        except ffmpeg.Error as e:
            stderr = e.stderr.decode() if e.stderr else "Unknown error"
            logger.error(f"FFmpeg conversion failed: {stderr}")
            raise MediaProcessingError(f"Audio conversion failed: {stderr}")
    
    @classmethod
    def prepare_audio_for_transcription(cls, file_path: str, file_type: FileType) -> str:
        """准备音频文件用于转录"""
        # 创建临时目录
        temp_dir = Path(tempfile.gettempdir()) / "ppt_generator" / "audio_processing"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成输出文件名
        file_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
        output_file = temp_dir / f"whisper_{file_hash}.wav"
        
        try:
            if file_type == FileType.VIDEO:
                # 从视频中提取音频
                return cls.extract_audio_from_video(file_path, str(output_file))
            else:
                # 音频格式转换
                return cls.convert_audio_for_whisper(file_path, str(output_file))
                
        except Exception as e:
            logger.error(f"Failed to prepare audio for transcription: {e}")
            # 清理可能的临时文件
            if output_file.exists():
                output_file.unlink()
            raise
    
    @classmethod
    def cleanup_temp_file(cls, file_path: str):
        """清理临时文件"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.info(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temporary file {file_path}: {e}")
    
    @classmethod
    def get_supported_formats(cls) -> Dict[str, list]:
        """获取支持的文件格式"""
        return {
            'audio': list(cls.AUDIO_EXTENSIONS),
            'video': list(cls.VIDEO_EXTENSIONS)
        }
    
    @classmethod
    def estimate_processing_time(cls, duration_seconds: float, file_type: FileType) -> int:
        """估算处理时间（分钟）"""
        if file_type == FileType.VIDEO:
            # 视频需要先提取音频，时间稍长
            return max(1, int(duration_seconds / 60 * 0.3))
        else:
            # 纯音频处理相对较快
            return max(1, int(duration_seconds / 60 * 0.2))