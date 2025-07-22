import api from './api';
import { Task, TaskType, TaskStatus, TaskProgress, GenerationConfig, ApiResponse } from '@/types';

export class TaskService {
  /**
   * 创建任务
   */
  static async createTask(data: {
    file_id: number;
    task_type?: TaskType;
    config_snapshot?: Record<string, any>;
  }): Promise<Task> {
    const response = await api.post<Task>('/tasks/', {
      file_id: data.file_id,
      task_type: data.task_type || TaskType.PPT_TO_SCRIPT,
      config_snapshot: data.config_snapshot,
    });
    return response.data;
  }

  /**
   * 获取任务详情
   */
  static async getTask(taskId: number): Promise<Task> {
    const response = await api.get<Task>(`/tasks/${taskId}`);
    return response.data;
  }

  /**
   * 获取任务列表
   */
  static async getTasks(params?: {
    skip?: number;
    limit?: number;
    status_filter?: TaskStatus;
  }): Promise<Task[]> {
    const response = await api.get<Task[]>('/tasks/', { params });
    return response.data;
  }

  /**
   * 更新任务
   */
  static async updateTask(
    taskId: number,
    data: {
      status?: TaskStatus;
      progress?: number;
      error_message?: string;
    }
  ): Promise<Task> {
    const response = await api.put<Task>(`/tasks/${taskId}`, data);
    return response.data;
  }

  /**
   * 启动任务
   */
  static async startTask(taskId: number): Promise<ApiResponse> {
    const response = await api.post<ApiResponse>(`/tasks/${taskId}/start`);
    return response.data;
  }

  /**
   * 取消任务
   */
  static async cancelTask(taskId: number): Promise<ApiResponse> {
    const response = await api.post<ApiResponse>(`/tasks/${taskId}/cancel`);
    return response.data;
  }

  /**
   * 创建并启动处理任务
   */
  static async createAndStartTask(data: {
    file_id: number;
    config: GenerationConfig;
  }): Promise<{ task: Task; started: boolean }> {
    // 1. 创建任务
    const task = await this.createTask({
      file_id: data.file_id,
      task_type: TaskType.PPT_TO_SCRIPT,
      config_snapshot: data.config,
    });

    // 2. 启动任务
    try {
      await this.startTask(task.id);
      return { task, started: true };
    } catch (error) {
      return { task, started: false };
    }
  }

  /**
   * 获取任务统计信息
   */
  static async getTaskStats(): Promise<{
    total: number;
    pending: number;
    processing: number;
    completed: number;
    failed: number;
  }> {
    // 这里可以实现一个专门的统计接口
    // 目前使用获取任务列表的方式
    const tasks = await this.getTasks({ limit: 1000 });
    
    const stats = {
      total: tasks.length,
      pending: 0,
      processing: 0,
      completed: 0,
      failed: 0,
    };

    tasks.forEach(task => {
      switch (task.status) {
        case TaskStatus.PENDING:
          stats.pending++;
          break;
        case TaskStatus.PROCESSING:
          stats.processing++;
          break;
        case TaskStatus.COMPLETED:
          stats.completed++;
          break;
        case TaskStatus.FAILED:
          stats.failed++;
          break;
      }
    });

    return stats;
  }

  /**
   * 格式化任务状态显示
   */
  static getStatusText(status: TaskStatus): string {
    const statusMap = {
      [TaskStatus.PENDING]: '等待处理',
      [TaskStatus.PROCESSING]: '处理中',
      [TaskStatus.COMPLETED]: '已完成',
      [TaskStatus.FAILED]: '处理失败',
      [TaskStatus.CANCELLED]: '已取消',
    };
    
    return statusMap[status] || '未知状态';
  }

  /**
   * 获取状态颜色
   */
  static getStatusColor(status: TaskStatus): string {
    const colorMap = {
      [TaskStatus.PENDING]: 'default',
      [TaskStatus.PROCESSING]: 'processing',
      [TaskStatus.COMPLETED]: 'success',
      [TaskStatus.FAILED]: 'error',
      [TaskStatus.CANCELLED]: 'default',
    };
    
    return colorMap[status] || 'default';
  }

  /**
   * 格式化任务类型显示
   */
  static getTaskTypeText(type: TaskType): string {
    const typeMap = {
      [TaskType.PPT_TO_SCRIPT]: 'PPT转讲稿',
      [TaskType.SCRIPT_EDIT]: '讲稿编辑',
      [TaskType.BATCH_PROCESS]: '批量处理',
    };
    
    return typeMap[type] || '未知类型';
  }

  /**
   * 格式化持续时间
   */
  static formatDuration(seconds: number): string {
    if (!seconds || seconds < 0) return '未知';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}小时${minutes}分钟${secs}秒`;
    } else if (minutes > 0) {
      return `${minutes}分钟${secs}秒`;
    } else {
      return `${secs}秒`;
    }
  }
}

/**
 * WebSocket连接管理类
 */
export class TaskWebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 3000; // 3秒

  /**
   * 连接WebSocket
   */
  connect(taskId: number, onProgress: (progress: TaskProgress) => void, onError?: (error: Event) => void): void {
    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/tasks/${taskId}/progress`;
    
    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log(`WebSocket connected for task ${taskId}`);
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onProgress(data);
        } catch (error) {
          console.error('WebSocket message parse error:', error);
        }
      };

      this.ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        this.attemptReconnect(taskId, onProgress, onError);
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        if (onError) onError(error);
      };

    } catch (error) {
      console.error('WebSocket connection failed:', error);
      if (onError) onError(error as Event);
    }
  }

  /**
   * 断开WebSocket连接
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.reconnectAttempts = 0;
  }

  /**
   * 尝试重连
   */
  private attemptReconnect(taskId: number, onProgress: (progress: TaskProgress) => void, onError?: (error: Event) => void): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        this.connect(taskId, onProgress, onError);
      }, this.reconnectInterval * this.reconnectAttempts);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  /**
   * 获取连接状态
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}