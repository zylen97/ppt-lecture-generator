import { useState, useCallback, useRef } from 'react';
import { useMutation, useQueryClient } from 'react-query';
import { message, Upload } from 'antd';
import api from '@/services/api';
import type { UploadFile } from 'antd/es/upload';

/**
 * 上传进度信息
 */
interface UploadProgress {
  percent: number;
  status: 'uploading' | 'success' | 'error' | 'idle';
  message?: string;
}

/**
 * 支持的格式信息
 */
interface SupportedFormats {
  audio?: string[];
  video?: string[];
}

/**
 * 媒体上传Hook
 * 
 * 提供文件上传、进度跟踪、格式验证等功能
 */
export const useMediaUpload = (supportedFormats?: SupportedFormats) => {
  const queryClient = useQueryClient();
  const [uploadFileList, setUploadFileList] = useState<UploadFile[]>([]);
  const [dragCount, setDragCount] = useState(0);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({
    percent: 0,
    status: 'idle'
  });
  
  // 用于取消上传的引用
  const cancelTokenRef = useRef<AbortController | null>(null);

  // 获取支持的文件扩展名
  const getSupportedExtensions = useCallback(() => {
    if (!supportedFormats) return [];
    return [...(supportedFormats.audio || []), ...(supportedFormats.video || [])];
  }, [supportedFormats]);

  // 验证文件类型
  const validateFileType = useCallback((fileName: string) => {
    const supportedExts = getSupportedExtensions();
    if (supportedExts.length === 0) return true; // 没有限制时允许所有格式
    
    const fileExt = '.' + fileName.split('.').pop()?.toLowerCase();
    return supportedExts.includes(fileExt);
  }, [getSupportedExtensions]);

  // 验证文件大小
  const validateFileSize = useCallback((fileSize: number, maxSizeMB = 500) => {
    const maxBytes = maxSizeMB * 1024 * 1024;
    return fileSize <= maxBytes;
  }, []);

  // 文件上传Mutation
  const uploadMutation = useMutation(
    async (formData: FormData) => {
      // 创建取消令牌
      const abortController = new AbortController();
      cancelTokenRef.current = abortController;

      setUploadProgress({ percent: 0, status: 'uploading', message: '开始上传...' });

      try {
        const response = await api.post('/media/upload', formData, {
          headers: {
            'Content-Type': undefined, // 让浏览器自动设置边界
          },
          signal: abortController.signal,
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const percentCompleted = Math.round(
                (progressEvent.loaded * 100) / progressEvent.total
              );
              setUploadProgress({
                percent: percentCompleted,
                status: 'uploading',
                message: `上传中... ${percentCompleted}%`
              });
            }
          },
        });

        setUploadProgress({ 
          percent: 100, 
          status: 'success', 
          message: '上传成功' 
        });

        return response.data?.data || response.data;
      } catch (error: any) {
        if (error.name === 'AbortError') {
          setUploadProgress({ 
            percent: 0, 
            status: 'idle', 
            message: '上传已取消' 
          });
          throw new Error('上传已取消');
        }
        
        setUploadProgress({ 
          percent: 0, 
          status: 'error', 
          message: '上传失败' 
        });
        throw error;
      } finally {
        cancelTokenRef.current = null;
      }
    },
    {
      onSuccess: () => {
        message.success('媒体文件上传成功');
        queryClient.invalidateQueries('mediaFiles');
        setUploadFileList([]);
        
        // 3秒后重置进度状态
        setTimeout(() => {
          setUploadProgress({ percent: 0, status: 'idle' });
        }, 3000);
      },
      onError: (error: any) => {
        if (error.message === '上传已取消') {
          message.warning('文件上传已取消');
          return;
        }

        const errorMessage = error?.response?.data?.error?.message || 
                           error?.response?.data?.detail || 
                           error?.message || 
                           '文件上传失败';
        message.error(`上传失败: ${errorMessage}`);
        console.error('Upload error:', error);
      },
    }
  );

  // 处理文件选择前的验证
  const beforeUpload = useCallback((file: File) => {
    // 验证文件类型
    if (!validateFileType(file.name)) {
      const supportedExts = getSupportedExtensions();
      message.error(`不支持的文件格式。支持的格式: ${supportedExts.join(', ')}`);
      return Upload.LIST_IGNORE;
    }

    // 验证文件大小
    if (!validateFileSize(file.size)) {
      message.error('文件大小不能超过500MB');
      return Upload.LIST_IGNORE;
    }

    console.log('文件验证通过:', file.name);
    return false; // 阻止自动上传
  }, [validateFileType, validateFileSize, getSupportedExtensions]);

  // 处理文件列表变化
  const handleFileListChange = useCallback((info: any) => {
    setUploadFileList(info.fileList);
  }, []);

  // 处理拖拽进入
  const handleDragEnter = useCallback(() => {
    setDragCount(prev => prev + 1);
  }, []);

  // 处理拖拽离开
  const handleDragLeave = useCallback(() => {
    setDragCount(prev => Math.max(0, prev - 1));
  }, []);

  // 处理文件拖拽放下
  const handleDrop = useCallback((e: React.DragEvent) => {
    console.log('Dropped files', e.dataTransfer.files);
    setDragCount(0);
  }, []);

  // 开始上传
  const startUpload = useCallback(async () => {
    if (uploadFileList.length === 0) {
      message.warning('请选择要上传的音视频文件');
      return;
    }

    const file = uploadFileList[0];
    if (file.originFileObj) {
      const formData = new FormData();
      formData.append('file', file.originFileObj);
      
      try {
        const result = await uploadMutation.mutateAsync(formData);
        return result;
      } catch (error) {
        console.error('Upload failed:', error);
        throw error;
      }
    }
  }, [uploadFileList, uploadMutation]);

  // 取消上传
  const cancelUpload = useCallback(() => {
    if (cancelTokenRef.current) {
      cancelTokenRef.current.abort();
      message.info('正在取消上传...');
    }
  }, []);

  // 清空文件列表
  const clearFileList = useCallback(() => {
    setUploadFileList([]);
    setUploadProgress({ percent: 0, status: 'idle' });
  }, []);

  // 批量上传文件
  const batchUpload = useCallback(async (files: File[]) => {
    if (files.length === 0) return [];

    const results = [];
    const totalFiles = files.length;
    
    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        // 验证文件
        if (!validateFileType(file.name) || !validateFileSize(file.size)) {
          console.warn(`Skipping invalid file: ${file.name}`);
          continue;
        }

        setUploadProgress({
          percent: Math.round((i / totalFiles) * 100),
          status: 'uploading',
          message: `上传文件 ${i + 1}/${totalFiles}: ${file.name}`
        });

        const formData = new FormData();
        formData.append('file', file);
        
        const result = await uploadMutation.mutateAsync(formData);
        results.push(result);
      }

      setUploadProgress({
        percent: 100,
        status: 'success',
        message: `批量上传完成，成功上传 ${results.length} 个文件`
      });

      return results;
    } catch (error) {
      console.error('Batch upload failed:', error);
      throw error;
    }
  }, [validateFileType, validateFileSize, uploadMutation]);

  // 重试上传
  const retryUpload = useCallback(() => {
    if (uploadFileList.length > 0) {
      startUpload();
    }
  }, [startUpload, uploadFileList]);

  // 获取上传状态信息
  const getUploadStatus = useCallback(() => {
    return {
      hasFiles: uploadFileList.length > 0,
      isUploading: uploadMutation.isLoading,
      isDragging: dragCount > 0,
      canUpload: uploadFileList.length > 0 && !uploadMutation.isLoading,
      progress: uploadProgress,
    };
  }, [uploadFileList, uploadMutation.isLoading, dragCount, uploadProgress]);

  return {
    // 状态
    uploadFileList,
    dragCount,
    uploadProgress,
    
    // 加载状态
    isUploading: uploadMutation.isLoading,
    
    // 上传属性配置
    uploadProps: {
      name: 'file',
      multiple: false,
      fileList: uploadFileList,
      beforeUpload,
      onChange: handleFileListChange,
      onDrop: handleDrop,
      onDragEnter: handleDragEnter,
      onDragLeave: handleDragLeave,
    },
    
    // 操作函数
    startUpload,
    cancelUpload,
    clearFileList,
    batchUpload,
    retryUpload,
    
    // 工具函数
    getSupportedExtensions,
    validateFileType,
    validateFileSize,
    getUploadStatus,
  };
};

export default useMediaUpload;