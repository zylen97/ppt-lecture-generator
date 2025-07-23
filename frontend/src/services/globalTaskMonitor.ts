/**
 * 全局任务监听WebSocket服务
 * 用于实时更新所有任务状态，替代轮询机制
 */

import { Task, WebSocketMessage } from '@/types';

export interface TaskUpdateCallback {
  (changedTasks: Task[]): void;
}

export interface ConnectionStatusCallback {
  (connected: boolean): void;
}

export class GlobalTaskMonitor {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000; // 3秒
  private isManualDisconnect = false;
  private currentProjectId: number | null = null;
  
  private updateCallbacks: Set<TaskUpdateCallback> = new Set();
  private statusCallbacks: Set<ConnectionStatusCallback> = new Set();

  constructor() {
    // 不在构造函数中自动连接，等待项目选择
  }

  /**
   * 添加任务更新回调
   */
  onTaskUpdate(callback: TaskUpdateCallback): () => void {
    this.updateCallbacks.add(callback);
    return () => this.updateCallbacks.delete(callback);
  }

  /**
   * 添加连接状态回调
   */
  onConnectionStatus(callback: ConnectionStatusCallback): () => void {
    this.statusCallbacks.add(callback);
    return () => this.statusCallbacks.delete(callback);
  }

  /**
   * 设置当前项目并连接到相应的WebSocket
   */
  setProject(projectId: number | null): void {
    if (this.currentProjectId === projectId) {
      return; // 项目没有变化，无需重连
    }

    this.currentProjectId = projectId;
    this.disconnectWebSocket();
    
    if (projectId) {
      this.connect();
    }
  }

  /**
   * 获取当前项目ID
   */
  getCurrentProjectId(): number | null {
    return this.currentProjectId;
  }

  /**
   * 建立WebSocket连接
   */
  private connect(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return;
    }

    if (!this.currentProjectId) {
      console.log('No project selected, WebSocket not connected');
      return;
    }

    // 使用相对路径以便通过Vite代理
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/tasks/projects/${this.currentProjectId}/monitor`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log(`Project task monitor WebSocket connected for project ${this.currentProjectId}`);
        this.reconnectAttempts = 0;
        this.notifyConnectionStatus(true);
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onclose = (event) => {
        console.log(`Project task monitor WebSocket closed for project ${this.currentProjectId}:`, event.code, event.reason);
        this.notifyConnectionStatus(false);
        
        if (!this.isManualDisconnect) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error(`Project task monitor WebSocket error for project ${this.currentProjectId}:`, error);
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.scheduleReconnect();
    }
  }

  /**
   * 处理WebSocket消息
   */
  private handleMessage(message: WebSocketMessage): void {
    switch (message.type) {
      case 'tasks_update':
        if (message.data && message.data.changed_tasks) {
          this.notifyTaskUpdate(message.data.changed_tasks);
        }
        break;
      case 'project_tasks_update':
        // 项目级别的任务更新
        if (message.data && message.data.changed_tasks) {
          this.notifyTaskUpdate(message.data.changed_tasks);
        }
        break;
      case 'progress':
        // 单个任务进度更新
        if (message.data && message.data.task_id) {
          this.notifyTaskUpdate([message.data]);
        }
        break;
      case 'status_change':
        // 任务状态变更
        if (message.data && message.data.task_id) {
          this.notifyTaskUpdate([message.data]);
        }
        break;
      default:
        console.log('Unknown WebSocket message type:', message.type);
    }
  }

  /**
   * 通知任务更新
   */
  private notifyTaskUpdate(changedTasks: Task[]): void {
    this.updateCallbacks.forEach(callback => {
      try {
        callback(changedTasks);
      } catch (error) {
        console.error('Error in task update callback:', error);
      }
    });
  }

  /**
   * 通知连接状态变化
   */
  private notifyConnectionStatus(connected: boolean): void {
    this.statusCallbacks.forEach(callback => {
      try {
        callback(connected);
      } catch (error) {
        console.error('Error in connection status callback:', error);
      }
    });
  }

  /**
   * 安排重连
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts && !this.isManualDisconnect) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // 指数退避
      
      console.log(`Scheduling reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        if (!this.isManualDisconnect) {
          this.connect();
        }
      }, delay);
    } else {
      console.error('Max reconnection attempts reached or manually disconnected');
    }
  }

  /**
   * 手动重连
   */
  reconnect(): void {
    this.reconnectAttempts = 0;
    this.isManualDisconnect = false;
    this.disconnectWebSocket();
    setTimeout(() => this.connect(), 1000);
  }

  /**
   * 仅断开WebSocket连接，不清理回调
   */
  private disconnectWebSocket(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * 断开连接并清理所有回调
   */
  disconnect(): void {
    this.isManualDisconnect = true;
    this.currentProjectId = null;
    
    this.disconnectWebSocket();
    
    this.updateCallbacks.clear();
    this.statusCallbacks.clear();
  }

  /**
   * 获取连接状态
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// 全局单例实例
let globalTaskMonitor: GlobalTaskMonitor | null = null;

export function getGlobalTaskMonitor(): GlobalTaskMonitor {
  if (!globalTaskMonitor) {
    globalTaskMonitor = new GlobalTaskMonitor();
  }
  return globalTaskMonitor;
}

// 页面卸载时清理
window.addEventListener('beforeunload', () => {
  if (globalTaskMonitor) {
    globalTaskMonitor.disconnect();
  }
});