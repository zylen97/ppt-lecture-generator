import { useState, useCallback, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { message } from 'antd';
import api from '@/services/api';
import { TaskService } from '@/services';
import type { Task, TaskStatus } from '@/types';

/**
 * 转录配置接口
 */
export interface TranscriptionConfig {
  language: string;
  model_size: string;
}

/**
 * 转录任务管理Hook
 * 
 * 提供转录任务的创建、监控、配置管理等功能
 */
export const useTranscription = (initialConfig?: TranscriptionConfig) => {
  const queryClient = useQueryClient();
  
  // 转录配置状态
  const [config, setConfig] = useState<TranscriptionConfig>(
    initialConfig || {
      language: 'auto',
      model_size: 'base',
    }
  );

  // 实时任务监控状态
  const [isMonitoring, setIsMonitoring] = useState(false);

  // 获取所有任务
  const {
    data: allTasks = [],
    isLoading: tasksLoading,
    error: tasksError,
    refetch: refetchTasks
  } = useQuery<Task[]>(
    'allTasks',
    () => TaskService.getTasks(),
    {
      refetchInterval: isMonitoring ? 3000 : 10000, // 监控时3秒，否则10秒
      staleTime: 2000,
      cacheTime: 5 * 60 * 1000,
      onError: (error) => {
        console.error('Failed to fetch tasks:', error);
        message.error('获取任务列表失败');
      }
    }
  );

  // 获取Whisper模型信息
  const {
    data: modelInfo,
    isLoading: modelInfoLoading
  } = useQuery(
    'whisperModels',
    async () => {
      const response = await api.get('/media/models/info');
      return response.data?.data || response.data;
    },
    {
      staleTime: 5 * 60 * 1000, // 5分钟缓存
      cacheTime: 30 * 60 * 1000, // 30分钟缓存
    }
  );

  // 筛选音视频转录任务
  const transcriptionTasks = allTasks.filter(
    task => task.task_type === 'audio_video_to_script'
  );

  // 创建转录任务
  const createTranscriptionMutation = useMutation(
    async ({ fileId, config }: { fileId: number; config: TranscriptionConfig }) => {
      const response = await api.post(`/media/${fileId}/transcribe`, config);
      return response.data?.data || response.data;
    },
    {
      onSuccess: () => {
        message.success('转录任务已创建并自动启动');
        queryClient.invalidateQueries('allTasks');
        
        // 开启实时监控
        setIsMonitoring(true);
        
        // 5分钟后关闭监控
        setTimeout(() => {
          setIsMonitoring(false);
        }, 5 * 60 * 1000);
      },
      onError: (error: any) => {
        const errorMessage = error?.response?.data?.error?.message || 
                           error?.response?.data?.detail || 
                           '转录任务创建失败';
        message.error(errorMessage);
        console.error('Transcription task creation error:', error);
      },
    }
  );

  // 启动转录任务
  const startTranscription = useCallback(async (fileId: number) => {
    try {
      message.loading('正在创建并启动转录任务...', 2);
      
      await createTranscriptionMutation.mutateAsync({
        fileId,
        config,
      });
      
      // 延迟刷新任务列表
      setTimeout(() => {
        queryClient.invalidateQueries('allTasks');
      }, 1000);
      
    } catch (error) {
      console.error('Failed to start transcription:', error);
    }
  }, [config, createTranscriptionMutation, queryClient]);

  // 批量启动转录
  const batchStartTranscription = useCallback(async (fileIds: number[]) => {
    if (fileIds.length === 0) {
      message.warning('请选择要转录的文件');
      return;
    }

    try {
      message.loading(`正在为${fileIds.length}个文件创建转录任务...`, 3);
      
      const promises = fileIds.map(fileId => 
        createTranscriptionMutation.mutateAsync({ fileId, config })
      );
      
      await Promise.all(promises);
      message.success(`成功创建${fileIds.length}个转录任务`);
      
      // 开启监控
      setIsMonitoring(true);
      setTimeout(() => setIsMonitoring(false), 10 * 60 * 1000); // 10分钟监控
      
    } catch (error) {
      console.error('Batch transcription failed:', error);
      message.error('批量转录任务创建失败');
    }
  }, [config, createTranscriptionMutation]);

  // 更新配置
  const updateConfig = useCallback((newConfig: Partial<TranscriptionConfig>) => {
    setConfig(prev => ({ ...prev, ...newConfig }));
  }, []);

  // 重置配置为默认值
  const resetConfig = useCallback(() => {
    setConfig({
      language: 'auto',
      model_size: 'base',
    });
  }, []);

  // 获取任务统计
  const getTaskStats = useCallback(() => {
    const pending = transcriptionTasks.filter(t => t.status === 'pending').length;
    const processing = transcriptionTasks.filter(t => t.status === 'processing').length;
    const completed = transcriptionTasks.filter(t => t.status === 'completed').length;
    const failed = transcriptionTasks.filter(t => t.status === 'failed').length;

    return {
      total: transcriptionTasks.length,
      pending,
      processing,
      completed,
      failed,
      successRate: transcriptionTasks.length > 0 
        ? Math.round((completed / transcriptionTasks.length) * 100) 
        : 0
    };
  }, [transcriptionTasks]);

  // 根据状态筛选任务
  const getTasksByStatus = useCallback((status: TaskStatus) => {
    return transcriptionTasks.filter(task => task.status === status);
  }, [transcriptionTasks]);

  // 获取进行中的任务
  const getActiveTask = useCallback(() => {
    return transcriptionTasks.find(task => task.status === 'processing');
  }, [transcriptionTasks]);

  // 获取最近的任务
  const getRecentTasks = useCallback((limit = 5) => {
    return transcriptionTasks
      .sort((a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime())
      .slice(0, limit);
  }, [transcriptionTasks]);

  // 手动刷新任务
  const refreshTasks = useCallback(() => {
    queryClient.invalidateQueries('allTasks');
  }, [queryClient]);

  // 获取推荐配置
  const getRecommendedConfig = useCallback((fileDuration?: number) => {
    if (!fileDuration) return config;

    let recommendedModel = 'base';
    if (fileDuration < 300) { // 5分钟以下
      recommendedModel = 'base';
    } else if (fileDuration < 1800) { // 30分钟以下
      recommendedModel = 'small';
    } else { // 长文件
      recommendedModel = 'medium';
    }

    return {
      ...config,
      model_size: recommendedModel
    };
  }, [config]);

  // 估算转录时间
  const estimateTranscriptionTime = useCallback((duration: number, modelSize?: string) => {
    const model = modelSize || config.model_size;
    const timeRatios: Record<string, number> = {
      'tiny': 0.1,
      'base': 0.15,
      'small': 0.25,
      'medium': 0.4,
      'large-v2': 0.6,
      'large-v3': 0.6,
    };

    const ratio = timeRatios[model] || 0.25;
    return Math.max(10, Math.round(duration * ratio)); // 最少10秒
  }, [config.model_size]);

  // 监听任务状态变化
  useEffect(() => {
    const activeTask = getActiveTask();
    if (activeTask && !isMonitoring) {
      setIsMonitoring(true);
    } else if (!activeTask && isMonitoring) {
      // 延迟关闭监控，避免频繁切换
      setTimeout(() => {
        if (!getActiveTask()) {
          setIsMonitoring(false);
        }
      }, 10000);
    }
  }, [transcriptionTasks, isMonitoring, getActiveTask]);

  return {
    // 数据
    config,
    allTasks,
    transcriptionTasks,
    modelInfo,
    
    // 加载状态
    tasksLoading,
    modelInfoLoading,
    isCreating: createTranscriptionMutation.isLoading,
    isMonitoring,
    
    // 错误状态
    tasksError,
    
    // 操作函数
    startTranscription,
    batchStartTranscription,
    updateConfig,
    resetConfig,
    refreshTasks,
    refetchTasks,
    
    // 工具函数
    getTaskStats,
    getTasksByStatus,
    getActiveTask,
    getRecentTasks,
    getRecommendedConfig,
    estimateTranscriptionTime,
  };
};

export default useTranscription;