import React from 'react';
import {
  Typography,
  Tabs,
  Card,
  Row,
  Col,
  Space,
  Empty,
  Button,
} from 'antd';
import '@/styles/media-processor.css';
import {
  UploadOutlined,
  SoundOutlined,
  ClockCircleOutlined,
  PlusOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { useMediaFiles, useTranscription } from '@/hooks';
import { useCurrentProject } from '@/contexts';
import type { TabsProps } from 'antd';
import {
  MediaUploadForm,
  TranscriptionConfig,
  MediaFileTable,
  TranscriptionTaskTable,
  MediaStatistics,
} from '@/components/Media';

const { Title, Paragraph, Text } = Typography;

const AudioVideoProcessor: React.FC = () => {
  const { currentProject } = useCurrentProject();
  const { files, supportedFormats } = useMediaFiles();
  const { 
    transcriptionTasks, 
    startTranscription,
    config,
    updateConfig,
    modelInfo 
  } = useTranscription();

  // 事件处理函数
  const handleUploadSuccess = (fileId: number) => {
    console.log('File uploaded successfully:', fileId);
  };

  // 开始转录
  const handleStartTranscription = async (fileId: number) => {
    await startTranscription(fileId);
  };

  // 处理配置变更
  const handleConfigChange = (newConfig: any) => {
    updateConfig(newConfig);
  };

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
              <MediaUploadForm 
                supportedFormats={supportedFormats}
                onUploadSuccess={handleUploadSuccess}
              />
            </Col>
            
            <Col xs={24} lg={8}>
              <TranscriptionConfig
                config={config}
                onChange={handleConfigChange}
                modelInfo={modelInfo}
              />
            </Col>
          </Row>
        </div>
      ),
    },
    {
      key: 'files',
      label: (
        <Space>
          <SoundOutlined />
          文件管理
        </Space>
      ),
      children: (
        <MediaFileTable
          onTranscriptionStart={handleStartTranscription}
        />
      ),
    },
    {
      key: 'tasks',
      label: (
        <Space>
          <ClockCircleOutlined />
          转录任务
        </Space>
      ),
      children: (
        <TranscriptionTaskTable />
      ),
    },
  ];

  return (
    <div className="media-processor-page">
      {/* 页面标题 */}
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>音视频转讲稿</Title>
        <Paragraph type="secondary">
          {currentProject ? 
            `项目：${currentProject.name} - 上传音视频文件并转录为讲稿` : 
            '请在顶部选择一个项目以开始音视频处理流程'
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
                请选择一个项目以开始音视频文件处理和转录流程
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
      <MediaStatistics files={files} tasks={transcriptionTasks} />
      
      {/* 主要内容区域 */}
      <Card>
        <Tabs items={tabItems} />
      </Card>
        </div>
      )}
    </div>
  );
};

export default AudioVideoProcessor;