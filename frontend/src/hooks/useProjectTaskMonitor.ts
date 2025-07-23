/**
 * 项目任务监控Hook
 * 自动管理全局任务监控器与项目上下文的集成
 */

import { useEffect, useCallback } from 'react';
import { useCurrentProject } from '@/contexts';
import { getGlobalTaskMonitor, TaskUpdateCallback, ConnectionStatusCallback } from '@/services/globalTaskMonitor';

export function useProjectTaskMonitor() {
  const { currentProject } = useCurrentProject();
  const taskMonitor = getGlobalTaskMonitor();

  // 当项目变化时，自动更新WebSocket连接
  useEffect(() => {
    taskMonitor.setProject(currentProject?.id || null);
  }, [currentProject?.id, taskMonitor]);

  // 添加任务更新监听器
  const onTaskUpdate = useCallback((callback: TaskUpdateCallback) => {
    return taskMonitor.onTaskUpdate(callback);
  }, [taskMonitor]);

  // 添加连接状态监听器
  const onConnectionStatus = useCallback((callback: ConnectionStatusCallback) => {
    return taskMonitor.onConnectionStatus(callback);
  }, [taskMonitor]);

  // 手动重连
  const reconnect = useCallback(() => {
    taskMonitor.reconnect();
  }, [taskMonitor]);

  // 获取连接状态
  const isConnected = useCallback(() => {
    return taskMonitor.isConnected();
  }, [taskMonitor]);

  // 获取当前项目ID
  const getCurrentProjectId = useCallback(() => {
    return taskMonitor.getCurrentProjectId();
  }, [taskMonitor]);

  return {
    currentProject,
    onTaskUpdate,
    onConnectionStatus,
    reconnect,
    isConnected,
    getCurrentProjectId,
  };
}