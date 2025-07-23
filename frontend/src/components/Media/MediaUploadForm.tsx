import React, { useEffect } from 'react';
import {
  Card,
  Upload,
  Button,
  Space,
  Typography,
  Progress,
} from 'antd';
import {
  UploadOutlined,
  SoundOutlined,
  CloseOutlined,
} from '@ant-design/icons';
import { useMediaUpload } from '@/hooks';

const { Text } = Typography;
const { Dragger } = Upload;

interface MediaUploadFormProps {
  supportedFormats?: { audio?: string[]; video?: string[]; };
  onUploadSuccess?: (fileId: number) => void;
}

const MediaUploadForm: React.FC<MediaUploadFormProps> = ({
  supportedFormats,
  onUploadSuccess,
}) => {
  const {
    isUploading,
    uploadProps,
    startUpload,
    cancelUpload,
    clearFileList,
    getSupportedExtensions,
    getUploadStatus,
  } = useMediaUpload(supportedFormats);

  const { hasFiles, canUpload, isDragging, progress } = getUploadStatus();

  // 处理上传成功回调
  const handleUpload = async () => {
    try {
      const result = await startUpload();
      if (onUploadSuccess && result?.file_id) {
        onUploadSuccess(result.file_id);
      }
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  // 添加拖拽状态效果
  useEffect(() => {
    const handleDragOver = (e: DragEvent) => {
      e.preventDefault();
    };
    
    document.addEventListener('dragover', handleDragOver);
    return () => document.removeEventListener('dragover', handleDragOver);
  }, []);

  return (
    <Card 
      title="上传音视频文件" 
      className="upload-card"
      style={{
        transition: 'all 0.3s ease',
        transform: 'none',
        boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px 0 rgba(0, 0, 0, 0.02)',
        background: '#ffffff',
        border: '1px solid #f0f0f0',
        borderRadius: '8px'
      }}
    >
      <Dragger 
        {...uploadProps} 
        style={{ 
          marginBottom: 16,
          borderColor: isDragging ? '#52c41a' : undefined,
          backgroundColor: isDragging 
            ? 'rgba(82, 196, 26, 0.1)' 
            : undefined
        }}
      >
        <p className="ant-upload-drag-icon">
          <SoundOutlined />
        </p>
        <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
        <p className="ant-upload-hint">
          支持单个文件上传，支持常见音视频格式，文件大小不超过 500MB
        </p>
        {supportedFormats && (
          <div style={{ marginTop: 8 }}>
            <Text type="secondary">
              支持格式: {getSupportedExtensions().join(', ')}
            </Text>
          </div>
        )}
      </Dragger>
      
      {/* 上传进度条 */}
      {progress.status === 'uploading' && (
        <div style={{ marginBottom: 16 }}>
          <Progress
            percent={progress.percent}
            status="active"
            strokeColor="#1890ff"
            format={(percent) => `${percent}%`}
          />
          <Text type="secondary" style={{ fontSize: 12, marginTop: 4, display: 'block' }}>
            {progress.message}
          </Text>
        </div>
      )}
      
      <Space>
        <Button
          type="primary"
          icon={isUploading ? <CloseOutlined /> : <UploadOutlined />}
          onClick={isUploading ? cancelUpload : handleUpload}
          disabled={!canUpload && !isUploading}
          loading={progress.status === 'uploading'}
          danger={isUploading}
        >
          {isUploading ? '取消上传' : '开始上传'}
        </Button>
        <Button onClick={clearFileList} disabled={isUploading}>
          清空列表
        </Button>
      </Space>
    </Card>
  );
};

export default MediaUploadForm;