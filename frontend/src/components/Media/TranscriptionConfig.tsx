import React from 'react';
import {
  Card,
  Form,
  Select,
  Alert,
  Divider,
  Typography,
} from 'antd';
import {
  SettingOutlined,
} from '@ant-design/icons';

const { Title } = Typography;
const { Option } = Select;

interface TranscriptionConfigData {
  language: string;
  model_size: string;
}

interface TranscriptionConfigProps {
  config: TranscriptionConfigData;
  onChange: (config: TranscriptionConfigData) => void;
  modelInfo?: {
    whisper_available: boolean;
    available_models?: string[];
    supported_languages?: Record<string, string>;
  };
}

const TranscriptionConfig: React.FC<TranscriptionConfigProps> = ({
  config,
  onChange,
  modelInfo,
}) => {
  const handleConfigChange = (field: keyof TranscriptionConfigData, value: string) => {
    onChange({
      ...config,
      [field]: value,
    });
  };

  const languageOptions = [
    { value: 'auto', label: '自动检测' },
    { value: 'zh', label: '中文' },
    { value: 'en', label: '英语' },
    { value: 'ja', label: '日语' },
    { value: 'ko', label: '韩语' },
    { value: 'es', label: '西班牙语' },
    { value: 'fr', label: '法语' },
    { value: 'de', label: '德语' },
    { value: 'ru', label: '俄语' },
  ];

  const modelOptions = [
    { value: 'tiny', label: 'Tiny (最快，准确度较低)', description: '~37 MB' },
    { value: 'base', label: 'Base (平衡)', description: '~142 MB' },
    { value: 'small', label: 'Small (较高准确度)', description: '~466 MB' },
    { value: 'medium', label: 'Medium (高准确度)', description: '~1.5 GB' },
    { value: 'large-v2', label: 'Large-v2 (最高准确度)', description: '~3.1 GB' },
    { value: 'large-v3', label: 'Large-v3 (最新版本)', description: '~3.1 GB' },
  ];

  return (
    <Card 
      title={
        <span>
          <SettingOutlined style={{ marginRight: 8 }} />
          转录配置
        </span>
      } 
      style={{
        background: '#ffffff',
        boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px 0 rgba(0, 0, 0, 0.02)',
        borderRadius: '8px',
        border: '1px solid #f0f0f0'
      }}
    >
      <Form layout="vertical">
        <Form.Item label="识别语言">
          <Select 
            value={config.language}
            onChange={(value) => handleConfigChange('language', value)}
          >
            {languageOptions.map(option => (
              <Option key={option.value} value={option.value}>
                {option.label}
              </Option>
            ))}
          </Select>
        </Form.Item>
        
        <Form.Item label="模型大小">
          <Select 
            value={config.model_size}
            onChange={(value) => handleConfigChange('model_size', value)}
          >
            {modelOptions.map(option => (
              <Option key={option.value} value={option.value}>
                <div>
                  <div>{option.label}</div>
                  <small style={{ color: '#666' }}>{option.description}</small>
                </div>
              </Option>
            ))}
          </Select>
        </Form.Item>
      </Form>
      
      {modelInfo && !modelInfo.whisper_available && (
        <Alert
          message="Whisper不可用"
          description="语音识别服务当前不可用，请联系管理员"
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}
      
      <Divider />
      
      <div>
        <Title level={5}>转录说明</Title>
        <ul style={{ marginBottom: 0 }}>
          <li>支持多种音视频格式</li>
          <li>自动提取视频中的音频</li>
          <li>支持词级时间戳</li>
          <li>支持语音活动检测</li>
          <li>转录结果可编辑和导出</li>
        </ul>
      </div>
    </Card>
  );
};

export default TranscriptionConfig;