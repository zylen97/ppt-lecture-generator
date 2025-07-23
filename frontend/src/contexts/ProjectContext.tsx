/**
 * 项目管理系统 - React Context上下文
 * 
 * 这个文件实现了项目管理系统的全局状态管理，基于React Context + useReducer模式。
 * 
 * 核心功能：
 * - 项目列表管理：加载、搜索、筛选、分页
 * - 当前项目管理：选择、切换、状态同步
 * - 项目CRUD操作：创建、更新、删除、归档、恢复
 * - 缓存机制：减少重复API调用，提升用户体验
 * - 持久化存储：localStorage保存当前项目，刷新页面后自动恢复
 * 
 * 架构特点：
 * - 使用useReducer管理复杂状态，保证状态更新的可预测性
 * - 提供便捷Hooks简化组件使用
 * - 实现项目级别数据隔离
 * - 支持项目详情缓存，提升访问速度
 * 
 * 使用方式：
 * 1. 在App根组件包裹ProjectProvider
 * 2. 在子组件中使用useCurrentProject或useProjectList获取状态和操作方法
 */

import React, { createContext, useContext, useReducer, useCallback, useEffect, ReactNode } from 'react';
import { message } from 'antd';
import { Project, ProjectSummary, ProjectListResponse } from '@/types';
import { ProjectService } from '@/services';

// 上下文状态类型
interface ProjectState {
  // 项目列表
  projects: ProjectSummary[];
  projectsLoading: boolean;
  projectsError: string | null;
  
  // 当前选中项目
  currentProject: Project | null;
  currentProjectLoading: boolean;
  currentProjectError: string | null;
  
  // 分页信息
  pagination: {
    current: number;
    pageSize: number;
    total: number;
    hasMore: boolean;
  };
  
  // 筛选条件
  filters: {
    search?: string;
    semester?: string;
    instructor?: string;
    activeOnly: boolean;
  };
  
  // 缓存项目详情
  projectCache: Map<number, Project>;
}

// 操作类型
type ProjectAction =
  | { type: 'SET_PROJECTS_LOADING'; payload: boolean }
  | { type: 'SET_PROJECTS'; payload: { projects: ProjectSummary[]; pagination: any } }
  | { type: 'SET_PROJECTS_ERROR'; payload: string | null }
  | { type: 'ADD_PROJECT'; payload: ProjectSummary }
  | { type: 'UPDATE_PROJECT'; payload: ProjectSummary }
  | { type: 'REMOVE_PROJECT'; payload: number }
  | { type: 'SET_CURRENT_PROJECT_LOADING'; payload: boolean }
  | { type: 'SET_CURRENT_PROJECT'; payload: Project | null }
  | { type: 'SET_CURRENT_PROJECT_ERROR'; payload: string | null }
  | { type: 'UPDATE_CURRENT_PROJECT'; payload: Partial<Project> }
  | { type: 'SET_FILTERS'; payload: Partial<ProjectState['filters']> }
  | { type: 'SET_PAGINATION'; payload: Partial<ProjectState['pagination']> }
  | { type: 'CACHE_PROJECT'; payload: Project }
  | { type: 'CLEAR_CACHE' }
  | { type: 'RESET_STATE' };

// 初始状态
const initialState: ProjectState = {
  projects: [],
  projectsLoading: false,
  projectsError: null,
  
  currentProject: null,
  currentProjectLoading: false,
  currentProjectError: null,
  
  pagination: {
    current: 1,
    pageSize: 20,
    total: 0,
    hasMore: false,
  },
  
  filters: {
    activeOnly: true,
  },
  
  projectCache: new Map(),
};

