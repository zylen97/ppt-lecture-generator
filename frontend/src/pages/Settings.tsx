import React, { useState, useMemo } from 'react';
import {
  Typography,
  Card,
  Tabs,
  Table,
  Space,
  Button,
  Tag,
  Select,
  Input,
  Modal,
  Form,
  Switch,
  Popconfirm,
  message,
  Row,
  Col,
  Divider,
  Tooltip,
  Alert,
  Badge,
  List,
  Progress,
  InputNumber,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ExperimentOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  SettingOutlined,
  ApiOutlined,
  FileTextOutlined,
  ReloadOutlined,
  EyeInvisibleOutlined,
  EyeOutlined,
  CopyOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { ConfigService } from '@/services';
import { APIConfig, APIConfigCreate, APITestRequest } from '@/types';
import type { ColumnsType } from 'antd/es/table';
import type { TabsProps } from 'antd';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TextArea } = Input;

interface APIConfigModalProps {
  config?: APIConfig;
  visible: boolean;
  onCancel: () => void;
  onSuccess: () => void;
}

const APIConfigModal: React.FC<APIConfigModalProps> = ({
  config,
  visible,
  onCancel,
  onSuccess,
}) => {
  const [form] = Form.useForm();
  const [testLoading, setTestLoading] = useState(false);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
    latency?: number;
  } | null>(null);
  const queryClient = useQueryClient();

  const createMutation = useMutation(ConfigService.createAPIConfig, {
    onSuccess: () => {
      queryClient.invalidateQueries('apiConfigs');
      message.success('API配置创建成功');
      onSuccess();
    },
    onError: () => {
      message.error('API配置创建失败');
    },
  });

  const updateMutation = useMutation(
    (data: APIConfigCreate) => ConfigService.updateAPIConfig(config!.id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('apiConfigs');
        message.success('API配置更新成功');
        onSuccess();
      },
      onError: () => {
        message.error('API配置更新失败');
      },
    }
  );

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const mutation = config ? updateMutation : createMutation;
      mutation.mutate(values);
    } catch (error) {
      // 表单验证失败
    }
  };

  const handleTest = async () => {
    try {
      const values = await form.validateFields(['endpoint', 'api_key', 'model']);
      setTestLoading(true);
      
      const testData: APITestRequest = {
        endpoint: values.endpoint,
        api_key: values.api_key,
        model: values.model,
      };
      
      const result = await ConfigService.testAPIConnection(testData);
      setTestResult(result);
      
      if (result.success) {
        message.success('API连接测试成功');
      } else {
        message.error(`API连接测试失败: ${result.message}`);
      }
    } catch (error) {
      setTestResult({
        success: false,
        message: '请先填写必填字段',
      });
    } finally {
      setTestLoading(false);
    }
  };

  const presetEndpoints = ConfigService.getPresetEndpoints();
  const commonModels = ConfigService.getCommonModels();

  return (
    <Modal
      title={config ? '编辑API配置' : '添加API配置'}
      open={visible}
      onCancel={onCancel}
      onOk={handleSubmit}
      confirmLoading={createMutation.isLoading || updateMutation.isLoading}
      width={700}
      destroyOnHidden
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={
          config
            ? {
                name: config.name,
                endpoint: config.endpoint,
                model: config.model,
                is_default: config.is_default,
              }
            : {
                is_default: false,
              }
        }
      >
        <Form.Item
          label="配置名称"
          name="name"
          rules={[
            { required: true, message: '请输入配置名称' },
            { max: 100, message: '名称不能超过100个字符' },
          ]}
        >
          <Input placeholder="给这个配置起个名字" />
        </Form.Item>

        <Form.Item
          label="API端点"
          name="endpoint"
          rules={[
            { required: true, message: '请输入API端点' },
            { type: 'url', message: '请输入有效的URL地址' },
          ]}
        >
          <Select
            showSearch
            placeholder="选择预设端点或输入自定义地址"
            allowClear
          >
            {presetEndpoints.map((preset) => (
              <Option key={preset.url} value={preset.url}>
                <div>
                  <div>{preset.name}</div>
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    {preset.description}
                  </Text>
                </div>
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          label="API密钥"
          name="api_key"
          rules={[
            { required: true, message: '请输入API密钥' },
            { min: 20, message: 'API密钥长度不足' },
          ]}
        >
          <Input.Password
            placeholder="请输入您的API密钥"
            visibilityToggle={{
              visible: false,
              onVisibleChange: () => {},
            }}
          />
        </Form.Item>

        <Form.Item
          label="模型"
          name="model"
          rules={[{ required: true, message: '请选择模型' }]}
        >
          <Select
            showSearch
            placeholder="选择AI模型"
            optionFilterProp="children"
          >
            {commonModels.map((model) => (
              <Option key={model.id} value={model.id}>
                <div>
                  <Space>
                    {model.name}
                    {model.vision && <Badge status="success" text="支持图像" />}
                  </Space>
                  <div>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      {model.description}
                    </Text>
                  </div>
                </div>
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item name="is_default" valuePropName="checked">
          <Switch checkedChildren="默认配置" unCheckedChildren="普通配置" />
          <Text type="secondary" style={{ marginLeft: 8 }}>
            设为默认配置
          </Text>
        </Form.Item>

        <Divider />

        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <Button
            icon={<ExperimentOutlined />}
            onClick={handleTest}
            loading={testLoading}
          >
            测试连接
          </Button>
          
          {testResult && (
            <Alert
              message={testResult.success ? '连接成功' : '连接失败'}
              description={
                <div>
                  <div>{testResult.message}</div>
                  {testResult.latency && (
                    <div>延迟: {ConfigService.formatLatency(testResult.latency)}</div>
                  )}
                </div>
              }
              type={testResult.success ? 'success' : 'error'}
              showIcon
              style={{ flex: 1, marginLeft: 16 }}
            />
          )}
        </Space>
      </Form>
    </Modal>
  );
};

const Settings: React.FC = () => {
  const queryClient = useQueryClient();
  
  // 状态管理
  const [selectedConfigs, setSelectedConfigs] = useState<number[]>([]);
  const [configModalVisible, setConfigModalVisible] = useState(false);
  const [selectedConfig, setSelectedConfig] = useState<APIConfig | null>(null);
  
  // 系统设置状态
  const [systemSettings, setSystemSettings] = useState({
    maxFileSize: 100, // MB
    maxConcurrentTasks: 3,
    defaultLanguage: 'zh-CN',
    autoCleanupDays: 30,
    enableNotifications: true,
    enableAutoSave: true,
  });

  // 数据查询
  const { data: apiConfigs = [], isLoading, error } = useQuery(
    'apiConfigs',
    () => ConfigService.getAPIConfigs({ limit: 100 })
  );

  // Mutations
  const deleteConfigMutation = useMutation(ConfigService.deleteAPIConfig, {
    onSuccess: () => {
      queryClient.invalidateQueries('apiConfigs');
      message.success('API配置删除成功');
    },
    onError: () => {
      message.error('API配置删除失败');
    },
  });

  // 操作函数
  const showConfigModal = (config?: APIConfig) => {
    setSelectedConfig(config || null);
    setConfigModalVisible(true);
  };

  const handleTestConfig = async (config: APIConfig) => {
    try {
      // 这里需要获取完整的API密钥来测试
      message.info('测试功能需要重新输入API密钥进行验证');
      showConfigModal(config);
    } catch (error) {
      message.error('测试连接失败');
    }
  };

  const handleCopyConfig = async (config: APIConfig) => {
    try {
      const configText = `配置名称: ${config.name}
API端点: ${config.endpoint}
模型: ${config.model}
创建时间: ${config.created_at}`;
      
      await navigator.clipboard.writeText(configText);
      message.success('配置信息已复制到剪贴板');
    } catch (error) {
      message.error('复制失败');
    }
  };

  // API配置表格列定义
  const apiConfigColumns: ColumnsType<APIConfig> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
      sorter: (a, b) => a.id - b.id,
    },
    {
      title: '配置名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record) => (
        <Space>
          <ApiOutlined />
          <Text strong={record.is_default}>{name}</Text>
          {record.is_default && <Tag color="gold">默认</Tag>}
        </Space>
      ),
      sorter: (a, b) => a.name.localeCompare(b.name),
    },
    {
      title: 'API端点',
      dataIndex: 'endpoint',
      key: 'endpoint',
      render: (endpoint: string) => (
        <Text ellipsis style={{ maxWidth: 200 }} title={endpoint}>
          {endpoint}
        </Text>
      ),
    },
    {
      title: '模型',
      dataIndex: 'model',
      key: 'model',
      render: (model: string) => {
        const modelInfo = ConfigService.getCommonModels().find(m => m.id === model);
        return (
          <Space>
            <Tag color="blue">{model}</Tag>
            {modelInfo?.vision && <Badge status="success" text="Vision" />}
          </Space>
        );
      },
    },
    {
      title: 'API密钥',
      dataIndex: 'api_key_masked',
      key: 'api_key_masked',
      render: (masked: string) => (
        <Text code style={{ fontSize: '12px' }}>
          {masked}
        </Text>
      ),
    },
    {
      title: '状态',
      key: 'status',
      width: 100,
      render: (_, record) => (
        <Tag color={record.is_active ? 'success' : 'default'}>
          {record.is_active ? '启用' : '禁用'}
        </Tag>
      ),
      filters: [
        { text: '启用', value: true },
        { text: '禁用', value: false },
      ],
      onFilter: (value, record) => record.is_active === value,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (date: string) => new Date(date).toLocaleDateString(),
      sorter: (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="测试连接">
            <Button
              type="text"
              icon={<ExperimentOutlined />}
              size="small"
              onClick={() => handleTestConfig(record)}
            />
          </Tooltip>
          
          <Tooltip title="编辑配置">
            <Button
              type="text"
              icon={<EditOutlined />}
              size="small"
              onClick={() => showConfigModal(record)}
            />
          </Tooltip>
          
          <Tooltip title="复制信息">
            <Button
              type="text"
              icon={<CopyOutlined />}
              size="small"
              onClick={() => handleCopyConfig(record)}
            />
          </Tooltip>
          
          <Tooltip title="删除配置">
            <Popconfirm
              title="确定要删除这个API配置吗？"
              onConfirm={() => deleteConfigMutation.mutate(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                type="text"
                icon={<DeleteOutlined />}
                size="small"
                danger
                disabled={record.is_default}
                loading={deleteConfigMutation.isLoading}
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ];

  const tabItems: TabsProps['items'] = [
    {
      key: 'api',
      label: (
        <Space>
          <ApiOutlined />
          API配置
        </Space>
      ),
      children: (
        <div>
          <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
            <div>
              <Title level={4}>API配置管理</Title>
              <Paragraph type="secondary">
                管理OpenAI API配置，支持多个配置切换使用
              </Paragraph>
            </div>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => showConfigModal()}
            >
              添加配置
            </Button>
          </div>

          <Card>
            {/* 批量操作工具栏 */}
            {selectedConfigs.length > 0 && (
              <div style={{ marginBottom: 16, padding: 12, background: '#f0f8ff', borderRadius: 6 }}>
                <Space>
                  <Text>已选择 {selectedConfigs.length} 个配置</Text>
                  <Button
                    size="small"
                    onClick={() => setSelectedConfigs([])}
                  >
                    取消选择
                  </Button>
                </Space>
              </div>
            )}

            <Table
              columns={apiConfigColumns}
              dataSource={apiConfigs}
              rowKey="id"
              loading={isLoading}
              rowSelection={{
                selectedRowKeys: selectedConfigs,
                onChange: setSelectedConfigs,
                getCheckboxProps: record => ({
                  disabled: record.is_default, // 默认配置不能被选择删除
                }),
              }}
              pagination={{
                pageSize: 10,
                showSizeChanger: false,
                showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
              }}
            />
          </Card>
        </div>
      ),
    },
    {
      key: 'system',
      label: (
        <Space>
          <SettingOutlined />
          系统参数
        </Space>
      ),
      children: (
        <div>
          <Title level={4}>系统参数设置</Title>
          <Paragraph type="secondary">
            配置系统运行参数和行为设置
          </Paragraph>

          <Row gutter={[24, 24]}>
            <Col xs={24} lg={12}>
              <Card title="文件处理设置" size="small">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text>最大文件大小</Text>
                    <Space>
                      <InputNumber
                        value={systemSettings.maxFileSize}
                        onChange={(value) => setSystemSettings(prev => ({ ...prev, maxFileSize: value || 100 }))}
                        min={1}
                        max={500}
                        addonAfter="MB"
                        style={{ width: 100 }}
                      />
                    </Space>
                  </div>
                  
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text>最大并发任务数</Text>
                    <InputNumber
                      value={systemSettings.maxConcurrentTasks}
                      onChange={(value) => setSystemSettings(prev => ({ ...prev, maxConcurrentTasks: value || 3 }))}
                      min={1}
                      max={10}
                      style={{ width: 80 }}
                    />
                  </div>
                  
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text>自动清理天数</Text>
                    <Space>
                      <InputNumber
                        value={systemSettings.autoCleanupDays}
                        onChange={(value) => setSystemSettings(prev => ({ ...prev, autoCleanupDays: value || 30 }))}
                        min={1}
                        max={365}
                        style={{ width: 80 }}
                      />
                      <Text type="secondary">天</Text>
                    </Space>
                  </div>
                </Space>
              </Card>
            </Col>
            
            <Col xs={24} lg={12}>
              <Card title="界面设置" size="small">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text>默认语言</Text>
                    <Select
                      value={systemSettings.defaultLanguage}
                      onChange={(value) => setSystemSettings(prev => ({ ...prev, defaultLanguage: value }))}
                      style={{ width: 120 }}
                    >
                      <Option value="zh-CN">简体中文</Option>
                      <Option value="en-US">English</Option>
                    </Select>
                  </div>
                  
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text>启用通知</Text>
                    <Switch
                      checked={systemSettings.enableNotifications}
                      onChange={(checked) => setSystemSettings(prev => ({ ...prev, enableNotifications: checked }))}
                    />
                  </div>
                  
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text>自动保存</Text>
                    <Switch
                      checked={systemSettings.enableAutoSave}
                      onChange={(checked) => setSystemSettings(prev => ({ ...prev, enableAutoSave: checked }))}
                    />
                  </div>
                </Space>
              </Card>
            </Col>
          </Row>
          
          <div style={{ marginTop: 24, textAlign: 'right' }}>
            <Button
              type="primary"
              onClick={() => {
                // 保存系统设置
                ConfigService.saveToLocalStorage('systemSettings', systemSettings);
                message.success('系统设置已保存');
              }}
            >
              保存设置
            </Button>
          </div>
        </div>
      ),
    },
    {
      key: 'templates',
      label: (
        <Space>
          <FileTextOutlined />
          讲稿模板
        </Space>
      ),
      children: (
        <div>
          <Title level={4}>讲稿模板管理</Title>
          <Paragraph type="secondary">
            管理讲稿生成模板，自定义生成格式和风格
          </Paragraph>

          <Alert
            message="模板功能开发中"
            description="讲稿模板管理功能正在开发中，将支持自定义生成格式、教学风格等高级功能。"
            type="info"
            showIcon
            style={{ marginBottom: 24 }}
          />

          <List
            size="large"
            header={<div>预设模板</div>}
            bordered
            dataSource={[
              {
                title: '标准教学模板',
                description: '适合大学课程的标准讲稿格式，包含目标、重点、案例等',
                status: '可用',
              },
              {
                title: '互动式模板',
                description: '强调师生互动的讲稿格式，包含提问、讨论环节',
                status: '开发中',
              },
              {
                title: '实践导向模板',
                description: '注重实践操作的讲稿格式，适合技能型课程',
                status: '计划中',
              },
            ]}
            renderItem={item => (
              <List.Item
                actions={[
                  <Tag color={item.status === '可用' ? 'success' : 'default'}>
                    {item.status}
                  </Tag>,
                ]}
              >
                <List.Item.Meta
                  avatar={<FileTextOutlined style={{ fontSize: 20 }} />}
                  title={item.title}
                  description={item.description}
                />
              </List.Item>
            )}
          />
        </div>
      ),
    },
  ];

  return (
    <div className="settings-page">
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>系统设置</Title>
        <Paragraph type="secondary">
          配置系统参数、API接口、讲稿模板等设置
        </Paragraph>
      </div>

      <Tabs items={tabItems} />

      {/* API配置模态框 */}
      <APIConfigModal
        config={selectedConfig || undefined}
        visible={configModalVisible}
        onCancel={() => setConfigModalVisible(false)}
        onSuccess={() => setConfigModalVisible(false)}
      />
    </div>
  );
};

export default Settings;