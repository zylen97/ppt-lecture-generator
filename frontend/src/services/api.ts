import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { message } from 'antd';

// 创建axios实例
const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证token
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error);
    
    // 处理网络错误
    if (!error.response) {
      message.error('网络连接失败，请检查网络设置');
      return Promise.reject(error);
    }

    // 处理HTTP错误状态码
    const { status, data } = error.response;
    
    switch (status) {
      case 400:
        message.error(data?.detail || '请求参数错误');
        break;
      case 401:
        message.error('未授权访问');
        // 可以在这里处理token过期，跳转到登录页
        break;
      case 403:
        message.error('禁止访问');
        break;
      case 404:
        message.error('请求的资源不存在');
        break;
      case 413:
        message.error('上传文件过大');
        break;
      case 422:
        message.error(data?.detail || '数据验证失败');
        break;
      case 429:
        message.error('请求过于频繁，请稍后再试');
        break;
      case 500:
        message.error('服务器内部错误');
        break;
      case 502:
      case 503:
      case 504:
        message.error('服务暂时不可用，请稍后再试');
        break;
      default:
        message.error(data?.detail || `请求失败 (${status})`);
    }
    
    return Promise.reject(error);
  }
);

export default api;