import React from 'react';
import {
  Table,
  Space,
  Button,
  Tag,
  Tooltip,
  Popconfirm,
  Typography,
  Empty,
} from 'antd';
import {
  SoundOutlined,
  VideoCameraOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  FileTextOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useMediaFiles } from '@/hooks';
import type { FileInfo, FileType } from '@/types';
import type { ColumnsType } from 'antd/es/table';

const { Text } = Typography;

interface MediaFileTableProps {
  onTranscriptionStart?: (fileId: number) => void;
}

const MediaFileTable: React.FC<MediaFileTableProps> = ({
  onTranscriptionStart,
}) => {
  const {
    files,
    selectedFiles,
    filesLoading,
    isDeleting,
    handleFileSelection,
    deleteFile,
    deleteBatchSelected,
    refreshFiles,
  } = useMediaFiles();

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

  const formatDuration = (seconds: number) => {
    if (!seconds) return '-';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const columns: ColumnsType<FileInfo> = [
    {
      title: '文件名',
      dataIndex: 'original_name',
      key: 'original_name',
      ellipsis: true,
      render: (name: string, record) => (
        <Space>
          {getFileTypeIcon(record.file_type)}
          <Text strong>{name}</Text>
          <Tag color={record.file_type === 'audio' ? 'green' : 'blue'}>
            {record.file_type === 'audio' ? '音频' : '视频'}
          </Tag>
        </Space>
      ),
    },
    {
      title: '时长',
      dataIndex: 'duration',
      key: 'duration',
      width: 100,
      render: (duration: number) => formatDuration(duration),
    },
    {
      title: '文件大小',
      dataIndex: 'file_size_mb',
      key: 'file_size_mb',
      width: 100,
      render: (size: number) => `${size} MB`,
    },
    {
      title: '格式信息',
      key: 'format_info',
      width: 150,
      render: (_, record) => (
        <div>
          {record.codec && (
            <div><Text type="secondary">编码: {record.codec}</Text></div>
          )}
          {record.sample_rate && (
            <div><Text type="secondary">采样率: {record.sample_rate}Hz</Text></div>
          )}
          {record.resolution && (
            <div><Text type="secondary">分辨率: {record.resolution}</Text></div>
          )}
        </div>
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
      width: 200,
      render: (_, record) => (
        <Space>
          <Tooltip title="开始转录">
            <Button
              type="primary"
              size="small"
              icon={<PlayCircleOutlined />}
              onClick={() => onTranscriptionStart?.(record.id)}
            >
              转录
            </Button>
          </Tooltip>
          
          <Tooltip title="删除文件">
            <Popconfirm
              title="确定要删除这个文件吗？"
              onConfirm={() => deleteFile(record.id)}
            >
              <Button
                size="small"
                danger
                icon={<DeleteOutlined />}
                loading={isDeleting}
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ];


  if (!files.length) {
    return (
      <div style={{ textAlign: 'center', padding: '40px 0' }}>
        <Empty
          description="暂无音视频文件"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
        <Button 
          icon={<ReloadOutlined />} 
          onClick={refreshFiles}
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
            已上传的音视频文件
          </Typography.Title>
          <Typography.Text type="secondary">
            管理已上传的音视频文件，可以启动转录任务
          </Typography.Text>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={refreshFiles}>
            刷新
          </Button>
          {selectedFiles.length > 0 && (
            <Popconfirm
              title={`确定要删除选中的${selectedFiles.length}个文件吗？`}
              onConfirm={deleteBatchSelected}
            >
              <Button danger loading={isDeleting}>
                批量删除({selectedFiles.length})
              </Button>
            </Popconfirm>
          )}
        </Space>
      </div>
      
      <Table
        columns={columns}
        dataSource={files}
        rowKey="id"
        loading={filesLoading}
        rowSelection={{
          selectedRowKeys: selectedFiles,
          onChange: (selectedRowKeys) => handleFileSelection(selectedRowKeys as number[]),
        }}
        pagination={{
          pageSize: 10,
          showSizeChanger: false,
          showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
        }}
      />
    </div>
  );
};

export default MediaFileTable;