import React, { useState, useMemo } from 'react';
import {
  Card,
  Upload,
  Button,
  Progress,
  Typography,
  Space,
  Alert,
  Divider,
  Row,
  Col,
  Statistic,
  message,
  Table,
  Tag,
  Tooltip,
  Switch,
  Input,
  Select,
  Form,
  Modal,
  Checkbox,
  List,
  Badge,
} from 'antd';
import {
  InboxOutlined,
  UploadOutlined,
  FileOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ReloadOutlined,
  SettingOutlined,
  FolderOpenOutlined,
} from '@ant-design/icons';
import type { UploadProps, UploadFile } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { FileService, TaskService } from '@/services';
import { formatFileSize } from '@/utils';
import { FileInfo, UploadState, GenerationConfig, TaskType } from '@/types';

const { Title, Paragraph, Text } = Typography;
const { Dragger } = Upload;
const { Option } = Select;

interface BatchUploadState {
  files: File[];
  uploadQueue: Array<{
    file: File;
    status: 'waiting' | 'uploading' | 'success' | 'error';
    progress: number;
    fileInfo?: FileInfo;
    error?: string;
  }>;
  currentUploading: number; // 当前上传的文件索引
  maxConcurrent: number;
  isUploading: boolean;
  isPaused: boolean;
}

interface BatchTaskModalProps {
  visible: boolean;
  files: FileInfo[];
  onCancel: () => void;
  onSuccess: () => void;
}

const BatchTaskModal: React.FC<BatchTaskModalProps> = ({
  visible,
  files,
  onCancel,
  onSuccess,
}) => {
  const [form] = Form.useForm();
  const [selectedFiles, setSelectedFiles] = useState<number[]>(files.map(f => f.id));
  const [isCreating, setIsCreating] = useState(false);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setIsCreating(true);

      const config: GenerationConfig = {
        total_duration: values.total_duration || 45,
        include_interaction: values.include_interaction || false,
        include_examples: values.include_examples || true,
        language: values.language || 'zh-CN',
        style: values.style || 'academic',
        no_questions: values.no_questions || false,
        no_blackboard: values.no_blackboard || false,
        target_audience: values.target_audience,
        course_name: values.course_name,
        chapter_name: values.chapter_name,
      };

      // 为所选文件创建任务
      const tasks = await Promise.allSettled(
        selectedFiles.map(fileId => 
          TaskService.createAndStartTask({
            file_id: fileId,
            config,
          })
        )
      );

      const successful = tasks.filter(t => t.status === 'fulfilled').length;
      const failed = tasks.filter(t => t.status === 'rejected').length;

      if (successful > 0) {
        message.success(`成功创建 ${successful} 个任务${failed > 0 ? `，${failed} 个失败` : ''}`);
        onSuccess();
      } else {
        message.error('所有任务创建失败');
      }
    } catch (error) {
      message.error('批量任务创建失败');
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <Modal
      title="批量创建任务"
      open={visible}
      onCancel={onCancel}
      onOk={handleSubmit}
      confirmLoading={isCreating}
      width={800}
      destroyOnHidden
    >
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        <div>
          <Text strong>选择文件（{selectedFiles.length}/{files.length}）</Text>
          <div style={{ marginTop: 8 }}>
            <Space wrap>
              <Button
                size="small"
                onClick={() => setSelectedFiles(files.map(f => f.id))}
              >
                全选
              </Button>
              <Button
                size="small"
                onClick={() => setSelectedFiles([])}
              >
                取消全选
              </Button>
            </Space>
          </div>
          
          <div style={{ maxHeight: 200, overflow: 'auto', marginTop: 8, border: '1px solid #d9d9d9', borderRadius: 6 }}>
            <List
              size="small"
              dataSource={files}
              renderItem={file => (
                <List.Item
                  style={{ padding: '8px 12px' }}
                  onClick={() => {
                    if (selectedFiles.includes(file.id)) {
                      setSelectedFiles(prev => prev.filter(id => id !== file.id));
                    } else {
                      setSelectedFiles(prev => [...prev, file.id]);
                    }
                  }}
                  className="cursor-pointer"
                >
                  <Space>
                    <Checkbox checked={selectedFiles.includes(file.id)} />
                    <FileOutlined />
                    <div>
                      <Text>{file.original_name}</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        {formatFileSize(file.file_size)}
                        {file.slide_count && ` • ${file.slide_count}张幻灯片`}
                      </Text>
                    </div>
                  </Space>
                </List.Item>
              )}
            />
          </div>
        </div>

        <Divider />

        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item
                label="预计时长（分钟）"
                name="total_duration"
                initialValue={45}
              >
                <Input type="number" min={5} max={180} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                label="语言"
                name="language"
                initialValue="zh-CN"
              >
                <Select>
                  <Option value="zh-CN">中文</Option>
                  <Option value="en-US">English</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item
                label="教学风格"
                name="style"
                initialValue="academic"
              >
                <Select>
                  <Option value="academic">学术型</Option>
                  <Option value="practical">实用型</Option>
                  <Option value="interactive">互动型</Option>
                  <Option value="storytelling">叙述型</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item label="目标受众" name="target_audience">
                <Input placeholder="例如：本科生、研究生、专业人士等" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item label="课程名称" name="course_name">
                <Input placeholder="例如：计算机科学导论" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item label="章节名称" name="chapter_name">
                <Input placeholder="例如：第一章 概述" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col xs={24} sm={8}>
              <Form.Item name="include_interaction" valuePropName="checked">
                <Checkbox>包含互动环节</Checkbox>
              </Form.Item>
            </Col>
            <Col xs={24} sm={8}>
              <Form.Item name="include_examples" valuePropName="checked" initialValue={true}>
                <Checkbox>包含案例说明</Checkbox>
              </Form.Item>
            </Col>
            <Col xs={24} sm={8}>
              <Form.Item name="no_questions" valuePropName="checked">
                <Checkbox>不生成提问环节</Checkbox>
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Space>
    </Modal>
  );
};

