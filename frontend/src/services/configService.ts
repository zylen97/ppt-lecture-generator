import api from './api';
import { APIConfig, APIConfigCreate, APITestRequest, APITestResponse, ApiResponse } from '@/types';

export class ConfigService {
  /**
   * 创建API配置
   */
  static async createAPIConfig(data: APIConfigCreate): Promise<APIConfig> {
    const response = await api.post<APIConfig>('/configs/api', data);
    return response.data;
  }

  /**
   * 获取API配置详情
   */
  static async getAPIConfig(configId: number): Promise<APIConfig> {
    const response = await api.get<APIConfig>(`/configs/api/${configId}`);
    return response.data;
  }

  /**
   * 获取API配置列表
   */
  static async getAPIConfigs(params?: {
    skip?: number;
    limit?: number;
  }): Promise<APIConfig[]> {
    const response = await api.get<APIConfig[]>('/configs/api', { params });
    return response.data;
  }

  /**
   * 更新API配置
   */
  static async updateAPIConfig(configId: number, data: APIConfigCreate): Promise<APIConfig> {
    const response = await api.put<APIConfig>(`/configs/api/${configId}`, data);
    return response.data;
  }

  /**
   * 删除API配置
   */
  static async deleteAPIConfig(configId: number): Promise<ApiResponse> {
    const response = await api.delete<ApiResponse>(`/configs/api/${configId}`);
    return response.data;
  }

  /**
   * 测试API连接
   */
  static async testAPIConnection(data: APITestRequest): Promise<APITestResponse> {
    const response = await api.post<APITestResponse>('/configs/api/test', data);
    return response.data;
  }

  /**
   * 获取默认API配置
   */
  static async getDefaultAPIConfig(): Promise<APIConfig> {
    const response = await api.get<APIConfig>('/configs/api/default');
    return response.data;
  }

  /**
   * 验证API配置
   */
  static validateAPIConfig(data: Partial<APIConfigCreate>): {
    valid: boolean;
    errors: Record<string, string>;
  } {
    const errors: Record<string, string> = {};

    // 验证名称
    if (!data.name || data.name.trim().length === 0) {
      errors.name = '配置名称不能为空';
    } else if (data.name.length > 100) {
      errors.name = '配置名称不能超过100个字符';
    }

    // 验证端点
    if (!data.endpoint || data.endpoint.trim().length === 0) {
      errors.endpoint = 'API端点不能为空';
    } else if (!this.isValidUrl(data.endpoint)) {
      errors.endpoint = '请输入有效的URL地址';
    } else if (!data.endpoint.endsWith('/v1')) {
      errors.endpoint = 'API端点应该以 /v1 结尾';
    }

    // 验证API密钥
    if (!data.api_key || data.api_key.trim().length === 0) {
      errors.api_key = 'API密钥不能为空';
    } else if (data.api_key.length < 20) {
      errors.api_key = 'API密钥长度不足';
    }

    // 验证模型
    if (!data.model || data.model.trim().length === 0) {
      errors.model = '模型名称不能为空';
    }

    return {
      valid: Object.keys(errors).length === 0,
      errors,
    };
  }

  /**
   * 验证URL格式
   */
  private static isValidUrl(url: string): boolean {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * 获取预设的API端点
   */
  static getPresetEndpoints(): Array<{
    name: string;
    url: string;
    description: string;
  }> {
    return [
      {
        name: 'OpenAI 官方',
        url: 'https://api.openai.com/v1',
        description: 'OpenAI官方API端点',
      },
      {
        name: 'ChatAnywhere',
        url: 'https://api.chatanywhere.tech/v1',
        description: '国内中转服务，速度较快',
      },
      {
        name: 'OpenAI-SB',
        url: 'https://api.openai-sb.com/v1',
        description: '另一个中转服务选择',
      },
    ];
  }

  /**
   * 获取常用模型列表
   */
  static getCommonModels(): Array<{
    id: string;
    name: string;
    description: string;
    vision: boolean;
  }> {
    return [
      {
        id: 'gpt-4-vision-preview',
        name: 'GPT-4 Vision Preview',
        description: '支持图像分析的GPT-4模型',
        vision: true,
      },
      {
        id: 'gpt-4o',
        name: 'GPT-4o',
        description: '最新的多模态GPT-4模型',
        vision: true,
      },
      {
        id: 'gpt-4',
        name: 'GPT-4',
        description: '标准GPT-4模型',
        vision: false,
      },
      {
        id: 'gpt-3.5-turbo',
        name: 'GPT-3.5 Turbo',
        description: '快速且经济的选择',
        vision: false,
      },
    ];
  }

  /**
   * 掩码显示API密钥
   */
  static maskAPIKey(apiKey: string): string {
    if (apiKey.length <= 8) {
      return '*'.repeat(apiKey.length);
    }
    
    return apiKey.slice(0, 4) + '*'.repeat(apiKey.length - 8) + apiKey.slice(-4);
  }

  /**
   * 格式化延迟显示
   */
  static formatLatency(latencyMs?: number): string {
    if (!latencyMs || latencyMs < 0) return '未知';
    
    if (latencyMs < 1000) {
      return `${latencyMs.toFixed(0)}ms`;
    } else {
      return `${(latencyMs / 1000).toFixed(2)}s`;
    }
  }

  /**
   * 获取连接状态颜色
   */
  static getConnectionStatusColor(success: boolean, latencyMs?: number): string {
    if (!success) return 'error';
    
    if (!latencyMs) return 'default';
    
    if (latencyMs < 1000) return 'success';
    if (latencyMs < 3000) return 'warning';
    return 'error';
  }

  /**
   * 本地存储配置相关方法
   */
  static saveToLocalStorage(key: string, value: any): void {
    try {
      localStorage.setItem(`ppt_generator_${key}`, JSON.stringify(value));
    } catch (error) {
      console.warn('Failed to save to localStorage:', error);
    }
  }

  static getFromLocalStorage<T>(key: string, defaultValue: T): T {
    try {
      const item = localStorage.getItem(`ppt_generator_${key}`);
      return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
      console.warn('Failed to get from localStorage:', error);
      return defaultValue;
    }
  }

  static removeFromLocalStorage(key: string): void {
    try {
      localStorage.removeItem(`ppt_generator_${key}`);
    } catch (error) {
      console.warn('Failed to remove from localStorage:', error);
    }
  }
}