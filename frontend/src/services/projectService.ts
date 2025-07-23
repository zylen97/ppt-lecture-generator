import api from './api';
import { 
  Project, 
  ProjectCreate, 
  ProjectUpdate, 
  ProjectSummary, 
  ProjectStatistics,
  ProjectListResponse,
  ProjectTemplate,
  ProjectTemplateResponse,
  ProjectActionResponse,
  ApiResponse 
} from '@/types';

export class ProjectService {
  /**
   * 创建项目
   */
  static async createProject(data: ProjectCreate): Promise<Project> {
    const response = await api.post<Project>('/projects/', data);
    return response.data;
  }

  /**
   * 获取项目列表
   */
  static async getProjects(params?: {
    skip?: number;
    limit?: number;
    active_only?: boolean;
    search?: string;
    semester?: string;
    instructor?: string;
    order_by?: string;
    order_direction?: 'asc' | 'desc';
  }): Promise<ProjectListResponse> {
    const response = await api.get<ProjectListResponse>('/projects/', { params });
    return response.data;
  }

  /**
   * 获取项目详情
   */
  static async getProject(projectId: number, includeStats: boolean = true): Promise<Project> {
    const response = await api.get<Project>(`/projects/${projectId}`, {
      params: { include_stats: includeStats }
    });
    return response.data;
  }

  /**
   * 更新项目
   */
  static async updateProject(projectId: number, data: ProjectUpdate): Promise<Project> {
    const response = await api.put<Project>(`/projects/${projectId}`, data);
    return response.data;
  }

  /**
   * 删除项目
   */
  static async deleteProject(projectId: number, force: boolean = false): Promise<ProjectActionResponse> {
    const response = await api.delete<ProjectActionResponse>(`/projects/${projectId}`, {
      params: { force }
    });
    return response.data;
  }

  /**
   * 归档项目
   */
  static async archiveProject(projectId: number): Promise<ProjectActionResponse> {
    const response = await api.post<ProjectActionResponse>(`/projects/${projectId}/archive`);
    return response.data;
  }

  /**
   * 恢复已归档的项目
   */
  static async restoreProject(projectId: number): Promise<ProjectActionResponse> {
    const response = await api.post<ProjectActionResponse>(`/projects/${projectId}/restore`);
    return response.data;
  }

  /**
   * 获取项目统计信息
   */
  static async getProjectStatistics(projectId: number, refresh: boolean = false): Promise<ProjectStatistics> {
    const response = await api.get<ProjectStatistics>(`/projects/${projectId}/statistics`, {
      params: { refresh }
    });
    return response.data;
  }

  /**
   * 获取项目模板
   */
  static async getProjectTemplates(): Promise<ProjectTemplate[]> {
    const response = await api.get<ProjectTemplateResponse>('/projects/templates/');
    return response.data.templates;
  }

  /**
   * 批量操作项目
   */
  static async batchArchiveProjects(projectIds: number[]): Promise<ProjectActionResponse[]> {
    const promises = projectIds.map(id => ProjectService.archiveProject(id));
    return Promise.all(promises);
  }

  static async batchRestoreProjects(projectIds: number[]): Promise<ProjectActionResponse[]> {
    const promises = projectIds.map(id => ProjectService.restoreProject(id));
    return Promise.all(promises);
  }

  static async batchDeleteProjects(projectIds: number[], force: boolean = false): Promise<ProjectActionResponse[]> {
    const promises = projectIds.map(id => ProjectService.deleteProject(id, force));
    return Promise.all(promises);
  }

  /**
   * 搜索项目
   */
  static async searchProjects(query: string, limit: number = 20): Promise<ProjectSummary[]> {
    const response = await ProjectService.getProjects({
      search: query,
      limit,
      active_only: true
    });
    return response.items;
  }

  /**
   * 获取项目概览统计
   */
  static async getProjectOverview(): Promise<{
    total_projects: number;
    active_projects: number;
    archived_projects: number;
    total_files: number;
    total_tasks: number;
    total_scripts: number;
    recent_projects: ProjectSummary[];
  }> {
    const [allProjects, recentProjects] = await Promise.all([
      ProjectService.getProjects({ limit: 1000 }),
      ProjectService.getProjects({ limit: 5, order_by: 'updated_at', order_direction: 'desc' })
    ]);

    const active = allProjects.items.filter(p => p.is_active);
    const archived = allProjects.items.filter(p => !p.is_active);
    
    const totalFiles = allProjects.items.reduce((sum, p) => sum + p.file_count, 0);
    const totalTasks = allProjects.items.reduce((sum, p) => sum + p.task_count, 0);
    const totalScripts = allProjects.items.reduce((sum, p) => sum + p.script_count, 0);

    return {
      total_projects: allProjects.total,
      active_projects: active.length,
      archived_projects: archived.length,
      total_files: totalFiles,
      total_tasks: totalTasks,
      total_scripts: totalScripts,
      recent_projects: recentProjects.items,
    };
  }

