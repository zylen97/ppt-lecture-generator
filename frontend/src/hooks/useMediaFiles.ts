import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { message } from 'antd';
import api from '@/services/api';
import type { FileInfo } from '@/types';

/**
 * 媒体文件管理Hook
 * 
 * 提供媒体文件的获取、删除、选择等功能，集中管理相关状态和操作
 */
export const useMediaFiles = () => {
  const queryClient = useQueryClient();
  const [selectedFiles, setSelectedFiles] = useState<number[]>([]);

  // 获取媒体文件列表
  const {
    data: files = [],
    isLoading: filesLoading,
    error: filesError,
    refetch: refetchFiles
  } = useQuery<FileInfo[]>(
    'mediaFiles',
    async () => {
      const response = await api.get('/media/');
      return response.data?.data || response.data;
    },
    {
      refetchInterval: 30000, // 30秒自动刷新
      staleTime: 10000, // 10秒内数据视为新鲜
      cacheTime: 5 * 60 * 1000, // 5分钟缓存
      onError: (error) => {
        console.error('Failed to fetch media files:', error);
        message.error('获取媒体文件列表失败');
      }
    }
  );

  // 获取支持的格式
  const {
    data: supportedFormats,
    isLoading: formatsLoading
  } = useQuery(
    'supportedFormats',
    async () => {
      const response = await api.get('/media/formats/supported');
      return response.data?.data || response.data;
    },
    {
      staleTime: 10 * 60 * 1000, // 10分钟缓存
      cacheTime: 60 * 60 * 1000, // 1小时缓存
    }
  );

  // 删除单个文件
  const deleteFileMutation = useMutation(
    async (fileId: number) => {
      await api.delete(`/media/${fileId}`);
    },
    {
      onSuccess: (_, fileId) => {
        message.success('文件删除成功');
        queryClient.invalidateQueries('mediaFiles');
        queryClient.invalidateQueries('allTasks');
        
        // 从选中列表中移除已删除的文件
        setSelectedFiles(prev => prev.filter(id => id !== fileId));
      },
      onError: (error: any) => {
        const errorMessage = error?.response?.data?.error?.message || 
                           error?.response?.data?.detail || 
                           '删除失败';
        message.error(`删除文件失败: ${errorMessage}`);
      },
    }
  );

  // 批量删除文件
  const batchDeleteMutation = useMutation(
    async (fileIds: number[]) => {
      await Promise.all(fileIds.map(id => api.delete(`/media/${id}`)));
    },
    {
      onSuccess: (_, fileIds) => {
        message.success(`成功删除${fileIds.length}个文件`);
        queryClient.invalidateQueries('mediaFiles');
        queryClient.invalidateQueries('allTasks');
        setSelectedFiles([]);
      },
      onError: (error: any, fileIds) => {
        console.error('Batch delete error:', error);
        message.error(`批量删除失败，共${fileIds.length}个文件`);
      },
    }
  );

  // 文件选择操作
  const handleFileSelection = useCallback((selectedRowKeys: number[]) => {
    setSelectedFiles(selectedRowKeys);
  }, []);

  // 清空选择
  const clearSelection = useCallback(() => {
    setSelectedFiles([]);
  }, []);

  // 删除单个文件
  const deleteFile = useCallback((fileId: number) => {
    deleteFileMutation.mutate(fileId);
  }, [deleteFileMutation]);

  // 批量删除选中文件
  const deleteBatchSelected = useCallback(() => {
    if (selectedFiles.length === 0) {
      message.warning('请先选择要删除的文件');
      return;
    }
    batchDeleteMutation.mutate(selectedFiles);
  }, [selectedFiles, batchDeleteMutation]);

  // 手动刷新文件列表
  const refreshFiles = useCallback(() => {
    queryClient.invalidateQueries('mediaFiles');
  }, [queryClient]);

  // 根据类型筛选文件
  const getFilesByType = useCallback((type?: 'audio' | 'video') => {
    if (!type) return files;
    return files.filter(file => file.file_type === type);
  }, [files]);

  // 获取文件统计信息
  const getFileStats = useCallback(() => {
    const audioFiles = files.filter(f => f.file_type === 'audio');
    const videoFiles = files.filter(f => f.file_type === 'video');
    const totalSize = files.reduce((sum, file) => sum + (file.file_size_mb || 0), 0);
    const totalDuration = files.reduce((sum, file) => sum + (file.duration || 0), 0);

    return {
      total: files.length,
      audio: audioFiles.length,
      video: videoFiles.length,
      totalSize,
      totalDuration,
      selected: selectedFiles.length
    };
  }, [files, selectedFiles]);

  return {
    // 数据
    files,
    supportedFormats,
    selectedFiles,
    
    // 加载状态
    filesLoading,
    formatsLoading,
    isDeleting: deleteFileMutation.isLoading || batchDeleteMutation.isLoading,
    
    // 错误状态
    filesError,
    
    // 操作函数
    handleFileSelection,
    clearSelection,
    deleteFile,
    deleteBatchSelected,
    refreshFiles,
    refetchFiles,
    
    // 工具函数
    getFilesByType,
    getFileStats,
  };
};

export default useMediaFiles;