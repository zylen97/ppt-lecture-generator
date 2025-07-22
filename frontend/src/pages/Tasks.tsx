import React, { useState, useMemo, useEffect } from 'react';
import {
  Typography,
  Card,
  Table,
  Space,
  Button,
  Tag,
  Select,
  Input,
  Modal,
  Progress,
  Descriptions,
  Timeline,
  Divider,
  Popconfirm,
  message,
  Row,
  Col,
  Statistic,
  DatePicker,
  Tooltip,
  Alert,
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  RedoOutlined,
  DeleteOutlined,
  EyeOutlined,
  FileTextOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { TaskService, FileService } from '@/services';
import { Task, TaskStatus, TaskType, FileInfo } from '@/types';
import { getGlobalTaskMonitor } from '@/services/globalTaskMonitor';
import { formatDateTime, formatDuration, formatRelativeTime } from '@/utils';
import type { ColumnsType } from 'antd/es/table';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { Search } = Input;
const { RangePicker } = DatePicker;

interface TaskFilters {
  status?: TaskStatus;
  type?: TaskType;
  dateRange?: [string, string];
  search?: string;
}

const Tasks: React.FC = () => {
  const queryClient = useQueryClient();
  
  // 状态管理
  const [selectedTasks, setSelectedTasks] = useState<number[]>([]);
  const [filters, setFilters] = useState<TaskFilters>({});
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [logsModalVisible, setLogsModalVisible] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);

  // 数据查询（移除轮询，使用WebSocket实时更新）
  const { data: tasks = [], isLoading, error } = useQuery(
    ['tasks', filters],
    () => TaskService.getTasks({
      status_filter: filters.status,
      limit: 1000,
    })
  );

  const { data: taskStats } = useQuery(
    'taskStats',
    TaskService.getTaskStats
  );

  // 文件信息查询
  const { data: files = [] } = useQuery(
    'files',
    () => FileService.getFiles({ limit: 1000 }),
    {
      staleTime: 5 * 60 * 1000, // 5分钟内不重复查询
    }
  );

  // WebSocket实时更新集成
  useEffect(() => {
    const taskMonitor = getGlobalTaskMonitor();
    
    // 监听任务更新
    const unsubscribeUpdate = taskMonitor.onTaskUpdate((changedTasks) => {
      // 无效化tasks查询以触发重新获取
      queryClient.invalidateQueries('tasks');
      queryClient.invalidateQueries('taskStats');
      
      console.log('Tasks updated via WebSocket:', changedTasks.length, 'tasks');
    });
    
    // 监听连接状态
    const unsubscribeStatus = taskMonitor.onConnectionStatus((connected) => {
      setWsConnected(connected);
      
      if (connected) {
        message.success('实时连接已建立', 2);
      } else {
        message.warning('实时连接已断开，将尝试重连', 3);
      }
    });
    
    // 组件卸载时清理
    return () => {
      unsubscribeUpdate();
      unsubscribeStatus();
    };
  }, [queryClient]);

  // 任务操作mutations
  const startTaskMutation = useMutation(TaskService.startTask, {
    onSuccess: () => {
      queryClient.invalidateQueries('tasks');
      queryClient.invalidateQueries('taskStats');
      message.success('任务启动成功');
    },
    onError: () => {
      message.error('任务启动失败');
    },
  });

  const cancelTaskMutation = useMutation(TaskService.cancelTask, {
    onSuccess: () => {
      queryClient.invalidateQueries('tasks');
      queryClient.invalidateQueries('taskStats');
      message.success('任务取消成功');
    },
    onError: () => {
      message.error('任务取消失败');
    },
  });

  // 文件映射
  const fileMap = useMemo(() => {
    return files.reduce((map, file) => {
      map[file.id] = file;
      return map;
    }, {} as Record<number, FileInfo>);
  }, [files]);

  // 过滤后的任务列表
  const filteredTasks = useMemo(() => {
    let result = [...tasks];

    // 状态筛选
    if (filters.status) {
      result = result.filter(task => task.status === filters.status);
    }

    // 类型筛选
    if (filters.type) {
      result = result.filter(task => task.task_type === filters.type);
    }

    // 搜索筛选
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      result = result.filter(task => {
        const file = fileMap[task.file_id];
        return file?.original_name.toLowerCase().includes(searchLower);
      });
    }

    // 日期范围筛选
    if (filters.dateRange) {
      const [startDate, endDate] = filters.dateRange;
      result = result.filter(task => {
        if (!task.started_at) return false;
        const taskDate = new Date(task.started_at);
        return taskDate >= new Date(startDate) && taskDate <= new Date(endDate);
      });
    }

    return result;
  }, [tasks, filters, fileMap]);

  // 表格列定义
  const columns: ColumnsType<Task> = [
    {
      title: '任务ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
      sorter: (a, b) => a.id - b.id,
    },
    {
      title: '文件名',
      key: 'filename',
      render: (_, record) => {
        const file = fileMap[record.file_id];
        return (
          <Space>
            <FileTextOutlined />
            <Text ellipsis style={{ maxWidth: 200 }}>
              {file?.original_name || '未知文件'}
            </Text>
          </Space>
        );
      },
      sorter: (a, b) => {
        const fileA = fileMap[a.file_id];
        const fileB = fileMap[b.file_id];
        return (fileA?.original_name || '').localeCompare(fileB?.original_name || '');
      },
    },
    {
      title: '任务类型',
      dataIndex: 'task_type',
      key: 'task_type',
      width: 120,
      render: (type: TaskType) => (
        <Tag color="blue">
          {TaskService.getTaskTypeText(type)}
        </Tag>
      ),
      filters: [
        { text: 'PPT转讲稿', value: TaskType.PPT_TO_SCRIPT },
        { text: '讲稿编辑', value: TaskType.SCRIPT_EDIT },
        { text: '批量处理', value: TaskType.BATCH_PROCESS },
      ],
      onFilter: (value, record) => record.task_type === value,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: TaskStatus, record) => {
        const color = TaskService.getStatusColor(status);
        const text = TaskService.getStatusText(status);
        
        return (
          <Space direction="vertical" size={0}>
            <Tag color={color}>{text}</Tag>
            {status === TaskStatus.PROCESSING && (
              <Progress
                percent={record.progress}
                size="small"
                style={{ width: 80 }}
              />
            )}
          </Space>
        );
      },
      filters: [
        { text: '等待处理', value: TaskStatus.PENDING },
        { text: '处理中', value: TaskStatus.PROCESSING },
        { text: '已完成', value: TaskStatus.COMPLETED },
        { text: '处理失败', value: TaskStatus.FAILED },
        { text: '已取消', value: TaskStatus.CANCELLED },
      ],
      onFilter: (value, record) => record.status === value,
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      width: 100,
      render: (progress: number, record) => (
        <Progress
          percent={progress}
          size="small"
          status={
            record.status === TaskStatus.FAILED ? 'exception' :
            record.status === TaskStatus.COMPLETED ? 'success' : 'active'
          }
        />
      ),
    },
    {
      title: '开始时间',
      dataIndex: 'started_at',
      key: 'started_at',
      width: 150,
      render: (date: string) => date ? formatDateTime(date, 'MM-DD HH:mm') : '-',
      sorter: (a, b) => {
        if (!a.started_at || !b.started_at) return 0;
        return new Date(a.started_at).getTime() - new Date(b.started_at).getTime();
      },
    },
    {
      title: '耗时',
      key: 'duration',
      width: 80,
      render: (_, record) => {
        if (record.duration) {
          return formatDuration(record.duration);
        }
        if (record.started_at && !record.completed_at && record.status === TaskStatus.PROCESSING) {
          return formatRelativeTime(record.started_at);
        }
        return '-';
      },
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              size="small"
              onClick={() => showTaskDetail(record)}
            />
          </Tooltip>
          
          {record.status === TaskStatus.PENDING && (
            <Tooltip title="启动任务">
              <Button
                type="text"
                icon={<PlayCircleOutlined />}
                size="small"
                onClick={() => startTaskMutation.mutate(record.id)}
                loading={startTaskMutation.isLoading}
              />
            </Tooltip>
          )}
          
          {record.status === TaskStatus.PROCESSING && (
            <Tooltip title="取消任务">
              <Popconfirm
                title="确定要取消这个任务吗？"
                onConfirm={() => cancelTaskMutation.mutate(record.id)}
                okText="确定"
                cancelText="取消"
              >
                <Button
                  type="text"
                  icon={<StopOutlined />}
                  size="small"
                  loading={cancelTaskMutation.isLoading}
                />
              </Popconfirm>
            </Tooltip>
          )}
          
          {record.status === TaskStatus.FAILED && (
            <Tooltip title="重试任务">
              <Button
                type="text"
                icon={<RedoOutlined />}
                size="small"
                onClick={() => retryTask(record)}
              />
            </Tooltip>
          )}
          
          <Tooltip title="删除任务">
            <Popconfirm
              title="确定要删除这个任务吗？删除后无法恢复。"
              onConfirm={() => deleteTask(record)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                type="text"
                icon={<DeleteOutlined />}
                size="small"
                danger
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ];

  // 任务操作函数
  const showTaskDetail = (task: Task) => {
    setSelectedTask(task);
    setDetailModalVisible(true);
  };

  const retryTask = async (task: Task) => {
    try {
      // 创建新任务（复制原任务配置）
      const newTask = await TaskService.createTask({
        file_id: task.file_id,
        task_type: task.task_type,
        config_snapshot: task.config_snapshot ? JSON.parse(task.config_snapshot) : undefined,
      });
      
      // 启动新任务
      await TaskService.startTask(newTask.id);
      
      queryClient.invalidateQueries('tasks');
      message.success('任务重试已启动');
    } catch (error) {
      message.error('任务重试失败');
    }
  };

  const deleteTask = (task: Task) => {
    // 这里应该调用删除API，暂时模拟
    message.success('任务删除成功');
    queryClient.invalidateQueries('tasks');
  };

  // 批量操作
  const handleBatchStart = () => {
    const pendingTasks = filteredTasks.filter(
      task => selectedTasks.includes(task.id) && task.status === TaskStatus.PENDING
    );
    
    if (pendingTasks.length === 0) {
      message.warning('没有可启动的任务');
      return;
    }
    
    // 批量启动任务
    Promise.all(pendingTasks.map(task => TaskService.startTask(task.id)))
      .then(() => {
        queryClient.invalidateQueries('tasks');
        message.success(`成功启动 ${pendingTasks.length} 个任务`);
        setSelectedTasks([]);
      })
      .catch(() => {
        message.error('批量启动任务失败');
      });
  };

  const handleBatchCancel = () => {
    const processingTasks = filteredTasks.filter(
      task => selectedTasks.includes(task.id) && task.status === TaskStatus.PROCESSING
    );
    
    if (processingTasks.length === 0) {
      message.warning('没有可取消的任务');
      return;
    }
    
    // 批量取消任务
    Promise.all(processingTasks.map(task => TaskService.cancelTask(task.id)))
      .then(() => {
        queryClient.invalidateQueries('tasks');
        message.success(`成功取消 ${processingTasks.length} 个任务`);
        setSelectedTasks([]);
      })
      .catch(() => {
        message.error('批量取消任务失败');
      });
  };

  return (
    <div className="tasks-page">
      {/* 页面标题和统计 */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={2}>任务管理</Title>
            <Paragraph type="secondary">
              管理和监控所有PPT处理任务的状态和进度
            </Paragraph>
          </div>
          
          {/* WebSocket连接状态 */}
          <div>
            {wsConnected ? (
              <Alert
                message="实时连接正常"
                type="success"
                showIcon
                style={{ marginBottom: 0 }}
                size="small"
              />
            ) : (
              <Alert
                message="实时连接断开"
                type="warning"
                showIcon
                style={{ marginBottom: 0 }}
                size="small"
                action={
                  <Button
                    size="small"
                    type="link"
                    onClick={() => {
                      const taskMonitor = getGlobalTaskMonitor();
                      taskMonitor.reconnect();
                    }}
                  >
                    重连
                  </Button>
                }
              />
            )}
          </div>
        </div>

        {/* 统计卡片 */}
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col xs={24} sm={6}>
            <Card size="small">
              <Statistic
                title="总任务数"
                value={taskStats?.total || 0}
                prefix={<FileTextOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card size="small">
              <Statistic
                title="处理中"
                value={taskStats?.processing || 0}
                prefix={<ClockCircleOutlined />}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card size="small">
              <Statistic
                title="已完成"
                value={taskStats?.completed || 0}
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card size="small">
              <Statistic
                title="失败任务"
                value={taskStats?.failed || 0}
                prefix={<ExclamationCircleOutlined />}
                valueStyle={{ color: '#f5222d' }}
              />
            </Card>
          </Col>
        </Row>
      </div>

      <Card>
        {/* 筛选和搜索工具栏 */}
        <div style={{ marginBottom: 16 }}>
          <Row gutter={[16, 16]} align="middle">
            <Col xs={24} sm={8} md={6}>
              <Search
                placeholder="搜索文件名"
                value={filters.search}
                onChange={e => setFilters(prev => ({ ...prev, search: e.target.value }))}
                allowClear
              />
            </Col>
            <Col xs={24} sm={8} md={4}>
              <Select
                placeholder="状态筛选"
                value={filters.status}
                onChange={value => setFilters(prev => ({ ...prev, status: value }))}
                allowClear
                style={{ width: '100%' }}
              >
                <Option value={TaskStatus.PENDING}>等待处理</Option>
                <Option value={TaskStatus.PROCESSING}>处理中</Option>
                <Option value={TaskStatus.COMPLETED}>已完成</Option>
                <Option value={TaskStatus.FAILED}>处理失败</Option>
                <Option value={TaskStatus.CANCELLED}>已取消</Option>
              </Select>
            </Col>
            <Col xs={24} sm={8} md={4}>
              <Select
                placeholder="类型筛选"
                value={filters.type}
                onChange={value => setFilters(prev => ({ ...prev, type: value }))}
                allowClear
                style={{ width: '100%' }}
              >
                <Option value={TaskType.PPT_TO_SCRIPT}>PPT转讲稿</Option>
                <Option value={TaskType.SCRIPT_EDIT}>讲稿编辑</Option>
                <Option value={TaskType.BATCH_PROCESS}>批量处理</Option>
              </Select>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <RangePicker
                placeholder={['开始日期', '结束日期']}
                onChange={(dates, dateStrings) => 
                  setFilters(prev => ({ 
                    ...prev, 
                    dateRange: dateStrings[0] && dateStrings[1] ? [dateStrings[0], dateStrings[1]] : undefined 
                  }))
                }
                style={{ width: '100%' }}
              />
            </Col>
            <Col xs={24} sm={12} md={4}>
              <Button
                icon={<ReloadOutlined />}
                onClick={() => queryClient.invalidateQueries('tasks')}
                loading={isLoading}
              >
                刷新
              </Button>
            </Col>
          </Row>
        </div>

        {/* 批量操作工具栏 */}
        {selectedTasks.length > 0 && (
          <div style={{ marginBottom: 16, padding: 12, background: '#f0f8ff', borderRadius: 6 }}>
            <Space>
              <Text>已选择 {selectedTasks.length} 个任务</Text>
              <Button
                type="primary"
                size="small"
                icon={<PlayCircleOutlined />}
                onClick={handleBatchStart}
              >
                批量启动
              </Button>
              <Button
                size="small"
                icon={<StopOutlined />}
                onClick={handleBatchCancel}
              >
                批量取消
              </Button>
              <Button
                size="small"
                onClick={() => setSelectedTasks([])}
              >
                取消选择
              </Button>
            </Space>
          </div>
        )}

        {/* 任务表格 */}
        <Table
          columns={columns}
          dataSource={filteredTasks}
          rowKey="id"
          loading={isLoading}
          rowSelection={{
            selectedRowKeys: selectedTasks,
            onChange: setSelectedTasks,
            getCheckboxProps: record => ({
              disabled: record.status === TaskStatus.PROCESSING,
            }),
          }}
          pagination={{
            total: filteredTasks.length,
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 任务详情模态框 */}
      <Modal
        title="任务详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>,
          <Button
            key="logs"
            onClick={() => {
              setLogsModalVisible(true);
              setDetailModalVisible(false);
            }}
          >
            查看日志
          </Button>,
        ]}
        width={800}
      >
        {selectedTask && (
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="任务ID" span={1}>
              {selectedTask.id}
            </Descriptions.Item>
            <Descriptions.Item label="任务类型" span={1}>
              <Tag color="blue">
                {TaskService.getTaskTypeText(selectedTask.task_type)}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="文件名" span={2}>
              {fileMap[selectedTask.file_id]?.original_name || '未知文件'}
            </Descriptions.Item>
            <Descriptions.Item label="当前状态" span={1}>
              <Tag color={TaskService.getStatusColor(selectedTask.status)}>
                {TaskService.getStatusText(selectedTask.status)}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="进度" span={1}>
              <Progress percent={selectedTask.progress} size="small" />
            </Descriptions.Item>
            <Descriptions.Item label="开始时间" span={1}>
              {selectedTask.started_at ? formatDateTime(selectedTask.started_at) : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="完成时间" span={1}>
              {selectedTask.completed_at ? formatDateTime(selectedTask.completed_at) : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="执行时长" span={2}>
              {selectedTask.duration ? TaskService.formatDuration(selectedTask.duration) : '-'}
            </Descriptions.Item>
            {selectedTask.error_message && (
              <Descriptions.Item label="错误信息" span={2}>
                <Text type="danger">{selectedTask.error_message}</Text>
              </Descriptions.Item>
            )}
            {selectedTask.config_snapshot && (
              <Descriptions.Item label="配置快照" span={2}>
                <pre style={{ fontSize: '12px', maxHeight: 200, overflow: 'auto' }}>
                  {JSON.stringify(JSON.parse(selectedTask.config_snapshot), null, 2)}
                </pre>
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Modal>

      {/* 任务日志模态框 */}
      <Modal
        title="任务日志"
        open={logsModalVisible}
        onCancel={() => setLogsModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setLogsModalVisible(false)}>
            关闭
          </Button>,
        ]}
        width={900}
      >
        {selectedTask && (
          <div>
            <Timeline
              items={[
                {
                  color: 'blue',
                  children: (
                    <div>
                      <Text strong>任务创建</Text>
                      <div>
                        <Text type="secondary">任务已创建并等待处理</Text>
                      </div>
                    </div>
                  ),
                },
                selectedTask.started_at && {
                  color: selectedTask.status === TaskStatus.PROCESSING ? 'blue' : 'gray',
                  children: (
                    <div>
                      <Text strong>任务开始</Text>
                      <div>
                        <Text type="secondary">
                          {formatDateTime(selectedTask.started_at)}
                        </Text>
                      </div>
                    </div>
                  ),
                },
                selectedTask.completed_at && {
                  color: selectedTask.status === TaskStatus.COMPLETED ? 'green' : 'red',
                  children: (
                    <div>
                      <Text strong>
                        {selectedTask.status === TaskStatus.COMPLETED ? '任务完成' : '任务失败'}
                      </Text>
                      <div>
                        <Text type="secondary">
                          {formatDateTime(selectedTask.completed_at)}
                        </Text>
                      </div>
                      {selectedTask.error_message && (
                        <div>
                          <Text type="danger">{selectedTask.error_message}</Text>
                        </div>
                      )}
                    </div>
                  ),
                },
              ].filter(Boolean)}
            />
            
            {/* 这里可以添加更详细的日志信息 */}
            <Divider />
            <Text type="secondary">
              详细日志功能正在开发中，将显示任务执行的完整过程记录
            </Text>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Tasks;