const UploadPage: React.FC = () => {
  // 批量上传状态
  const [batchUploadState, setBatchUploadState] = useState<BatchUploadState>({
    files: [],
    uploadQueue: [],
    currentUploading: -1,
    maxConcurrent: 2,
    isUploading: false,
    isPaused: false,
  });

  const [uploadedFiles, setUploadedFiles] = useState<FileInfo[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<number[]>([]);
  const [batchMode, setBatchMode] = useState(true);
  const [batchTaskModalVisible, setBatchTaskModalVisible] = useState(false);

  // 单文件上传状态（用于兼容原有功能）
  const [singleUploadState, setSingleUploadState] = useState<UploadState>({
    progress: 0,
    status: 'idle',
  });

  // 文件验证
  const validateFile = (file: File): { valid: boolean; message?: string } => {
    const typeValidation = FileService.validateFileType(file);
    if (!typeValidation.valid) {
      return typeValidation;
    }

    const sizeValidation = FileService.validateFileSize(file);
    if (!sizeValidation.valid) {
      return sizeValidation;
    }

    return { valid: true };
  };

  // 批量文件选择处理
  const handleBatchFileSelect = (fileList: File[]) => {
    const validFiles: File[] = [];
    const invalidFiles: string[] = [];

    fileList.forEach(file => {
      const validation = validateFile(file);
      if (validation.valid) {
        validFiles.push(file);
      } else {
        invalidFiles.push(`${file.name}: ${validation.message}`);
      }
    });

    if (invalidFiles.length > 0) {
      message.error(`以下文件不符合要求：\n${invalidFiles.join('\n')}`);
    }

    if (validFiles.length > 0) {
      setBatchUploadState(prev => ({
        ...prev,
        files: [...prev.files, ...validFiles],
        uploadQueue: [
          ...prev.uploadQueue,
          ...validFiles.map(file => ({
            file,
            status: 'waiting' as const,
            progress: 0,
          }))
        ],
      }));
    }
  };

  // 开始批量上传
  const startBatchUpload = async () => {
    setBatchUploadState(prev => ({
      ...prev,
      isUploading: true,
      isPaused: false,
    }));

    await processBatchUpload();
  };

  // 处理批量上传队列
  const processBatchUpload = async () => {
    const { uploadQueue, maxConcurrent } = batchUploadState;
    const waitingFiles = uploadQueue.filter(item => item.status === 'waiting');
    
    if (waitingFiles.length === 0) {
      setBatchUploadState(prev => ({ ...prev, isUploading: false }));
      return;
    }

    // 限制并发上传数量
    const currentUploading = uploadQueue.filter(item => item.status === 'uploading').length;
    const canUpload = Math.min(maxConcurrent - currentUploading, waitingFiles.length);

    for (let i = 0; i < canUpload; i++) {
      const fileItem = waitingFiles[i];
      uploadSingleFileInQueue(fileItem.file);
    }
  };

  // 在队列中上传单个文件
  const uploadSingleFileInQueue = async (file: File) => {
    setBatchUploadState(prev => ({
      ...prev,
      uploadQueue: prev.uploadQueue.map(item =>
        item.file === file ? { ...item, status: 'uploading' as const } : item
      ),
    }));

    try {
      const response = await FileService.uploadFile(
        file,
        (percentage) => {
          setBatchUploadState(prev => ({
            ...prev,
            uploadQueue: prev.uploadQueue.map(item =>
              item.file === file ? { ...item, progress: percentage } : item
            ),
          }));
        }
      );

      if (response.success && response.file_id) {
        const fileInfo = await FileService.getFileInfo(response.file_id);
        
        setBatchUploadState(prev => ({
          ...prev,
          uploadQueue: prev.uploadQueue.map(item =>
            item.file === file 
              ? { ...item, status: 'success' as const, progress: 100, fileInfo }
              : item
          ),
        }));

        setUploadedFiles(prev => [fileInfo, ...prev]);
      } else {
        throw new Error(response.message || '上传失败');
      }
    } catch (error) {
      setBatchUploadState(prev => ({
        ...prev,
        uploadQueue: prev.uploadQueue.map(item =>
          item.file === file 
            ? { ...item, status: 'error' as const, error: error instanceof Error ? error.message : '上传失败' }
            : item
        ),
      }));
    }

    // 继续处理队列中的下一个文件
    setTimeout(() => processBatchUpload(), 500);
  };

  // 暂停/恢复批量上传
  const toggleBatchUpload = () => {
    setBatchUploadState(prev => ({
      ...prev,
      isPaused: !prev.isPaused,
    }));
  };

  // 清空上传队列
  const clearUploadQueue = () => {
    setBatchUploadState({
      files: [],
      uploadQueue: [],
      currentUploading: -1,
      maxConcurrent: 2,
      isUploading: false,
      isPaused: false,
    });
  };

  // 从队列中移除文件
  const removeFromQueue = (file: File) => {
    setBatchUploadState(prev => ({
      ...prev,
      files: prev.files.filter(f => f !== file),
      uploadQueue: prev.uploadQueue.filter(item => item.file !== file),
    }));
  };

  // 重试失败的文件
  const retryFailedFile = (file: File) => {
    setBatchUploadState(prev => ({
      ...prev,
      uploadQueue: prev.uploadQueue.map(item =>
        item.file === file 
          ? { ...item, status: 'waiting' as const, progress: 0, error: undefined }
          : item
      ),
    }));
    
    if (!batchUploadState.isUploading) {
      startBatchUpload();
    }
  };

  // 单文件上传处理（向后兼容）
  const handleSingleUpload = async (file: File) => {
    setSingleUploadState({
      file,
      progress: 0,
      status: 'uploading',
    });

    try {
      const response = await FileService.uploadFile(
        file,
        (percentage) => {
          setSingleUploadState(prev => ({ ...prev, progress: percentage }));
        }
      );

      if (response.success && response.file_id) {
        const fileInfo = await FileService.getFileInfo(response.file_id);
        
        setSingleUploadState({
          progress: 100,
          status: 'success',
          fileInfo,
        });

        setUploadedFiles(prev => [fileInfo, ...prev]);
        message.success('文件上传成功！');
      } else {
        throw new Error(response.message || '上传失败');
      }
    } catch (error) {
      setSingleUploadState(prev => ({
        ...prev,
        status: 'error',
        error: error instanceof Error ? error.message : '上传失败',
      }));
      message.error('文件上传失败');
    }
  };

  // 上传组件属性
  const uploadProps: UploadProps = {
    name: 'file',
    multiple: batchMode,
    accept: '.ppt,.pptx',
    beforeUpload: (file, fileList) => {
      const validation = validateFile(file);
      if (!validation.valid) {
        message.error(validation.message);
        return false;
      }
      return false; // 阻止默认上传，使用自定义处理
    },
    onChange: ({ fileList }) => {
      if (batchMode && fileList.length > 0) {
        const files = fileList
          .filter(f => f.originFileObj)
          .map(f => f.originFileObj as File);
        handleBatchFileSelect(files);
      }
    },
    customRequest: ({ file }) => {
      if (!batchMode && file instanceof File) {
        handleSingleUpload(file);
      }
    },
    showUploadList: false,
  };

  // 批量任务创建
  const handleBatchTaskCreation = () => {
    if (selectedFiles.length === 0) {
      message.warning('请先选择要处理的文件');
      return;
    }
    
    const selectedFileInfos = uploadedFiles.filter(f => selectedFiles.includes(f.id));
    setBatchTaskModalVisible(true);
  };

  // 队列统计
  const queueStats = useMemo(() => {
    const { uploadQueue } = batchUploadState;
    return {
      total: uploadQueue.length,
      waiting: uploadQueue.filter(item => item.status === 'waiting').length,
      uploading: uploadQueue.filter(item => item.status === 'uploading').length,
      success: uploadQueue.filter(item => item.status === 'success').length,
      error: uploadQueue.filter(item => item.status === 'error').length,
    };
  }, [batchUploadState.uploadQueue]);

  // 队列表格列定义
  const queueColumns: ColumnsType<typeof batchUploadState.uploadQueue[0]> = [
    {
      title: '文件名',
      key: 'filename',
      render: (_, record) => (
        <Space>
          <FileOutlined />
          <div>
            <Text ellipsis style={{ maxWidth: 200 }}>
              {record.file.name}
            </Text>
            <br />
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {formatFileSize(record.file.size)}
            </Text>
          </div>
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string, record) => {
        const statusConfig = {
          waiting: { color: 'default', text: '等待中' },
          uploading: { color: 'processing', text: '上传中' },
          success: { color: 'success', text: '成功' },
          error: { color: 'error', text: '失败' },
        };
        
        return <Tag color={statusConfig[status as keyof typeof statusConfig].color}>
          {statusConfig[status as keyof typeof statusConfig].text}
        </Tag>;
      },
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
          status={record.status === 'error' ? 'exception' : 
                 record.status === 'success' ? 'success' : 'active'}
        />
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Space size="small">
          {record.status === 'error' && (
            <Tooltip title="重试">
              <Button
                type="text"
                icon={<ReloadOutlined />}
                size="small"
                onClick={() => retryFailedFile(record.file)}
              />
            </Tooltip>
          )}
          
          {['waiting', 'error'].includes(record.status) && (
            <Tooltip title="移除">
              <Button
                type="text"
                icon={<DeleteOutlined />}
                size="small"
                onClick={() => removeFromQueue(record.file)}
              />
            </Tooltip>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div className="upload-page">
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>上传PPT文件</Title>
        <Paragraph type="secondary">
          上传您的PowerPoint文件，支持单个或批量上传，系统将自动分析并生成讲稿
        </Paragraph>
        
        <Space>
          <Switch
            checked={batchMode}
            onChange={setBatchMode}
            checkedChildren="批量模式"
            unCheckedChildren="单文件模式"
          />
          <Text type="secondary">
            {batchMode ? '支持多个文件同时上传和处理' : '单个文件上传模式'}
          </Text>
        </Space>
      </div>

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={batchMode ? 24 : 16}>
          <Card 
            title={
              <Space>
                <FolderOpenOutlined />
                文件上传
                {batchMode && queueStats.total > 0 && (
                  <Badge count={queueStats.total} />
                )}
              </Space>
            }
            extra={
              batchMode && batchUploadState.files.length > 0 && (
                <Space>
                  {!batchUploadState.isUploading ? (
                    <Button
                      type="primary"
                      icon={<PlayCircleOutlined />}
                      onClick={startBatchUpload}
                      disabled={queueStats.waiting === 0}
                    >
                      开始上传
                    </Button>
                  ) : (
                    <Button
                      icon={batchUploadState.isPaused ? <PlayCircleOutlined /> : <PauseCircleOutlined />}
                      onClick={toggleBatchUpload}
                    >
                      {batchUploadState.isPaused ? '继续' : '暂停'}
                    </Button>
                  )}
                  
                  <Button
                    icon={<DeleteOutlined />}
                    onClick={clearUploadQueue}
                  >
                    清空队列
                  </Button>
                </Space>
              )
            }
          >
            {/* 上传区域 */}
            {(!batchMode && singleUploadState.status === 'idle') || 
             (batchMode && (queueStats.total === 0 || queueStats.waiting + queueStats.error > 0)) ? (
              <Dragger {...uploadProps} style={{ padding: '40px 20px' }}>
                <p className="ant-upload-drag-icon">
                  <InboxOutlined style={{ fontSize: 48, color: '#1890ff' }} />
                </p>
                <p className="ant-upload-text">
                  点击或拖拽文件到此区域上传
                </p>
                <p className="ant-upload-hint">
                  支持 .ppt 和 .pptx 格式，文件大小限制100MB
                  {batchMode && '，支持同时选择多个文件'}
                </p>
              </Dragger>
            ) : (
              <div>
                {!batchMode && singleUploadState.file && (
                  // 单文件上传进度显示
                  <div style={{ padding: '40px 20px', textAlign: 'center' }}>
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <FileOutlined style={{ fontSize: 48, color: '#1890ff' }} />
                      <Text strong>{singleUploadState.file.name}</Text>
                      <Text type="secondary">
                        {formatFileSize(singleUploadState.file.size)}
                      </Text>

                      <Progress
                        percent={singleUploadState.progress}
                        status={
                          singleUploadState.status === 'error' ? 'exception' :
                          singleUploadState.status === 'success' ? 'success' : 'active'
                        }
                        style={{ maxWidth: 400 }}
                      />

                      {singleUploadState.status === 'success' && (
                        <Alert
                          message="上传成功"
                          description="文件已成功上传"
                          type="success"
                          showIcon
                          style={{ textAlign: 'left' }}
                        />
                      )}

                      {singleUploadState.status === 'error' && (
                        <Alert
                          message="上传失败"
                          description={singleUploadState.error}
                          type="error"
                          showIcon
                          style={{ textAlign: 'left' }}
                        />
                      )}
                    </Space>
                  </div>
                )}

                {batchMode && batchUploadState.uploadQueue.length > 0 && (
                  // 批量上传队列显示
                  <div>
                    <div style={{ marginBottom: 16 }}>
                      <Row gutter={16}>
                        <Col span={6}>
                          <Statistic
                            title="总文件数"
                            value={queueStats.total}
                            prefix={<FileOutlined />}
                          />
                        </Col>
                        <Col span={6}>
                          <Statistic
                            title="等待上传"
                            value={queueStats.waiting}
                            valueStyle={{ color: '#faad14' }}
                          />
                        </Col>
                        <Col span={6}>
                          <Statistic
                            title="上传成功"
                            value={queueStats.success}
                            valueStyle={{ color: '#52c41a' }}
                            prefix={<CheckCircleOutlined />}
                          />
                        </Col>
                        <Col span={6}>
                          <Statistic
                            title="上传失败"
                            value={queueStats.error}
                            valueStyle={{ color: '#f5222d' }}
                            prefix={<ExclamationCircleOutlined />}
                          />
                        </Col>
                      </Row>
                    </div>

                    <Table
                      columns={queueColumns}
                      dataSource={batchUploadState.uploadQueue}
                      rowKey={(record) => record.file.name + record.file.size}
                      pagination={false}
                      size="small"
                      scroll={{ y: 300 }}
                    />
                  </div>
                )}
              </div>
            )}
          </Card>
        </Col>

        {/* 右侧信息面板（单文件模式时显示） */}
        {!batchMode && (
          <Col xs={24} lg={8}>
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <Card title="上传要求" size="small">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Text strong>支持格式：</Text>
                    <Text>.ppt, .pptx</Text>
                  </div>
                  <div>
                    <Text strong>文件大小：</Text>
                    <Text>最大 100MB</Text>
                  </div>
                  <div>
                    <Text strong>建议内容：</Text>
                    <Text>清晰的文字和图表</Text>
                  </div>
                </Space>
              </Card>

              <Card title="处理流程" size="small">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>1. 上传PPT文件</div>
                  <div>2. 系统解析文件结构</div>
                  <div>3. AI分析幻灯片内容</div>
                  <div>4. 生成教学讲稿</div>
                  <div>5. 下载或在线编辑</div>
                </Space>
              </Card>
            </Space>
          </Col>
        )}
      </Row>

      {/* 已上传文件管理 */}
      {uploadedFiles.length > 0 && (
        <Card
          title="文件管理"
          style={{ marginTop: 24 }}
          extra={
            <Space>
              <Text type="secondary">共 {uploadedFiles.length} 个文件</Text>
              {batchMode && uploadedFiles.length > 1 && (
                <>
                  <Button
                    type="primary"
                    icon={<SettingOutlined />}
                    onClick={handleBatchTaskCreation}
                    disabled={selectedFiles.length === 0}
                  >
                    批量创建任务 ({selectedFiles.length})
                  </Button>
                </>
              )}
            </Space>
          }
        >
          <Table
            rowSelection={batchMode && uploadedFiles.length > 1 ? {
              selectedRowKeys: selectedFiles,
              onChange: setSelectedFiles,
            } : undefined}
            dataSource={uploadedFiles}
            rowKey="id"
            pagination={{ pageSize: 10 }}
            columns={[
              {
                title: '文件名',
                key: 'filename',
                render: (_, record) => (
                  <Space>
                    <FileOutlined />
                    <div>
                      <Text strong>{record.original_name}</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        {formatFileSize(record.file_size)}
                        {record.slide_count && ` • ${record.slide_count}张幻灯片`}
                      </Text>
                    </div>
                  </Space>
                ),
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
                width: 150,
                render: (_, record) => (
                  <Space>
                    <Button
                      type="primary"
                      size="small"
                      onClick={() => {
                        window.location.href = `/tasks?file_id=${record.id}`;
                      }}
                    >
                      生成讲稿
                    </Button>
                    <Button
                      danger
                      size="small"
                      icon={<DeleteOutlined />}
                      onClick={async () => {
                        try {
                          await FileService.deleteFile(record.id);
                          setUploadedFiles(prev => prev.filter(f => f.id !== record.id));
                          message.success('文件删除成功');
                        } catch (error) {
                          message.error('文件删除失败');
                        }
                      }}
                    />
                  </Space>
                ),
              },
            ]}
          />
        </Card>
      )}

      {/* 批量任务创建模态框 */}
      <BatchTaskModal
        visible={batchTaskModalVisible}
        files={uploadedFiles.filter(f => selectedFiles.includes(f.id))}
        onCancel={() => setBatchTaskModalVisible(false)}
        onSuccess={() => {
          setBatchTaskModalVisible(false);
          setSelectedFiles([]);
          // 跳转到任务页面
          setTimeout(() => {
            window.location.href = '/tasks';
          }, 1000);
        }}
      />
    </div>
  );
};

export default UploadPage;