import React, { useState, useMemo } from 'react';
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
  Descriptions,
  Divider,
  Popconfirm,
  message,
  Row,
  Col,
  Statistic,
  DatePicker,
  Tooltip,
  Dropdown,
  Badge,
  Switch,
} from 'antd';
import {
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  DownloadOutlined,
  FileTextOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  SearchOutlined,
  PlusOutlined,
  CopyOutlined,
  ReloadOutlined,
  FilterOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { ScriptService, TaskService, FileService } from '@/services';
import { Script, ScriptSummary, Task, FileInfo } from '@/types';
import { useCurrentProject } from '@/contexts';
import { formatDateTime, formatRelativeTime } from '@/utils';
import type { ColumnsType } from 'antd/es/table';
import type { MenuProps } from 'antd';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { Search } = Input;
const { TextArea } = Input;
const { RangePicker } = DatePicker;

interface ScriptFilters {
  task_id?: number;
  dateRange?: [string, string];
  search?: string;
  showInactive?: boolean;
}

interface ScriptEditModalProps {
  script?: Script;
  visible: boolean;
  onCancel: () => void;
  onSuccess: () => void;
}

const ScriptEditModal: React.FC<ScriptEditModalProps> = ({
  script,
  visible,
  onCancel,
  onSuccess,
}) => {
  const [form] = useState({
    title: script?.title || '',
    content: script?.content || '',
    estimated_duration: script?.estimated_duration || 0,
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const queryClient = useQueryClient();

  const updateMutation = useMutation(
    (data: any) => ScriptService.updateScript(script!.id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('scripts');
        message.success('讲稿更新成功');
        onSuccess();
      },
      onError: () => {
        message.error('讲稿更新失败');
      },
    }
  );

  const handleSubmit = () => {
    // 验证表单
    const errors: Record<string, string> = {};
    
    if (!form.title.trim()) {
      errors.title = '标题不能为空';
    }
    
    const validation = ScriptService.validateScriptContent(form.content);
    if (!validation.valid) {
      errors.content = validation.issues.join(', ');
    }
    
    setFormErrors(errors);
    
    if (Object.keys(errors).length === 0) {
      updateMutation.mutate({
        title: form.title,
        content: form.content,
        estimated_duration: form.estimated_duration || undefined,
      });
    }
  };

  return (
    <Modal
      title="编辑讲稿"
      open={visible}
      onCancel={onCancel}
      onOk={handleSubmit}
      confirmLoading={updateMutation.isLoading}
      width={800}
      style={{ top: 20 }}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        <div>
          <Text strong>标题</Text>
          <Input
            value={form.title}
            onChange={(e) => (form.title = e.target.value)}
            placeholder="输入讲稿标题"
            status={formErrors.title ? 'error' : undefined}
          />
          {formErrors.title && <Text type="danger">{formErrors.title}</Text>}
        </div>
        
        <div>
          <Text strong>预估时长（分钟）</Text>
          <Input
            type="number"
            value={form.estimated_duration}
            onChange={(e) => (form.estimated_duration = parseInt(e.target.value) || 0)}
            placeholder="预估讲授时长"
            min={0}
            max={1440}
          />
        </div>
        
        <div>
          <Text strong>讲稿内容</Text>
          <TextArea
            value={form.content}
            onChange={(e) => (form.content = e.target.value)}
            placeholder="输入讲稿内容（支持Markdown格式）"
            rows={15}
            status={formErrors.content ? 'error' : undefined}
          />
          {formErrors.content && <Text type="danger">{formErrors.content}</Text>}
          <Text type="secondary" style={{ fontSize: '12px' }}>
            字数: {form.content.length} | 
            预计阅读时间: {ScriptService.calculateReadingTime(form.content.length)}分钟
          </Text>
        </div>
      </Space>
    </Modal>
  );
};

const Scripts: React.FC = () => {
  const queryClient = useQueryClient();
  const { currentProject } = useCurrentProject();
  
  // 状态管理
  const [selectedScripts, setSelectedScripts] = useState<number[]>([]);
  const [filters, setFilters] = useState<ScriptFilters>({});
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [previewModalVisible, setPreviewModalVisible] = useState(false);
  const [selectedScript, setSelectedScript] = useState<Script | null>(null);
  const [previewContent, setPreviewContent] = useState<string>('');

  // 数据查询 - 基于当前项目
  const { data: scripts = [], isLoading, error } = useQuery(
    ['scripts', currentProject?.id, filters],
    () => currentProject ? ScriptService.getScripts({
      project_id: currentProject.id,
      task_id: filters.task_id,
      limit: 1000,
    }) : Promise.resolve([]),
    {
      enabled: !!currentProject,
    }
  );

  const { data: tasks = [] } = useQuery(
    ['tasks', currentProject?.id],
    () => currentProject ? TaskService.getTasks({ 
      project_id: currentProject.id,
      limit: 1000 
    }) : Promise.resolve([]),
    {
      staleTime: 5 * 60 * 1000,
      enabled: !!currentProject,
    }
  );

  const { data: files = [] } = useQuery(
    ['files', currentProject?.id],
    () => currentProject ? FileService.getFiles({ 
      project_id: currentProject.id,
      limit: 1000 
    }) : Promise.resolve([]),
    {
      staleTime: 5 * 60 * 1000,
      enabled: !!currentProject,
    }
  );

  // 映射数据
  const taskMap = useMemo(() => {
    return tasks.reduce((map, task) => {
      map[task.id] = task;
      return map;
    }, {} as Record<number, Task>);
  }, [tasks]);

  const fileMap = useMemo(() => {
    return files.reduce((map, file) => {
      map[file.id] = file;
      return map;
    }, {} as Record<number, FileInfo>);
  }, [files]);

  // 过滤后的讲稿列表
  const filteredScripts = useMemo(() => {
    let result = [...scripts];

    // 搜索筛选
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      result = result.filter(script => 
        script.title.toLowerCase().includes(searchLower) ||
        ScriptService.extractSummary(script.content || '', 100).toLowerCase().includes(searchLower)
      );
    }

    // 是否显示非活跃讲稿
    if (!filters.showInactive) {
      result = result.filter(script => script.is_active);
    }

    // 日期范围筛选
    if (filters.dateRange) {
      const [startDate, endDate] = filters.dateRange;
      result = result.filter(script => {
        const scriptDate = new Date(script.created_at);
        return scriptDate >= new Date(startDate) && scriptDate <= new Date(endDate);
      });
    }

    return result;
  }, [scripts, filters]);

  // Mutations
  const deleteScriptMutation = useMutation(ScriptService.deleteScript, {
    onSuccess: () => {
      queryClient.invalidateQueries(['scripts', currentProject?.id]);
      message.success('讲稿删除成功');
    },
    onError: () => {
      message.error('讲稿删除失败');
    },
  });

  // 操作函数
  const showScriptDetail = async (script: ScriptSummary) => {
    try {
      const fullScript = await ScriptService.getScript(script.id);
      setSelectedScript(fullScript);
      setDetailModalVisible(true);
    } catch (error) {
      message.error('获取讲稿详情失败');
    }
  };

  const showScriptEdit = async (script: ScriptSummary) => {
    try {
      const fullScript = await ScriptService.getScript(script.id);
      setSelectedScript(fullScript);
      setEditModalVisible(true);
    } catch (error) {
      message.error('获取讲稿详情失败');
    }
  };

  const showScriptPreview = async (script: ScriptSummary) => {
    try {
      const content = await ScriptService.previewScript(script.id);
      setPreviewContent(content);
      setSelectedScript(script as Script);
      setPreviewModalVisible(true);
    } catch (error) {
      message.error('获取讲稿预览失败');
    }
  };

  const handleExport = (script: ScriptSummary, format: string) => {
    ScriptService.exportScript(script.id, format as any)
      .then(() => {
        message.success(`讲稿已导出为${format.toUpperCase()}格式`);
      })
      .catch(() => {
        message.error('讲稿导出失败');
      });
  };

  const handleCopyContent = async (script: ScriptSummary) => {
    try {
      const fullScript = await ScriptService.getScript(script.id);
      await navigator.clipboard.writeText(fullScript.content || '');
      message.success('讲稿内容已复制到剪贴板');
    } catch (error) {
      message.error('复制失败');
    }
  };

  // 导出菜单
  const getExportMenu = (script: ScriptSummary): MenuProps => ({
    items: ScriptService.getSupportedExportFormats().map(format => ({
      key: format.key,
      label: (
        <Space>
          <DownloadOutlined />
          {format.label}
        </Space>
      ),
      onClick: () => handleExport(script, format.key),
    })),
  });

  // 表格列定义
  const columns: ColumnsType<ScriptSummary> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
      sorter: (a, b) => a.id - b.id,
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      render: (title: string, record) => (
        <Space>
          <FileTextOutlined />
          <Text style={{ maxWidth: 200 }} ellipsis={{ tooltip: title }}>
            {title}
          </Text>
          {!record.is_active && <Badge status="default" text="非活跃" />}
        </Space>
      ),
      sorter: (a, b) => a.title.localeCompare(b.title),
    },
    {
      title: '关联任务',
      key: 'task_info',
      render: (_, record) => {
        const task = taskMap[record.task_id];
        const file = task ? fileMap[task.file_id] : null;
        return (
          <Space direction="vertical" size={0}>
            <Text ellipsis style={{ maxWidth: 150 }}>
              {file?.original_name || '未知文件'}
            </Text>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              任务ID: {record.task_id}
            </Text>
          </Space>
        );
      },
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      width: 80,
      render: (version: number) => (
        <Tag color="blue">v{version}</Tag>
      ),
      sorter: (a, b) => a.version - b.version,
    },
    {
      title: '字数',
      dataIndex: 'word_count',
      key: 'word_count',
      width: 100,
      render: (count?: number) => ScriptService.formatWordCount(count),
      sorter: (a, b) => (a.word_count || 0) - (b.word_count || 0),
    },
    {
      title: '预估时长',
      dataIndex: 'estimated_duration',
      key: 'estimated_duration',
      width: 100,
      render: (duration?: number) => ScriptService.formatEstimatedDuration(duration),
      sorter: (a, b) => (a.estimated_duration || 0) - (b.estimated_duration || 0),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (date: string) => formatDateTime(date, 'MM-DD HH:mm'),
      sorter: (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    },
    {
      title: '状态',
      key: 'status',
      width: 80,
      render: (_, record) => (
        <Tag color={record.is_active ? 'green' : 'default'}>
          {record.is_active ? '活跃' : '归档'}
        </Tag>
      ),
      filters: [
        { text: '活跃', value: true },
        { text: '归档', value: false },
      ],
      onFilter: (value, record) => record.is_active === value,
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
              onClick={() => showScriptDetail(record)}
            />
          </Tooltip>
          
          <Tooltip title="编辑讲稿">
            <Button
              type="text"
              icon={<EditOutlined />}
              size="small"
              onClick={() => showScriptEdit(record)}
            />
          </Tooltip>
          
          <Tooltip title="预览">
            <Button
              type="text"
              icon={<SearchOutlined />}
              size="small"
              onClick={() => showScriptPreview(record)}
            />
          </Tooltip>
          
          <Tooltip title="复制内容">
            <Button
              type="text"
              icon={<CopyOutlined />}
              size="small"
              onClick={() => handleCopyContent(record)}
            />
          </Tooltip>
          
          <Dropdown menu={getExportMenu(record)} placement="bottomRight">
            <Button
              type="text"
              icon={<DownloadOutlined />}
              size="small"
            />
          </Dropdown>
          
          <Tooltip title="删除讲稿">
            <Popconfirm
              title="确定要删除这个讲稿吗？删除后无法恢复。"
              onConfirm={() => deleteScriptMutation.mutate(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                type="text"
                icon={<DeleteOutlined />}
                size="small"
                danger
                loading={deleteScriptMutation.isLoading}
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div className="scripts-page">
      {/* 页面标题 */}
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>讲稿管理</Title>
        <Paragraph type="secondary">
          {currentProject ? 
            `项目：${currentProject.name} - 管理和编辑项目中的讲稿内容` : 
            '请在顶部选择一个项目以查看相关讲稿'
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
                请选择一个项目以查看项目相关的讲稿列表
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
        <>
        {/* 统计卡片 */}
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col xs={24} sm={6}>
            <Card size="small">
              <Statistic
                title="总讲稿数"
                value={scripts.length}
                prefix={<FileTextOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card size="small">
              <Statistic
                title="活跃讲稿"
                value={scripts.filter(s => s.is_active).length}
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card size="small">
              <Statistic
                title="总字数"
                value={scripts.reduce((sum, s) => sum + (s.word_count || 0), 0)}
                formatter={(value) => ScriptService.formatWordCount(value as number)}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card size="small">
              <Statistic
                title="总时长"
                value={scripts.reduce((sum, s) => sum + (s.estimated_duration || 0), 0)}
                formatter={(value) => ScriptService.formatEstimatedDuration(value as number)}
                prefix={<ClockCircleOutlined />}
                valueStyle={{ color: '#fa541c' }}
              />
            </Card>
          </Col>
        </Row>

      <Card>
        {/* 筛选和搜索工具栏 */}
        <div style={{ marginBottom: 16 }}>
          <Row gutter={[16, 16]} align="middle">
            <Col xs={24} sm={8} md={6}>
              <Search
                placeholder="搜索讲稿标题或内容"
                value={filters.search}
                onChange={e => setFilters(prev => ({ ...prev, search: e.target.value }))}
                allowClear
              />
            </Col>
            <Col xs={24} sm={8} md={4}>
              <Select
                placeholder="筛选任务"
                value={filters.task_id}
                onChange={value => setFilters(prev => ({ ...prev, task_id: value }))}
                allowClear
                style={{ width: '100%' }}
              >
                {tasks.map(task => {
                  const file = fileMap[task.file_id];
                  return (
                    <Option key={task.id} value={task.id}>
                      {file?.original_name || `任务${task.id}`}
                    </Option>
                  );
                })}
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
            <Col>
              <Space>
                <Switch
                  checkedChildren="显示全部"
                  unCheckedChildren="仅活跃"
                  checked={filters.showInactive}
                  onChange={checked => setFilters(prev => ({ ...prev, showInactive: checked }))}
                />
                <Button
                  icon={<ReloadOutlined />}
                  onClick={() => {
                    queryClient.invalidateQueries(['scripts', currentProject?.id]);
                    queryClient.invalidateQueries(['tasks', currentProject?.id]);
                    queryClient.invalidateQueries(['files', currentProject?.id]);
                  }}
                  loading={isLoading}
                >
                  刷新
                </Button>
              </Space>
            </Col>
          </Row>
        </div>

        {/* 批量操作工具栏 */}
        {selectedScripts.length > 0 && (
          <div style={{ marginBottom: 16, padding: 12, background: '#f0f8ff', borderRadius: 6 }}>
            <Space>
              <Text>已选择 {selectedScripts.length} 个讲稿</Text>
              <Button
                size="small"
                onClick={() => setSelectedScripts([])}
              >
                取消选择
              </Button>
            </Space>
          </div>
        )}

        {/* 讲稿表格 */}
        <Table
          columns={columns}
          dataSource={filteredScripts}
          rowKey="id"
          loading={isLoading}
          rowSelection={{
            selectedRowKeys: selectedScripts,
            onChange: setSelectedScripts,
          }}
          pagination={{
            total: filteredScripts.length,
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 讲稿详情模态框 */}
      <Modal
        title="讲稿详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>,
          <Button
            key="edit"
            type="primary"
            onClick={() => {
              setDetailModalVisible(false);
              setEditModalVisible(true);
            }}
          >
            编辑
          </Button>,
        ]}
        width={800}
      >
        {selectedScript && (
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="讲稿ID" span={1}>
              {selectedScript.id}
            </Descriptions.Item>
            <Descriptions.Item label="版本" span={1}>
              <Tag color="blue">v{selectedScript.version}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="标题" span={2}>
              {selectedScript.title}
            </Descriptions.Item>
            <Descriptions.Item label="字数统计" span={1}>
              {ScriptService.formatWordCount(selectedScript.word_count)}
            </Descriptions.Item>
            <Descriptions.Item label="预估时长" span={1}>
              {ScriptService.formatEstimatedDuration(selectedScript.estimated_duration)}
            </Descriptions.Item>
            <Descriptions.Item label="创建时间" span={1}>
              {formatDateTime(selectedScript.created_at)}
            </Descriptions.Item>
            <Descriptions.Item label="更新时间" span={1}>
              {formatDateTime(selectedScript.updated_at)}
            </Descriptions.Item>
            <Descriptions.Item label="文件大小" span={1}>
              {selectedScript.file_size} 字节
            </Descriptions.Item>
            <Descriptions.Item label="状态" span={1}>
              <Tag color={selectedScript.is_active ? 'green' : 'default'}>
                {selectedScript.is_active ? '活跃' : '归档'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="内容摘要" span={2}>
              <Text type="secondary">
                {ScriptService.extractSummary(selectedScript.content || '', 300)}
              </Text>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      {/* 讲稿编辑模态框 */}
      <ScriptEditModal
        script={selectedScript || undefined}
        visible={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        onSuccess={() => setEditModalVisible(false)}
      />

      {/* 讲稿预览模态框 */}
      <Modal
        title={`预览 - ${selectedScript?.title}`}
        open={previewModalVisible}
        onCancel={() => setPreviewModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setPreviewModalVisible(false)}>
            关闭
          </Button>,
        ]}
        width={900}
        style={{ top: 20 }}
      >
        <div
          style={{
            maxHeight: '60vh',
            overflow: 'auto',
            padding: '16px',
            background: '#fafafa',
            border: '1px solid #d9d9d9',
            borderRadius: '6px',
          }}
        >
          <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>
            {previewContent}
          </pre>
        </div>
      </Modal>
        </>
      )}
    </div>
  );
};

export default Scripts;