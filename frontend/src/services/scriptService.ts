import api from './api';
import { Script, ScriptSummary, ApiResponse } from '@/types';

export class ScriptService {
  /**
   * 创建讲稿
   */
  static async createScript(data: {
    task_id: number;
    title: string;
    content: string;
    format?: string;
    estimated_duration?: number;
  }): Promise<Script> {
    const response = await api.post<Script>('/scripts/', {
      task_id: data.task_id,
      title: data.title,
      content: data.content,
      format: data.format || 'markdown',
      estimated_duration: data.estimated_duration,
    });
    return response.data;
  }

  /**
   * 获取讲稿详情
   */
  static async getScript(scriptId: number): Promise<Script> {
    const response = await api.get<Script>(`/scripts/${scriptId}`);
    return response.data;
  }

  /**
   * 获取讲稿列表
   */
  static async getScripts(params?: {
    skip?: number;
    limit?: number;
    task_id?: number;
    project_id?: number;
  }): Promise<ScriptSummary[]> {
    const response = await api.get<ScriptSummary[]>('/scripts/', { params });
    return response.data;
  }

  /**
   * 更新讲稿
   */
  static async updateScript(
    scriptId: number,
    data: {
      title?: string;
      content?: string;
      estimated_duration?: number;
    }
  ): Promise<Script> {
    const response = await api.put<Script>(`/scripts/${scriptId}`, data);
    return response.data;
  }

  /**
   * 删除讲稿
   */
  static async deleteScript(scriptId: number): Promise<ApiResponse> {
    const response = await api.delete<ApiResponse>(`/scripts/${scriptId}`);
    return response.data;
  }

  /**
   * 导出讲稿
   */
  static async exportScript(
    scriptId: number,
    format: 'markdown' | 'html' | 'txt'
  ): Promise<void> {
    const response = await api.get(`/scripts/${scriptId}/export/${format}`, {
      responseType: 'blob',
    });

    // 从响应头获取文件名
    const contentDisposition = response.headers['content-disposition'];
    let filename = `script_${scriptId}.${format}`;
    
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="(.+)"/);
      if (filenameMatch) {
        filename = filenameMatch[1];
      }
    }

    // 创建下载链接
    const blob = new Blob([response.data]);
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  /**
   * 预览讲稿
   */
  static async previewScript(scriptId: number): Promise<string> {
    const response = await api.get(`/scripts/${scriptId}/preview`, {
      responseType: 'text',
    });
    return response.data;
  }

  /**
   * 获取预览URL
   */
  static getPreviewUrl(scriptId: number): string {
    return `/api/scripts/${scriptId}/preview`;
  }

  /**
   * 格式化字数显示
   */
  static formatWordCount(count?: number): string {
    if (!count || count <= 0) return '未统计';
    
    if (count >= 10000) {
      return `${(count / 10000).toFixed(1)}万字`;
    } else if (count >= 1000) {
      return `${(count / 1000).toFixed(1)}千字`;
    } else {
      return `${count}字`;
    }
  }

  /**
   * 格式化预估时长
   */
  static formatEstimatedDuration(minutes?: number): string {
    if (!minutes || minutes <= 0) return '未设定';
    
    if (minutes >= 60) {
      const hours = Math.floor(minutes / 60);
      const remainingMinutes = minutes % 60;
      
      if (remainingMinutes === 0) {
        return `${hours}小时`;
      } else {
        return `${hours}小时${remainingMinutes}分钟`;
      }
    } else {
      return `${minutes}分钟`;
    }
  }

  /**
   * 计算阅读时长（按每分钟200字估算）
   */
  static calculateReadingTime(wordCount?: number): number {
    if (!wordCount || wordCount <= 0) return 0;
    return Math.max(1, Math.round(wordCount / 200));
  }

  /**
   * 获取支持的导出格式
   */
  static getSupportedExportFormats(): Array<{
    key: string;
    label: string;
    description: string;
  }> {
    return [
      {
        key: 'markdown',
        label: 'Markdown',
        description: '原始Markdown格式，适合进一步编辑',
      },
      {
        key: 'html',
        label: 'HTML',
        description: '网页格式，适合在线预览和分享',
      },
      {
        key: 'txt',
        label: '纯文本',
        description: '纯文本格式，兼容性最好',
      },
    ];
  }

  /**
   * 验证讲稿内容
   */
  static validateScriptContent(content: string): {
    valid: boolean;
    issues: string[];
  } {
    const issues: string[] = [];
    
    if (!content || content.trim().length === 0) {
      issues.push('讲稿内容不能为空');
    } else {
      if (content.length < 50) {
        issues.push('讲稿内容过短，建议至少50个字符');
      }
      
      if (content.length > 100000) {
        issues.push('讲稿内容过长，建议不超过10万字符');
      }
    }
    
    return {
      valid: issues.length === 0,
      issues,
    };
  }

  /**
   * 提取讲稿摘要
   */
  static extractSummary(content: string, maxLength: number = 200): string {
    if (!content || content.trim().length === 0) return '';
    
    // 移除Markdown标记
    let summary = content
      .replace(/#{1,6}\s+/g, '') // 移除标题标记
      .replace(/\*\*(.+?)\*\*/g, '$1') // 移除粗体标记
      .replace(/\*(.+?)\*/g, '$1') // 移除斜体标记
      .replace(/`(.+?)`/g, '$1') // 移除代码标记
      .replace(/\[(.+?)\]\(.+?\)/g, '$1') // 移除链接，保留文本
      .replace(/!\[.*?\]\(.+?\)/g, '') // 移除图片
      .replace(/^\s*[-*+]\s+/gm, '') // 移除列表标记
      .replace(/^\s*\d+\.\s+/gm, '') // 移除有序列表标记
      .replace(/\n+/g, ' ') // 将换行替换为空格
      .trim();
    
    // 截取指定长度
    if (summary.length > maxLength) {
      summary = summary.substring(0, maxLength) + '...';
    }
    
    return summary;
  }
}