// Reducer
function projectReducer(state: ProjectState, action: ProjectAction): ProjectState {
  switch (action.type) {
    case 'SET_PROJECTS_LOADING':
      return { ...state, projectsLoading: action.payload };
      
    case 'SET_PROJECTS':
      return {
        ...state,
        projects: action.payload.projects,
        pagination: { ...state.pagination, ...action.payload.pagination },
        projectsLoading: false,
        projectsError: null,
      };
      
    case 'SET_PROJECTS_ERROR':
      return {
        ...state,
        projectsError: action.payload,
        projectsLoading: false,
      };
      
    case 'ADD_PROJECT':
      return {
        ...state,
        projects: [action.payload, ...state.projects],
        pagination: {
          ...state.pagination,
          total: state.pagination.total + 1,
        },
      };
      
    case 'UPDATE_PROJECT':
      return {
        ...state,
        projects: state.projects.map(p => 
          p.id === action.payload.id ? action.payload : p
        ),
      };
      
    case 'REMOVE_PROJECT':
      return {
        ...state,
        projects: state.projects.filter(p => p.id !== action.payload),
        pagination: {
          ...state.pagination,
          total: Math.max(0, state.pagination.total - 1),
        },
      };
      
    case 'SET_CURRENT_PROJECT_LOADING':
      return { ...state, currentProjectLoading: action.payload };
      
    case 'SET_CURRENT_PROJECT':
      return {
        ...state,
        currentProject: action.payload,
        currentProjectLoading: false,
        currentProjectError: null,
      };
      
    case 'SET_CURRENT_PROJECT_ERROR':
      return {
        ...state,
        currentProjectError: action.payload,
        currentProjectLoading: false,
      };
      
    case 'UPDATE_CURRENT_PROJECT':
      return {
        ...state,
        currentProject: state.currentProject 
          ? { ...state.currentProject, ...action.payload }
          : null,
      };
      
    case 'SET_FILTERS':
      return {
        ...state,
        filters: { ...state.filters, ...action.payload },
      };
      
    case 'SET_PAGINATION':
      return {
        ...state,
        pagination: { ...state.pagination, ...action.payload },
      };
      
    case 'CACHE_PROJECT':
      const newCache = new Map(state.projectCache);
      newCache.set(action.payload.id, action.payload);
      return { ...state, projectCache: newCache };
      
    case 'CLEAR_CACHE':
      return { ...state, projectCache: new Map() };
      
    case 'RESET_STATE':
      return { ...initialState, projectCache: new Map() };
      
    default:
      return state;
  }
}

// 上下文值类型
interface ProjectContextValue {
  // 状态
  state: ProjectState;
  
  // 项目列表操作
  loadProjects: (params?: { reset?: boolean }) => Promise<void>;
  refreshProjects: () => Promise<void>;
  searchProjects: (query: string) => Promise<void>;
  setFilters: (filters: Partial<ProjectState['filters']>) => void;
  
  // 当前项目操作
  selectProject: (projectId: number) => Promise<void>;
  clearCurrentProject: () => void;
  updateCurrentProject: (data: Partial<Project>) => void;
  
  // 项目CRUD操作
  createProject: (data: any) => Promise<Project>;
  updateProject: (projectId: number, data: any) => Promise<Project>;
  deleteProject: (projectId: number, force?: boolean) => Promise<void>;
  archiveProject: (projectId: number) => Promise<void>;
  restoreProject: (projectId: number) => Promise<void>;
  
  // 工具方法
  getProjectFromCache: (projectId: number) => Project | null;
  clearCache: () => void;
  resetState: () => void;
}

// 创建上下文
const ProjectContext = createContext<ProjectContextValue | null>(null);

// Provider组件
interface ProjectProviderProps {
  children: ReactNode;
}

