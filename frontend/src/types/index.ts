// API响应基础类型
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

// 用户相关类型
export interface User {
  id: number;
  username: string;
  email?: string;
  created_at: string;
  updated_at: string;
}

// 文件相关类型
export enum FileType {
  PPT = "ppt",
  AUDIO = "audio",
  VIDEO = "video"
}

export interface FileInfo {
  id: number;
  filename: string;
  original_name: string;
  file_path: string;
  file_size: number;
  file_size_mb: number;
  file_type: FileType;
  
  // PPT相关字段
  slide_count?: number;
  
  // 音视频相关字段
  duration?: number; // 时长（秒）
  duration_formatted?: string; // 格式化时长 (HH:MM:SS)
  sample_rate?: number; // 采样率
  channels?: number; // 声道数
  bitrate?: number; // 比特率
  codec?: string; // 编码格式
  resolution?: string; // 视频分辨率
  fps?: number; // 帧率
  
  file_hash?: string;
  upload_time: string;
  user_id?: number;
  project_id?: number; // 关联项目ID
}

export interface FileUploadResponse {
  success: boolean;
  message: string;
  file_id?: number;
}

// 任务相关类型
export enum TaskType {
  PPT_TO_SCRIPT = "ppt_to_script",
  AUDIO_VIDEO_TO_SCRIPT = "audio_video_to_script",
  SCRIPT_EDIT = "script_edit",
  BATCH_PROCESS = "batch_process"
}

export enum TaskStatus {
  PENDING = "pending",
  PROCESSING = "processing",
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled"
}

export interface Task {
  id: number;
  file_id: number;
  task_type: TaskType;
  status: TaskStatus;
  progress: number;
  config_snapshot?: Record<string, any>;
  created_at?: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  user_id?: number;
  project_id?: number; // 关联项目ID
  duration?: number;
}

export interface TaskProgress {
  task_id: number;
  progress: number;
  message: string;
  current_step?: string;
}

// 讲稿相关类型
export interface Script {
  id: number;
  task_id: number;
  title: string;
  content: string;
  format: string;
  version: number;
  word_count?: number;
  estimated_duration?: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  project_id?: number; // 关联项目ID
  file_size: number;
  reading_time?: number;
}

export interface ScriptSummary {
  id: number;
  title: string;
  version: number;
  word_count?: number;
  estimated_duration?: number;
  created_at: string;
  is_active: boolean;
}

// API配置相关类型
export interface APIConfig {
  id: number;
  name: string;
  endpoint: string;
  model: string;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  user_id?: number;
  api_key_masked: string;
}

export interface APIConfigCreate {
  name: string;
  endpoint: string;
  model: string;
  api_key: string;
  is_default?: boolean;
}

export interface APITestRequest {
  endpoint: string;
  api_key: string;
  model: string;
}

export interface APITestResponse {
  success: boolean;
  message: string;
  latency_ms?: number;
}

// 生成配置类型
export interface GenerationConfig {
  total_duration: number;
  include_interaction: boolean;
  include_examples: boolean;
  language: string;
  style: string;
  no_questions: boolean;
  no_blackboard: boolean;
  target_audience?: string;
  course_name?: string;
  chapter_name?: string;
}

// 统计信息类型
export interface GenerationStats {
  start_time: number;
  total_time: number;
  total_slides: number;
  successful_analyses: number;
  failed_analyses: number;
  total_tokens: number;
  total_length: number;
}

// WebSocket消息类型
export interface WebSocketMessage {
  type: 'progress' | 'status_change' | 'tasks_update' | 'error' | 'complete';
  task_id?: number;
  data: any;
  timestamp?: string;
}

// 上传状态类型
export interface UploadState {
  file?: File;
  progress: number;
  status: 'idle' | 'uploading' | 'success' | 'error';
  error?: string;
  fileInfo?: FileInfo;
}

// 表格列配置
export interface TableColumn {
  title: string;
  dataIndex: string;
  key: string;
  width?: number;
  render?: (text: any, record: any, index: number) => React.ReactNode;
  sorter?: boolean;
  filters?: Array<{ text: string; value: any }>;
}

// 项目相关类型
export interface Project {
  id: number;
  name: string;
  description?: string;
  course_code?: string;
  semester?: string;
  instructor?: string;
  target_audience?: string;
  cover_image?: string;
  total_files: number;
  total_tasks: number;
  total_scripts: number;
  total_duration?: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  user_id?: number;
  statistics?: ProjectStatistics;
}

export interface ProjectCreate {
  name: string;
  description?: string;
  course_code?: string;
  semester?: string;
  instructor?: string;
  target_audience?: string;
  cover_image?: string;
  is_active?: boolean;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
  course_code?: string;
  semester?: string;
  instructor?: string;
  target_audience?: string;
  cover_image?: string;
  is_active?: boolean;
}

export interface ProjectSummary {
  id: number;
  name: string;
  description?: string;
  course_code?: string;
  semester?: string;
  instructor?: string;
  cover_image?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  file_count: number;
  task_count: number;
  script_count: number;
  completion_rate: number;
}

export interface ProjectStatistics {
  total_files: number;
  total_tasks: number;
  total_scripts: number;
  total_duration?: number;
  total_word_count?: number;
  completion_rate: number;
  status_summary: {
    total: number;
    pending: number;
    processing: number;
    completed: number;
    failed: number;
  };
}

export interface ProjectListResponse {
  items: ProjectSummary[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}

export interface ProjectTemplate {
  id: string;
  name: string;
  description: string;
  fields: string[];
  example: Record<string, string>;
}

export interface ProjectTemplateResponse {
  templates: ProjectTemplate[];
}

// 项目操作相关类型
export interface ProjectActionRequest {
  action: 'archive' | 'restore' | 'delete';
  force?: boolean;
}

export interface ProjectActionResponse {
  success: boolean;
  message: string;
  data?: any;
}