import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Button, 
  Space, 
  Typography,
  Avatar,
  Tag,
  Descriptions,
  Progress,
  Statistic,
  Table,
  Tabs,
  Empty,
  Spin,
  Dropdown,
  Modal,
  message,
  Breadcrumb
} from 'antd';
import {
  ArrowLeftOutlined,
  EditOutlined,
  MoreOutlined,
  FolderOutlined,
  FileTextOutlined,
  CalendarOutlined,
  UserOutlined,
  BookOutlined,
  TeamOutlined,
  DownloadOutlined,
  DeleteOutlined,
  InboxOutlined,
  ReloadOutlined,
  PieChartOutlined
} from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { Project, FileInfo, Task, Script } from '@/types';
import { ProjectService, FileService, TaskService, ScriptService } from '@/services';
import { useCurrentProject } from '@/contexts';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

const ProjectDetail: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [project, setProject] = useState<Project | null>(null);
  const [projectFiles, setProjectFiles] = useState<FileInfo[]>([]);
  const [projectTasks, setProjectTasks] = useState<Task[]>([]);
  const [projectScripts, setProjectScripts] = useState<Script[]>([]);
  const [activeTab, setActiveTab] = useState('overview');

  const { selectProject } = useCurrentProject();

  // 加载项目详情
  const loadProjectDetail = async () => {
    if (!projectId) return;
    
    try {
      setLoading(true);
      const projectData = await ProjectService.getProject(parseInt(projectId), true);
      setProject(projectData);
      
      // 设置为当前项目
      selectProject(parseInt(projectId));
      
      // 加载关联数据
      await Promise.all([
        loadProjectFiles(parseInt(projectId)),
        loadProjectTasks(parseInt(projectId)),
        loadProjectScripts(parseInt(projectId))
      ]);
    } catch (error) {
      message.error('加载项目详情失败');
      navigate('/projects');
    } finally {
      setLoading(false);
    }
  };

  // 加载项目文件
  const loadProjectFiles = async (projectId: number) => {
    try {
      const files = await FileService.getFiles({ project_id: projectId });
      setProjectFiles(files);
    } catch (error) {
      console.error('Failed to load project files:', error);
    }
  };

  // 加载项目任务
  const loadProjectTasks = async (projectId: number) => {
    try {
      const tasks = await TaskService.getTasks({ project_id: projectId });
      setProjectTasks(tasks);
    } catch (error) {
      console.error('Failed to load project tasks:', error);
    }
  };

  // 加载项目讲稿
  const loadProjectScripts = async (projectId: number) => {
    try {
      const scripts = await ScriptService.getScripts({ project_id: projectId });
      setProjectScripts(scripts);
    } catch (error) {
      console.error('Failed to load project scripts:', error);
    }
  };

  // 初始化
  useEffect(() => {
    loadProjectDetail();
  }, [projectId]);

  // 返回项目列表
  const handleBack = () => {
    navigate('/projects');
  };

  // 编辑项目
  const handleEditProject = () => {
    // 这里可以打开编辑对话框或跳转到编辑页面
    message.info('编辑功能待实现');
  };

  // 项目操作菜单
  const projectActionMenu = {
    items: [
      {
        key: 'edit',
        label: '编辑项目',
        icon: <EditOutlined />,
        onClick: handleEditProject,
      },
      {
        key: 'archive',
        label: project?.is_active ? '归档项目' : '恢复项目',
        icon: <InboxOutlined />,
        onClick: () => {
          // 归档/恢复项目逻辑
          message.info('归档功能待实现');
        },
      },
      {
        key: 'delete',
        label: '删除项目',
        icon: <DeleteOutlined />,
        danger: true,
        onClick: () => {
          Modal.confirm({
            title: '确认删除',
            content: '确定要删除这个项目吗？此操作无法撤销。',
            onOk: () => {
              message.info('删除功能待实现');
            },
          });
        },
      },
    ],
  };

  // 文件表格列
  const fileColumns = [
    {
      title: '文件名',
      dataIndex: 'original_name',
      key: 'original_name',
      ellipsis: true,
    },
    {
      title: '文件类型',
      dataIndex: 'file_type',
      key: 'file_type',
      render: (type: string) => <Tag>{type.toUpperCase()}</Tag>,
    },
    {
      title: '文件大小',
      dataIndex: 'file_size',
      key: 'file_size',
      render: (size: number) => FileService.formatFileSize(size),
    },
    {
      title: '上传时间',
      dataIndex: 'upload_time',
      key: 'upload_time',
      render: (time: string) => new Date(time).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: FileInfo) => (
        <Space>
          <Button 
            type="link" 
            size="small"
            onClick={() => FileService.downloadFile(record.id)}
          >
            下载
          </Button>
          <Button 
            type="link" 
            size="small" 
            danger
            onClick={() => {
              Modal.confirm({
                title: '确认删除',
                content: '确定要删除这个文件吗？',
                onOk: async () => {
                  try {
                    await FileService.deleteFile(record.id);
                    message.success('文件删除成功');
                    loadProjectFiles(parseInt(projectId!));
                  } catch (error) {
                    message.error('文件删除失败');
                  }
                },
              });
            }}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  // 任务表格列
  const taskColumns = [
    {
      title: '任务类型',
      dataIndex: 'task_type',
      key: 'task_type',
      render: (type: string) => TaskService.getTaskTypeText(type as any),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={TaskService.getStatusColor(status as any)}>
          {TaskService.getStatusText(status as any)}
        </Tag>
      ),
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      render: (progress: number) => <Progress percent={progress} size="small" />,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time: string) => time ? new Date(time).toLocaleString('zh-CN') : '-',
    },
    {
      title: '完成时间',
      dataIndex: 'completed_at',
      key: 'completed_at',
      render: (time: string) => time ? new Date(time).toLocaleString('zh-CN') : '-',
    },
  ];

  // 讲稿表格列
  const scriptColumns = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
    },
    {
      title: '字数',
      dataIndex: 'word_count',
      key: 'word_count',
      render: (count: number) => count ? `${count} 字` : '-',
    },
    {
      title: '预估时长',
      dataIndex: 'estimated_duration',
      key: 'estimated_duration',
      render: (duration: number) => duration ? `${duration} 分钟` : '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time: string) => new Date(time).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: Script) => (
        <Space>
          <Button type="link" size="small">
            查看
          </Button>
          <Button type="link" size="small">
            编辑
          </Button>
          <Button type="link" size="small">
            导出
          </Button>
        </Space>
      ),
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!project) {
    return (
      <Empty
        description="项目不存在"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      >
        <Button type="primary" onClick={handleBack}>
          返回项目列表
        </Button>
      </Empty>
    );
  }

  return (
    <div className="project-detail">
      {/* 面包屑导航 */}
      <Breadcrumb style={{ marginBottom: 16 }}>
        <Breadcrumb.Item>
          <Button type="link" onClick={handleBack} style={{ padding: 0 }}>
            项目管理
          </Button>
        </Breadcrumb.Item>
        <Breadcrumb.Item>{project.name}</Breadcrumb.Item>
      </Breadcrumb>

      {/* 项目头部信息 */}
      <Card style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start' }}>
            <Avatar 
              size={64} 
              icon={<FolderOutlined />}
              style={{ 
                backgroundColor: project.is_active ? '#1890ff' : '#d9d9d9',
                marginRight: 16 
              }}
            />
            <div>
              <Space align="start">
                <Title level={2} style={{ margin: 0 }}>
                  {project.name}
                </Title>
                <Tag color={project.is_active ? 'green' : 'default'}>
                  {project.is_active ? '活跃' : '已归档'}
                </Tag>
              </Space>
              <Paragraph 
                style={{ marginTop: 8, marginBottom: 16, color: '#8c8c8c' }}
              >
                {project.description || '暂无描述'}
              </Paragraph>
              <Space size={16}>
                {project.course_code && (
                  <Space size={4}>
                    <BookOutlined style={{ color: '#8c8c8c' }} />
                    <Text>{project.course_code}</Text>
                  </Space>
                )}
                {project.instructor && (
                  <Space size={4}>
                    <UserOutlined style={{ color: '#8c8c8c' }} />
                    <Text>{project.instructor}</Text>
                  </Space>
                )}
                {project.semester && (
                  <Space size={4}>
                    <CalendarOutlined style={{ color: '#8c8c8c' }} />
                    <Text>{project.semester}</Text>
                  </Space>
                )}
                {project.target_audience && (
                  <Space size={4}>
                    <TeamOutlined style={{ color: '#8c8c8c' }} />
                    <Text>{project.target_audience}</Text>
                  </Space>
                )}
              </Space>
            </div>
          </div>
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={handleBack}>
              返回
            </Button>
            <Button type="primary" icon={<EditOutlined />} onClick={handleEditProject}>
              编辑
            </Button>
            <Dropdown menu={projectActionMenu} trigger={['click']}>
              <Button icon={<MoreOutlined />} />
            </Dropdown>
          </Space>
        </div>
      </Card>

      {/* 统计信息卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="文件数量"
              value={project.total_files}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="任务数量"
              value={project.total_tasks}
              prefix={<PieChartOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="讲稿数量"
              value={project.total_scripts}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="完成率"
              value={project.statistics?.completion_rate || 0}
              suffix="%"
            />
          </Card>
        </Col>
      </Row>

      {/* 详细内容标签页 */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="项目概览" key="overview">
            <Row gutter={16}>
              <Col xs={24} lg={12}>
                <Card title="项目信息" size="small">
                  <Descriptions column={1} size="small">
                    <Descriptions.Item label="项目名称">
                      {project.name}
                    </Descriptions.Item>
                    <Descriptions.Item label="项目描述">
                      {project.description || '暂无描述'}
                    </Descriptions.Item>
                    <Descriptions.Item label="课程代码">
                      {project.course_code || '-'}
                    </Descriptions.Item>
                    <Descriptions.Item label="学期">
                      {project.semester || '-'}
                    </Descriptions.Item>
                    <Descriptions.Item label="授课教师">
                      {project.instructor || '-'}
                    </Descriptions.Item>
                    <Descriptions.Item label="目标群体">
                      {project.target_audience || '-'}
                    </Descriptions.Item>
                    <Descriptions.Item label="创建时间">
                      {new Date(project.created_at).toLocaleString('zh-CN')}
                    </Descriptions.Item>
                    <Descriptions.Item label="最后更新">
                      {new Date(project.updated_at).toLocaleString('zh-CN')}
                    </Descriptions.Item>
                  </Descriptions>
                </Card>
              </Col>
              <Col xs={24} lg={12}>
                <Card title="任务统计" size="small">
                  {project.statistics ? (
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <Row gutter={16}>
                        <Col span={12}>
                          <Statistic 
                            title="待处理" 
                            value={project.statistics.status_summary.pending}
                            valueStyle={{ color: '#faad14' }}
                          />
                        </Col>
                        <Col span={12}>
                          <Statistic 
                            title="处理中" 
                            value={project.statistics.status_summary.processing}
                            valueStyle={{ color: '#1890ff' }}
                          />
                        </Col>
                      </Row>
                      <Row gutter={16}>
                        <Col span={12}>
                          <Statistic 
                            title="已完成" 
                            value={project.statistics.status_summary.completed}
                            valueStyle={{ color: '#52c41a' }}
                          />
                        </Col>
                        <Col span={12}>
                          <Statistic 
                            title="失败" 
                            value={project.statistics.status_summary.failed}
                            valueStyle={{ color: '#ff4d4f' }}
                          />
                        </Col>
                      </Row>
                      <div style={{ marginTop: 16 }}>
                        <Text style={{ marginBottom: 8, display: 'block' }}>总体进度</Text>
                        <Progress 
                          percent={project.statistics.completion_rate}
                          strokeColor={{
                            '0%': '#108ee9',
                            '100%': '#87d068',
                          }}
                        />
                      </div>
                    </Space>
                  ) : (
                    <Empty description="暂无统计数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                  )}
                </Card>
              </Col>
            </Row>
          </TabPane>

          <TabPane tab={`文件 (${projectFiles.length})`} key="files">
            <Table
              columns={fileColumns}
              dataSource={projectFiles}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              locale={{ emptyText: '暂无文件' }}
            />
          </TabPane>

          <TabPane tab={`任务 (${projectTasks.length})`} key="tasks">
            <Table
              columns={taskColumns}
              dataSource={projectTasks}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              locale={{ emptyText: '暂无任务' }}
            />
          </TabPane>

          <TabPane tab={`讲稿 (${projectScripts.length})`} key="scripts">
            <Table
              columns={scriptColumns}
              dataSource={projectScripts}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              locale={{ emptyText: '暂无讲稿' }}
            />
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default ProjectDetail;