  /**
   * 格式化项目状态显示
   */
  static getStatusText(isActive: boolean): string {
    return isActive ? '活跃' : '已归档';
  }

  /**
   * 获取状态颜色
   */
  static getStatusColor(isActive: boolean): string {
    return isActive ? 'success' : 'default';
  }

  /**
   * 计算项目完成率
   */
  static calculateCompletionRate(statistics?: ProjectStatistics): number {
    if (!statistics || statistics.total_tasks === 0) {
      return 0;
    }
    return Math.round((statistics.status_summary.completed / statistics.total_tasks) * 100);
  }

  /**
   * 格式化项目创建时间
   */
  static formatCreateTime(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 1) {
      return '今天创建';
    } else if (diffDays === 2) {
      return '昨天创建';
    } else if (diffDays <= 7) {
      return `${diffDays}天前创建`;
    } else if (diffDays <= 30) {
      const weeks = Math.floor(diffDays / 7);
      return `${weeks}周前创建`;
    } else {
      return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    }
  }

  /**
   * 验证项目名称
   */
  static validateProjectName(name: string): { valid: boolean; message?: string } {
    if (!name || name.trim().length === 0) {
      return { valid: false, message: '项目名称不能为空' };
    }
    
    if (name.length > 100) {
      return { valid: false, message: '项目名称不能超过100个字符' };
    }
    
    // 检查特殊字符
    const invalidChars = /[<>:"/\\|?*]/;
    if (invalidChars.test(name)) {
      return { valid: false, message: '项目名称不能包含特殊字符 < > : " / \\ | ? *' };
    }
    
    return { valid: true };
  }

  /**
   * 验证课程代码格式
   */
  static validateCourseCode(code?: string): { valid: boolean; message?: string } {
    if (!code) return { valid: true };
    
    // 通常课程代码格式：字母+数字，如 CS101, MATH205
    const courseCodePattern = /^[A-Z]{2,4}\d{3,4}$/i;
    if (!courseCodePattern.test(code)) {
      return {
        valid: false,
        message: '课程代码格式无效，应为字母+数字组合（如：CS101）'
      };
    }
    
    return { valid: true };
  }

  /**
   * 生成项目快捷操作菜单项
   */
  static getProjectActions(project: ProjectSummary): Array<{
    key: string;
    label: string;
    icon?: string;
    disabled?: boolean;
    danger?: boolean;
  }> {
    const baseActions = [
      { key: 'view', label: '查看详情', icon: 'EyeOutlined' },
      { key: 'edit', label: '编辑项目', icon: 'EditOutlined' },
    ];

    if (project.is_active) {
      baseActions.push(
        { key: 'archive', label: '归档项目', icon: 'InboxOutlined' }
      );
    } else {
      baseActions.push(
        { key: 'restore', label: '恢复项目', icon: 'ReloadOutlined' }
      );
    }

    baseActions.push(
      { key: 'delete', label: '删除项目', icon: 'DeleteOutlined', danger: true }
    );

    return baseActions;
  }

  /**
   * 获取项目统计图表数据
   */
  static getStatisticsChartData(statistics: ProjectStatistics) {
    return {
      taskStatus: [
        { name: '待处理', value: statistics.status_summary.pending, color: '#faad14' },
        { name: '处理中', value: statistics.status_summary.processing, color: '#1890ff' },
        { name: '已完成', value: statistics.status_summary.completed, color: '#52c41a' },
        { name: '失败', value: statistics.status_summary.failed, color: '#ff4d4f' },
      ].filter(item => item.value > 0),
      contentOverview: [
        { name: '文件', value: statistics.total_files, color: '#722ed1' },
        { name: '任务', value: statistics.total_tasks, color: '#13c2c2' },
        { name: '讲稿', value: statistics.total_scripts, color: '#eb2f96' },
      ].filter(item => item.value > 0),
    };
  }
}