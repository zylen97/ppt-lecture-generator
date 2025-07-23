import React, { useState } from 'react';
import {
  Typography,
  Card,
  Upload,
  Button,
  message,
  Progress,
  List,
  Space,
  Tag,
  Alert,
  Row,
  Col,
  Statistic,
  Tabs,
  Table,
  Popconfirm,
  Tooltip,
  Modal,
  Form,
  Select,
  Divider,
  Empty,
} from 'antd';
import {
  UploadOutlined,
  FileTextOutlined,
  DeleteOutlined,
  EyeOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ReloadOutlined,
  SettingOutlined,
  PlusOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { FileService, TaskService, ConfigService } from '@/services';
import { FileInfo, Task, TaskStatus, FileType, GenerationConfig } from '@/types';
import { useCurrentProject } from '@/contexts';
import type { UploadFile, UploadProps } from 'antd/es/upload';
import type { ColumnsType } from 'antd/es/table';
import type { TabsProps } from 'antd';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { Dragger } = Upload;

const PPTProcessor: React.FC = () => {
  const queryClient = useQueryClient();
  const { currentProject } = useCurrentProject();
  
  // 状态管理
  const [uploadFileList, setUploadFileList] = useState<UploadFile[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<number[]>([]);
  const [configModalVisible, setConfigModalVisible] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [generationConfig, setGenerationConfig] = useState<GenerationConfig>({
    language: 'zh-CN',
    style: 'academic',
    detail_level: 'medium',
    include_examples: true,
    max_length: 2000,
  });
  
  // 数据查询 - 基于当前项目
  const { data: files = [], isLoading: filesLoading } = useQuery(
    ['pptFiles', currentProject?.id],
    () => currentProject ? FileService.getFiles({ 
      file_type: 'ppt', 
      project_id: currentProject.id 
    }) : Promise.resolve([]),
    { 
      refetchInterval: 30000,
      enabled: !!currentProject,
    }
  );
  
  const { data: tasks = [], isLoading: tasksLoading } = useQuery(
    ['pptTasks', currentProject?.id],
    () => currentProject ? TaskService.getTasks({ 
      task_type: 'ppt_to_script',
      project_id: currentProject.id 
    }) : Promise.resolve([]),
    { 
      refetchInterval: 5000,
      enabled: !!currentProject,
    }
  );
  
  const { data: apiConfigs = [] } = useQuery(
    'apiConfigs',
    () => ConfigService.getAPIConfigs({ limit: 100 })
  );
  
  // Mutations
  const uploadMutation = useMutation(FileService.uploadFile, {
    onSuccess: (data) => {
      message.success('PPT文件上传成功');
      queryClient.invalidateQueries(['pptFiles', currentProject?.id]);
      setUploadFileList([]);
    },
    onError: (error) => {
      message.error('文件上传失败');
      console.error('Upload error:', error);
    },
  });
  
  const createTaskMutation = useMutation(TaskService.createAndStartTask, {
    onSuccess: (data) => {
      message.success('讲稿生成任务已创建');
      queryClient.invalidateQueries(['pptTasks', currentProject?.id]);
    },
    onError: (error) => {
      message.error('任务创建失败');
      console.error('Task creation error:', error);
    },
  });
  
  const deleteFileMutation = useMutation(FileService.deleteFile, {
    onSuccess: () => {
      message.success('文件删除成功');
      queryClient.invalidateQueries(['pptFiles', currentProject?.id]);
      queryClient.invalidateQueries(['pptTasks', currentProject?.id]);
    },
  });
  
  // 上传配置
  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    fileList: uploadFileList,
    beforeUpload: (file) => {
      const isValidType = file.type === 'application/vnd.ms-powerpoint' || 
                         file.type === 'application/vnd.openxmlformats-officedocument.presentationml.presentation' ||
                         file.name.toLowerCase().endsWith('.ppt') ||
                         file.name.toLowerCase().endsWith('.pptx');
      
      if (!isValidType) {
        message.error('只能上传PPT或PPTX文件');
        return Upload.LIST_IGNORE;
      }
      
      const isLt100M = file.size! / 1024 / 1024 < 100;
      if (!isLt100M) {
        message.error('文件大小不能超过100MB');
        return Upload.LIST_IGNORE;
      }
      
      return false; // 阻止自动上传
    },
    onChange: (info) => {
      setUploadFileList(info.fileList);
    },
    onDrop: (e) => {
      console.log('Dropped files', e.dataTransfer.files);
    },
  };
  
  // 处理文件上传
  const handleUpload = async () => {
    if (!currentProject) {
      message.warning('请先选择一个项目');
      return;
    }
    
    if (uploadFileList.length === 0) {
      message.warning('请选择要上传的PPT文件');
      return;
    }
    
    const file = uploadFileList[0];
    if (file.originFileObj) {
      uploadMutation.mutate(file.originFileObj, {
        onProgress: (percentage: number) => {
          // 更新上传进度
          setUploadFileList(prev => 
            prev.map(f => 
              f.uid === file.uid 
                ? { ...f, percent: percentage }
                : f
            )
          );
        },
        project_id: currentProject.id,
      });
    }
  };
  
  // 开始生成讲稿
  const handleGenerateScript = (fileId: number) => {
    if (apiConfigs.length === 0) {
      message.error('请先配置API密钥');
      return;
    }
    
    const defaultConfig = apiConfigs.find(config => config.is_default) || apiConfigs[0];
    
    createTaskMutation.mutate({
      file_id: fileId,
      project_id: currentProject?.id,
      config: {
        ...generationConfig,
        api_config_id: defaultConfig.id,
      }
    });
  };
  
  // 批量操作
  const handleBatchDelete = () => {
    if (selectedFiles.length === 0) {
      message.warning('请选择要删除的文件');
      return;
    }
    
    selectedFiles.forEach(fileId => {
      deleteFileMutation.mutate(fileId);
    });
    setSelectedFiles([]);
  };
  
  // 获取任务状态颜色
  const getTaskStatusColor = (status: TaskStatus) => {
    const colors = {
      [TaskStatus.PENDING]: 'default',
      [TaskStatus.PROCESSING]: 'blue',
      [TaskStatus.COMPLETED]: 'success',
      [TaskStatus.FAILED]: 'error',
      [TaskStatus.CANCELLED]: 'warning',
    };
    return colors[status] || 'default';
  };
  
  // 获取任务状态文本
  const getTaskStatusText = (status: TaskStatus) => {
    const texts = {
      [TaskStatus.PENDING]: '等待中',
      [TaskStatus.PROCESSING]: '处理中',
      [TaskStatus.COMPLETED]: '已完成',
      [TaskStatus.FAILED]: '失败',
      [TaskStatus.CANCELLED]: '已取消',
    };
    return texts[status] || status;
  };
  
  // 文件表格列定义
  const fileColumns: ColumnsType<FileInfo> = [
    {
      title: '文件名',
      dataIndex: 'original_name',
      key: 'original_name',
      ellipsis: true,
      render: (name: string, record) => (
        <Space>
          <FileTextOutlined />
          <Text strong>{name}</Text>
        </Space>
      ),
    },
    {
      title: '文件大小',
      dataIndex: 'file_size_mb',
      key: 'file_size_mb',
      width: 100,
      render: (size: number) => `${size} MB`,
    },
    {
      title: '幻灯片数',
      dataIndex: 'slide_count',
      key: 'slide_count',
      width: 100,
      render: (count: number) => count || '-',
    },
    {
      title: '上传时间',
      dataIndex: 'upload_time',
      key: 'upload_time',
      width: 150,
      render: (time: string) => new Date(time).toLocaleString(),
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_, record) => (
        <Space>
          <Tooltip title="开始生成讲稿">
            <Button
              type="primary"
              size="small"
              icon={<PlayCircleOutlined />}
              onClick={() => handleGenerateScript(record.id)}
              loading={createTaskMutation.isLoading}
            >
              生成讲稿
            </Button>
          </Tooltip>
          
          <Tooltip title="删除文件">
            <Popconfirm
              title="确定要删除这个文件吗？"
              onConfirm={() => deleteFileMutation.mutate(record.id)}
            >
              <Button
                size="small"
                danger
                icon={<DeleteOutlined />}
                loading={deleteFileMutation.isLoading}
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ];
  
  // 任务表格列定义
  const taskColumns: ColumnsType<Task> = [
    {
      title: '任务ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '文件名',
      key: 'filename',
      render: (_, record) => {
        const file = files.find(f => f.id === record.file_id);
        return file ? file.original_name : '未知文件';
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: TaskStatus) => (
        <Tag color={getTaskStatusColor(status)}>
          {getTaskStatusText(status)}
        </Tag>
      ),
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      width: 150,
      render: (progress: number, record) => (
        <Progress
          percent={progress}
          size="small"
          status={record.status === TaskStatus.FAILED ? 'exception' : 'active'}
        />
      ),
    },
    {
      title: '开始时间',
      dataIndex: 'started_at',
      key: 'started_at',
      width: 150,
      render: (time: string) => time ? new Date(time).toLocaleString() : '-',
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Space>
          {record.status === TaskStatus.COMPLETED && (
            <Tooltip title="查看讲稿">
              <Button
                size="small"
                icon={<EyeOutlined />}
                onClick={() => {
                  // 跳转到讲稿页面
                  window.open(`/scripts?task_id=${record.id}`, '_blank');
                }}
              />
            </Tooltip>
          )}
        </Space>
      ),
    },
  ];
  
  // Tab配置
  const tabItems: TabsProps['items'] = [
    {
      key: 'upload',
      label: (
        <Space>
          <UploadOutlined />
          文件上传
        </Space>
      ),
      children: (
        <div>
          <Row gutter={[24, 24]}>
            <Col xs={24} lg={16}>
              <Card title="上传PPT文件" className="upload-card">
                <Dragger {...uploadProps} style={{ marginBottom: 16 }}>
                  <p className="ant-upload-drag-icon">
                    <UploadOutlined />
                  </p>
                  <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
                  <p className="ant-upload-hint">
                    支持单个文件上传，仅支持 PPT/PPTX 格式，文件大小不超过 100MB
                  </p>
                </Dragger>
                
                <Space>
                  <Button
                    type="primary"
                    onClick={handleUpload}
                    disabled={uploadFileList.length === 0}
                    loading={uploadMutation.isLoading}
                  >
                    开始上传
                  </Button>
                  <Button onClick={() => setUploadFileList([])}>
                    清空列表
                  </Button>
                </Space>
              </Card>
            </Col>
            
            <Col xs={24} lg={8}>
              <Card title="生成配置" className="config-card">
                <Form layout="vertical">
                  <Form.Item label="生成语言">
                    <Select 
                      value={generationConfig.language}
                      onChange={(value) => setGenerationConfig(prev => ({ ...prev, language: value }))}
                    >
                      <Option value="zh-CN">中文</Option>
                      <Option value="en-US">English</Option>
                    </Select>
                  </Form.Item>
                  
                  <Form.Item label="讲稿风格">
                    <Select 
                      value={generationConfig.style}
                      onChange={(value) => setGenerationConfig(prev => ({ ...prev, style: value }))}
                    >
                      <Option value="academic">学术风格</Option>
                      <Option value="conversational">对话风格</Option>
                      <Option value="formal">正式风格</Option>
                    </Select>
                  </Form.Item>
                  
                  <Form.Item label="详细程度">
                    <Select 
                      value={generationConfig.detail_level}
                      onChange={(value) => setGenerationConfig(prev => ({ ...prev, detail_level: value }))}
                    >
                      <Option value="brief">简洁</Option>
                      <Option value="medium">适中</Option>
                      <Option value="detailed">详细</Option>
                    </Select>
                  </Form.Item>
                </Form>
                
                {apiConfigs.length === 0 && (
                  <Alert
                    message="请先配置API密钥"
                    description="需要在系统设置中配置OpenAI API密钥才能生成讲稿"
                    type="warning"
                    showIcon
                    action={
                      <Button size="small" onClick={() => window.open('/settings', '_blank')}>
                        去设置
                      </Button>
                    }
                  />
                )}
              </Card>
            </Col>
          </Row>
        </div>
      ),
    },
    {
      key: 'files',
      label: (
        <Space>
          <FileTextOutlined />
          文件管理
        </Space>
      ),
      children: (
        <div>
          <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <Title level={4} style={{ margin: 0 }}>已上传的PPT文件</Title>
              <Text type="secondary">管理已上传的PPT文件，可以为文件生成讲稿</Text>
            </div>
            <Space>
              <Button icon={<ReloadOutlined />} onClick={() => queryClient.invalidateQueries('pptFiles')}>
                刷新
              </Button>
              {selectedFiles.length > 0 && (
                <Popconfirm
                  title={`确定要删除选中的${selectedFiles.length}个文件吗？`}
                  onConfirm={handleBatchDelete}
                >
                  <Button danger>批量删除</Button>
                </Popconfirm>
              )}
            </Space>
          </div>
          
          <Table
            columns={fileColumns}
            dataSource={files}
            rowKey="id"
            loading={filesLoading}
            rowSelection={{
              selectedRowKeys: selectedFiles,
              onChange: setSelectedFiles,
            }}
            pagination={{
              pageSize: 10,
              showSizeChanger: false,
              showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            }}
          />
        </div>
      ),
    },
    {
      key: 'tasks',
      label: (
        <Space>
          <SettingOutlined />
          任务状态
        </Space>
      ),
      children: (
        <div>
          <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <Title level={4} style={{ margin: 0 }}>讲稿生成任务</Title>
              <Text type="secondary">查看PPT转讲稿任务的执行状态和进度</Text>
            </div>
            <Button icon={<ReloadOutlined />} onClick={() => queryClient.invalidateQueries('pptTasks')}>
              刷新
            </Button>
          </div>
          
          <Table
            columns={taskColumns}
            dataSource={tasks}
            rowKey="id"
            loading={tasksLoading}
            pagination={{
              pageSize: 10,
              showSizeChanger: false,
              showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            }}
          />
        </div>
      ),
    },
  ];
  
  return (
    <div className="ppt-processor-page">
      {/* 页面标题 */}
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>PPT生成讲稿</Title>
        <Paragraph type="secondary">
          {currentProject ? 
            `项目：${currentProject.name} - 上传PPT文件并生成教学讲稿` : 
            '请在顶部选择一个项目以开始PPT处理流程'
          }
        </Paragraph>
      </div>

      {/* 无项目选中的提示 */}
      {!currentProject && (
        <Card style={{ marginBottom: 24 }}>
          <Empty
            description="未选择项目"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Space direction="vertical" align="center">
              <Text type="secondary">
                请选择一个项目以开始PPT文件处理和讲稿生成流程
              </Text>
              <Space>
                <Button 
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => window.open('/projects', '_blank')}
                >
                  创建项目
                </Button>
                <Button 
                  icon={<FileTextOutlined />}
                  onClick={() => window.open('/projects', '_blank')}
                >
                  浏览项目
                </Button>
              </Space>
            </Space>
          </Empty>
        </Card>
      )}

      {/* 只有选择了项目才显示以下内容 */}
      {currentProject && (
        <div>
      
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="已上传文件"
              value={files.length}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="处理中任务"
              value={tasks.filter(t => t.status === TaskStatus.PROCESSING).length}
              prefix={<PlayCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="已完成任务"
              value={tasks.filter(t => t.status === TaskStatus.COMPLETED).length}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>
      
      {/* 主要内容区域 */}
      <Card>
        <Tabs items={tabItems} />
      </Card>
        </div>
      )}
    </div>
  );
};

export default PPTProcessor;