export const ProjectProvider: React.FC<ProjectProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(projectReducer, initialState);

  // 加载项目列表
  const loadProjects = useCallback(async (params?: { reset?: boolean }) => {
    try {
      dispatch({ type: 'SET_PROJECTS_LOADING', payload: true });
      
      const queryParams = {
        skip: params?.reset ? 0 : (state.pagination.current - 1) * state.pagination.pageSize,
        limit: state.pagination.pageSize,
        active_only: state.filters.activeOnly,
        search: state.filters.search,
        semester: state.filters.semester,
        instructor: state.filters.instructor,
        order_by: 'updated_at',
        order_direction: 'desc' as const,
      };
      
      const response: ProjectListResponse = await ProjectService.getProjects(queryParams);
      
      dispatch({
        type: 'SET_PROJECTS',
        payload: {
          projects: params?.reset ? response.items : [...state.projects, ...response.items],
          pagination: {
            current: params?.reset ? 1 : state.pagination.current,
            total: response.total,
            hasMore: response.has_more,
          },
        },
      });
    } catch (error: any) {
      const errorMessage = error?.response?.data?.detail || error?.message || '获取项目列表失败';
      dispatch({ type: 'SET_PROJECTS_ERROR', payload: errorMessage });
      message.error(errorMessage);
    }
  }, [
    state.pagination.current,
    state.pagination.pageSize,
    state.filters,
    state.projects,
  ]);

  // 刷新项目列表
  const refreshProjects = useCallback(async () => {
    await loadProjects({ reset: true });
  }, [loadProjects]);

  // 搜索项目
  const searchProjects = useCallback(async (query: string) => {
    dispatch({ type: 'SET_FILTERS', payload: { search: query } });
    dispatch({ type: 'SET_PAGINATION', payload: { current: 1 } });
    await loadProjects({ reset: true });
  }, [loadProjects]);

  // 设置筛选条件
  const setFilters = useCallback((filters: Partial<ProjectState['filters']>) => {
    dispatch({ type: 'SET_FILTERS', payload: filters });
    dispatch({ type: 'SET_PAGINATION', payload: { current: 1 } });
  }, []);

  // 选择当前项目
  // 这是项目管理系统的核心功能，切换当前活跃项目
  // 所有页面的数据都会基于当前项目进行过滤和显示
  const selectProject = useCallback(async (projectId: number) => {
    try {
      // 优先从缓存中获取项目数据，减少API调用
      const cachedProject = state.projectCache.get(projectId);
      if (cachedProject) {
        dispatch({ type: 'SET_CURRENT_PROJECT', payload: cachedProject });
        return;
      }

      // 显示加载状态
      dispatch({ type: 'SET_CURRENT_PROJECT_LOADING', payload: true });
      
      // 从服务器获取完整的项目详情（包含统计数据）
      const project = await ProjectService.getProject(projectId, true);
      
      // 将项目数据添加到缓存中，提升后续访问速度
      dispatch({ type: 'CACHE_PROJECT', payload: project });
      dispatch({ type: 'SET_CURRENT_PROJECT', payload: project });
      
      // 持久化当前项目ID，页面刷新后自动恢复
      localStorage.setItem('currentProjectId', projectId.toString());
    } catch (error: any) {
      const errorMessage = error?.response?.data?.detail || error?.message || '获取项目详情失败';
      dispatch({ type: 'SET_CURRENT_PROJECT_ERROR', payload: errorMessage });
      message.error(errorMessage);
    }
  }, [state.projectCache]);

  // 清除当前项目
  const clearCurrentProject = useCallback(() => {
    dispatch({ type: 'SET_CURRENT_PROJECT', payload: null });
    localStorage.removeItem('currentProjectId');
  }, []);

  // 更新当前项目
  const updateCurrentProject = useCallback((data: Partial<Project>) => {
    dispatch({ type: 'UPDATE_CURRENT_PROJECT', payload: data });
  }, []);

  // 创建项目
  const createProject = useCallback(async (data: any): Promise<Project> => {
    try {
      const project = await ProjectService.createProject(data);
      
      // 转换为ProjectSummary格式添加到列表
      const summary: ProjectSummary = {
        id: project.id,
        name: project.name,
        description: project.description,
        course_code: project.course_code,
        semester: project.semester,
        instructor: project.instructor,
        cover_image: project.cover_image,
        is_active: project.is_active,
        created_at: project.created_at,
        updated_at: project.updated_at,
        file_count: project.total_files,
        task_count: project.total_tasks,
        script_count: project.total_scripts,
        completion_rate: 0,
      };
      
      dispatch({ type: 'ADD_PROJECT', payload: summary });
      dispatch({ type: 'CACHE_PROJECT', payload: project });
      
      message.success('项目创建成功');
      return project;
    } catch (error: any) {
      const errorMessage = error?.response?.data?.detail || error?.message || '创建项目失败';
      message.error(errorMessage);
      throw error;
    }
  }, []);

  // 更新项目
  const updateProject = useCallback(async (projectId: number, data: any): Promise<Project> => {
    try {
      const project = await ProjectService.updateProject(projectId, data);
      
      // 更新列表中的项目
      const summary: ProjectSummary = {
        id: project.id,
        name: project.name,
        description: project.description,
        course_code: project.course_code,
        semester: project.semester,
        instructor: project.instructor,
        cover_image: project.cover_image,
        is_active: project.is_active,
        created_at: project.created_at,
        updated_at: project.updated_at,
        file_count: project.total_files,
        task_count: project.total_tasks,
        script_count: project.total_scripts,
        completion_rate: ProjectService.calculateCompletionRate(project.statistics),
      };
      
      dispatch({ type: 'UPDATE_PROJECT', payload: summary });
      dispatch({ type: 'CACHE_PROJECT', payload: project });
      
      // 如果是当前项目，也更新当前项目状态
      if (state.currentProject?.id === projectId) {
        dispatch({ type: 'SET_CURRENT_PROJECT', payload: project });
      }
      
      message.success('项目更新成功');
      return project;
    } catch (error: any) {
      const errorMessage = error?.response?.data?.detail || error?.message || '更新项目失败';
      message.error(errorMessage);
      throw error;
    }
  }, [state.currentProject]);

  // 删除项目
  const deleteProject = useCallback(async (projectId: number, force: boolean = false) => {
    try {
      await ProjectService.deleteProject(projectId, force);
      
      dispatch({ type: 'REMOVE_PROJECT', payload: projectId });
      
      // 如果删除的是当前项目，清除当前项目状态
      if (state.currentProject?.id === projectId) {
        clearCurrentProject();
      }
      
      // 从缓存中移除
      const newCache = new Map(state.projectCache);
      newCache.delete(projectId);
      dispatch({ type: 'CACHE_PROJECT', payload: Array.from(newCache.values())[0] || null });
      
      message.success('项目删除成功');
    } catch (error: any) {
      const errorMessage = error?.response?.data?.detail || error?.message || '删除项目失败';
      message.error(errorMessage);
      throw error;
    }
  }, [state.currentProject, state.projectCache, clearCurrentProject]);

  // 归档项目
  const archiveProject = useCallback(async (projectId: number) => {
    try {
      await ProjectService.archiveProject(projectId);
      
      // 更新项目状态
      const updatedProjects = state.projects.map(p =>
        p.id === projectId ? { ...p, is_active: false } : p
      );
      dispatch({ type: 'SET_PROJECTS', payload: { projects: updatedProjects, pagination: state.pagination } });
      
      message.success('项目已归档');
    } catch (error: any) {
      const errorMessage = error?.response?.data?.detail || error?.message || '归档项目失败';
      message.error(errorMessage);
      throw error;
    }
  }, [state.projects, state.pagination]);

  // 恢复项目
  const restoreProject = useCallback(async (projectId: number) => {
    try {
      await ProjectService.restoreProject(projectId);
      
      // 更新项目状态
      const updatedProjects = state.projects.map(p =>
        p.id === projectId ? { ...p, is_active: true } : p
      );
      dispatch({ type: 'SET_PROJECTS', payload: { projects: updatedProjects, pagination: state.pagination } });
      
      message.success('项目已恢复');
    } catch (error: any) {
      const errorMessage = error?.response?.data?.detail || error?.message || '恢复项目失败';
      message.error(errorMessage);
      throw error;
    }
  }, [state.projects, state.pagination]);

  // 从缓存获取项目
  const getProjectFromCache = useCallback((projectId: number): Project | null => {
    return state.projectCache.get(projectId) || null;
  }, [state.projectCache]);

  // 清除缓存
  const clearCache = useCallback(() => {
    dispatch({ type: 'CLEAR_CACHE' });
  }, []);

  // 重置状态
  const resetState = useCallback(() => {
    dispatch({ type: 'RESET_STATE' });
    localStorage.removeItem('currentProjectId');
  }, []);

  // 页面刷新时恢复当前项目
  // 实现项目状态的持久化，用户刷新页面后仍然保持在当前项目
  useEffect(() => {
    const savedProjectId = localStorage.getItem('currentProjectId');
    if (savedProjectId && !state.currentProject) {
      selectProject(parseInt(savedProjectId, 10));
    }
  }, [selectProject, state.currentProject]);

  // 初始加载项目列表
  // 应用启动时自动加载项目列表，确保用户有项目可选择
  useEffect(() => {
    if (state.projects.length === 0 && !state.projectsLoading) {
      loadProjects({ reset: true });
    }
  }, [loadProjects, state.projects.length, state.projectsLoading]);

  const contextValue: ProjectContextValue = {
    state,
    loadProjects,
    refreshProjects,
    searchProjects,
    setFilters,
    selectProject,
    clearCurrentProject,
    updateCurrentProject,
    createProject,
    updateProject,
    deleteProject,
    archiveProject,
    restoreProject,
    getProjectFromCache,
    clearCache,
    resetState,
  };

  return (
    <ProjectContext.Provider value={contextValue}>
      {children}
    </ProjectContext.Provider>
  );
};

