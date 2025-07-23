import React from 'react';
import {
  Table,
  Space,
  Button,
  Tag,
  Progress,
  Tooltip,
  Typography,
  Empty,
} from 'antd';
import {
  SoundOutlined,
  VideoCameraOutlined,
  EyeOutlined,
  FileTextOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useTranscription } from '@/hooks';
import { useMediaFiles } from '@/hooks';
import type { Task, TaskStatus, FileType } from '@/types';
import type { ColumnsType } from 'antd/es/table';

const { Text } = Typography;

interface TranscriptionTaskTableProps {}

const TranscriptionTaskTable: React.FC<TranscriptionTaskTableProps> = () => {
  const {
    transcriptionTasks,
    tasksLoading,
    refreshTasks,
  } = useTranscription();

  const { files } = useMediaFiles();

  const getFileTypeIcon = (fileType: FileType) => {
    switch (fileType) {
      case 'audio':
        return <SoundOutlined style={{ color: '#52c41a' }} />;
      case 'video':
        return <VideoCameraOutlined style={{ color: '#1890ff' }} />;
      default:
        return <FileTextOutlined />;
    }
  };

  const getTaskStatusColor = (status: TaskStatus) => {
    const colors = {
      'pending': 'default',
      'processing': 'blue',
      'completed': 'success',
      'failed': 'error',
      'cancelled': 'warning',
    };
    return colors[status] || 'default';
  };

  const getTaskStatusText = (status: TaskStatus) => {
    const texts = {
      'pending': '等待中',
      'processing': '转录中',
      'completed': '已完成',
      'failed': '失败',
      'cancelled': '已取消',
    };
    return texts[status] || status;
  };

  const columns: ColumnsType<Task> = [
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
        return file ? (
          <Space>
            {getFileTypeIcon(file.file_type)}
            {file.original_name}
          </Space>
        ) : '未知文件';
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
          status={record.status === 'failed' ? 'exception' : 'active'}
          strokeColor={record.status === 'processing' ? '#1890ff' : undefined}
        />
      ),
    },
    {
      title: '配置',
      key: 'config',
      width: 120,
      render: (_, record) => {
        let config: any = {};
        try {
          config = record.config_snapshot ? JSON.parse(JSON.stringify(record.config_snapshot)) : {};
        } catch (e) {
          config = {};
        }
        return (
          <div>
            <div><Text type="secondary">语言: {config.language || 'auto'}</Text></div>
            <div><Text type="secondary">模型: {config.model_size || 'base'}</Text></div>
          </div>
        );
      },
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
          {record.status === 'completed' && (
            <Tooltip title="查看转录结果">
              <Button
                size="small"
                icon={<EyeOutlined />}
                onClick={() => {
                  window.open(`/scripts?task_id=${record.id}`, '_blank');
                }}
              />
            </Tooltip>
          )}
        </Space>
      ),
    },
  ];


  if (!transcriptionTasks.length) {
    return (
      <div style={{ textAlign: 'center', padding: '40px 0' }}>
        <Empty
          description="暂无转录任务"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
        <Button 
          icon={<ReloadOutlined />} 
          onClick={refreshTasks}
          style={{ marginTop: 16 }}
        >
          刷新
        </Button>
      </div>
    );
  }

  return (
    <div>
      <div style={{ 
        marginBottom: 16, 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center' 
      }}>
        <div>
          <Typography.Title level={4} style={{ margin: 0 }}>
            音视频转录任务
          </Typography.Title>
          <Typography.Text type="secondary">
            查看音视频转录任务的执行状态和进度
          </Typography.Text>
        </div>
        <Button icon={<ReloadOutlined />} onClick={refreshTasks}>
          刷新
        </Button>
      </div>
      
      <Table
        columns={columns}
        dataSource={transcriptionTasks}
        rowKey="id"
        loading={tasksLoading}
        pagination={{
          pageSize: 10,
          showSizeChanger: false,
          showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
        }}
      />
    </div>
  );
};

export default TranscriptionTaskTable;