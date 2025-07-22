import api from './api';
import { FileInfo, FileUploadResponse, ApiResponse } from '@/types';

export class FileService {
  /**
   * 上传文件
   */
  static async uploadFile(
    file: File,
    onProgress?: (percentage: number) => void
  ): Promise<FileUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post<FileUploadResponse>('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percentage = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percentage);
        }
      },
    });

    return response.data;
  }

  /**
   * 获取文件信息
   */
  static async getFileInfo(fileId: number): Promise<FileInfo> {
    const response = await api.get<FileInfo>(`/files/${fileId}`);
    return response.data;
  }

  /**
   * 获取文件列表
   */
  static async getFiles(params?: {
    skip?: number;
    limit?: number;
  }): Promise<FileInfo[]> {
    const response = await api.get<FileInfo[]>('/files/', { params });
    return response.data;
  }

  /**
   * 删除文件
   */
  static async deleteFile(fileId: number): Promise<ApiResponse> {
    const response = await api.delete<ApiResponse>(`/files/${fileId}`);
    return response.data;
  }

  /**
   * 下载文件
   */
  static async downloadFile(fileId: number): Promise<void> {
    const response = await api.get(`/files/${fileId}/download`, {
      responseType: 'blob',
    });

    // 从响应头获取文件名
    const contentDisposition = response.headers['content-disposition'];
    let filename = `file_${fileId}`;
    
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
   * 验证文件类型
   */
  static validateFileType(file: File): { valid: boolean; message?: string } {
    const allowedTypes = ['.ppt', '.pptx'];
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    
    if (!allowedTypes.includes(fileExtension)) {
      return {
        valid: false,
        message: `不支持的文件类型。支持的类型: ${allowedTypes.join(', ')}`
      };
    }

    return { valid: true };
  }

  /**
   * 验证文件大小
   */
  static validateFileSize(file: File, maxSizeMB: number = 100): { valid: boolean; message?: string } {
    const maxSize = maxSizeMB * 1024 * 1024; // 转换为字节
    
    if (file.size > maxSize) {
      return {
        valid: false,
        message: `文件大小超过限制（最大 ${maxSizeMB}MB），当前文件大小: ${(file.size / 1024 / 1024).toFixed(2)}MB`
      };
    }

    return { valid: true };
  }

  /**
   * 格式化文件大小
   */
  static formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
}