/**
 * 基础Hook：获取完整的项目上下文
 * 
 * @returns ProjectContextValue 完整的项目上下文值
 * @throws Error 如果不在ProjectProvider内使用
 */
export const useProject = (): ProjectContextValue => {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
};

/**
 * 便捷Hook：获取当前项目相关状态和操作
 * 
 * 专门用于需要访问当前项目的组件，如页面标题、项目选择器等
 * 自动提供项目切换和清除功能
 * 
 * @returns 当前项目状态和操作方法
 */
export const useCurrentProject = () => {
  const { state, selectProject, clearCurrentProject } = useProject();
  return {
    currentProject: state.currentProject,
    currentProjectLoading: state.currentProjectLoading,
    currentProjectError: state.currentProjectError,
    selectProject,
    clearCurrentProject,
  };
};

/**
 * 便捷Hook：获取项目列表相关状态和操作
 * 
 * 专门用于项目管理页面，提供完整的项目列表管理功能
 * 包括加载、搜索、筛选、CRUD操作等
 * 
 * @returns 项目列表状态和操作方法
 */
export const useProjectList = () => {
  const { 
    state, 
    loadProjects, 
    refreshProjects, 
    searchProjects, 
    setFilters,
    createProject,
    updateProject,
    deleteProject,
    archiveProject,
    restoreProject 
  } = useProject();
  
  return {
    projects: state.projects,
    projectsLoading: state.projectsLoading,
    projectsError: state.projectsError,
    pagination: state.pagination,
    filters: state.filters,
    loadProjects,
    refreshProjects,
    searchProjects,
    setFilters,
    createProject,
    updateProject,
    deleteProject,
    archiveProject,
    restoreProject,
  };
};