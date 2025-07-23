import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Button, 
  Input, 
  Select, 
  Space, 
  Typography,
  Avatar,
  Tag,
  Progress,
  Dropdown,
  Pagination,
  Empty,
  Spin,
  Modal,
  message
} from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  FilterOutlined,
  MoreOutlined,
  FolderOutlined,
  BookOutlined,
  UserOutlined,
  CalendarOutlined,
  FileTextOutlined,
  TeamOutlined,
  EyeOutlined,
  EditOutlined,
  InboxOutlined,
  ReloadOutlined,
  DeleteOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useProjectList } from '@/contexts';
import { ProjectModal } from '@/components/Project';
import { ProjectSummary, Project } from '@/types';
import { ProjectService } from '@/services';

const { Title, Text, Paragraph } = Typography;
const { Search } = Input;
const { Option } = Select;

const Projects: React.FC = () => {
  const navigate = useNavigate();
  const [searchKeyword, setSearchKeyword] = useState('');
  const [modalVisible, setModalVisible] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  
  const {
    projects,
    projectsLoading,
    pagination,
    filters,
    loadProjects,
    refreshProjects,
    searchProjects,
    setFilters,
    createProject,
    updateProject,
    deleteProject,
    archiveProject,
    restoreProject,
  } = useProjectList();

  // 初始化加载
  useEffect(() => {
    if (projects.length === 0) {
      loadProjects({ reset: true });
    }
  }, []);

  // 处理搜索
  const handleSearch = (value: string) => {
    setSearchKeyword(value);
    searchProjects(value);
  };

  // 处理筛选
  const handleFilterChange = (key: string, value: any) => {
    setFilters({ ...filters, [key]: value });
  };

  // 处理分页
  const handlePageChange = (page: number, pageSize?: number) => {
    loadProjects();
  };

  // 打开创建项目对话框
  const handleCreateProject = () => {
    setEditingProject(null);
    setModalVisible(true);
  };

  // 打开编辑项目对话框
  const handleEditProject = async (projectId: number) => {
    try {
      const project = await ProjectService.getProject(projectId);
      setEditingProject(project);
      setModalVisible(true);
    } catch (error) {
      message.error('获取项目详情失败');
    }
  };

  // 查看项目详情
  const handleViewProject = (projectId: number) => {
    navigate(`/projects/${projectId}`);
  };

  // 归档/恢复项目
  const handleArchiveProject = async (project: ProjectSummary) => {
    try {
      if (project.is_active) {
        await archiveProject(project.id);
      } else {
        await restoreProject(project.id);
      }
      refreshProjects();
    } catch (error) {
      // 错误处理已在context中完成
    }
  };

  // 删除项目
  const handleDeleteProject = (project: ProjectSummary) => {
    Modal.confirm({
      title: '确认删除项目',
      content: (
        <div>
          <p>您确定要删除项目 "<strong>{project.name}</strong>" 吗？</p>
          <p style={{ color: '#ff4d4f' }}>
            警告：此操作将删除项目及其关联的所有文件、任务和讲稿，且无法恢复！
          </p>
        </div>
      ),
      okText: '确认删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await deleteProject(project.id, true);
          refreshProjects();
        } catch (error) {
          // 错误处理已在context中完成
        }
      },
    });
  };

  // 处理项目模态框成功
  const handleModalSuccess = (project: Project) => {
    refreshProjects();
  };

  // 生成项目操作菜单
  const getProjectActionMenu = (project: ProjectSummary) => {
    const actions = ProjectService.getProjectActions(project);
    
    return {
      items: actions.map(action => ({
        key: action.key,
        label: action.label,
        icon: action.icon ? React.createElement(
          {
            EyeOutlined,
            EditOutlined,
            InboxOutlined,
            ReloadOutlined,
            DeleteOutlined,
          }[action.icon] || EyeOutlined
        ) : undefined,
        danger: action.danger,
        onClick: () => {
          switch (action.key) {
            case 'view':
              handleViewProject(project.id);
              break;
            case 'edit':
              handleEditProject(project.id);
              break;
            case 'archive':
            case 'restore':
              handleArchiveProject(project);
              break;
            case 'delete':
              handleDeleteProject(project);
              break;
          }
        },
      })),
    };
  };

  // 渲染项目卡片
  const renderProjectCard = (project: ProjectSummary) => (
    <Col xs={24} sm={12} lg={8} xl={6} key={project.id}>
      <Card
        hoverable
        className="project-card"
        style={{ 
          height: '100%',
          cursor: 'pointer'
        }}
        onClick={() => handleViewProject(project.id)}
        actions={[
          <Button 
            type="text" 
            icon={<EyeOutlined />} 
            onClick={(e) => {
              e.stopPropagation();
              handleViewProject(project.id);
            }}
          >
            查看
          </Button>,
          <Button 
            type="text" 
            icon={<EditOutlined />}
            onClick={(e) => {
              e.stopPropagation();
              handleEditProject(project.id);
            }}
          >
            编辑
          </Button>,
          <Dropdown 
            menu={getProjectActionMenu(project)}
            trigger={['click']}
          >
            <Button 
              type="text" 
              icon={<MoreOutlined />}
              onClick={(e) => e.stopPropagation()}
            />
          </Dropdown>,
        ]}
      >
        <Card.Meta
          avatar={
            <Avatar 
              size={48}
              icon={<FolderOutlined />}
              style={{ 
                backgroundColor: project.is_active ? '#1890ff' : '#d9d9d9' 
              }}
            />
          }
          title={
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Text strong ellipsis style={{ flex: 1 }}>
                {project.name}
              </Text>
              <Tag color={project.is_active ? 'green' : 'default'} style={{ marginLeft: 8 }}>
                {project.is_active ? '活跃' : '归档'}
              </Tag>
            </div>
          }
          description={
            <div style={{ minHeight: 60 }}>
              <Paragraph 
                ellipsis={{ rows: 2 }} 
                style={{ margin: 0, color: '#8c8c8c', fontSize: '12px' }}
              >
                {project.description || '暂无描述'}
              </Paragraph>
            </div>
          }
        />
        
        <div style={{ marginTop: 16 }}>
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            {/* 项目信息 */}
            <Space wrap size="small">
              {project.course_code && (
                <Space size={2}>
                  <BookOutlined style={{ fontSize: '12px', color: '#8c8c8c' }} />
                  <Text style={{ fontSize: '12px' }}>{project.course_code}</Text>
                </Space>
              )}
              {project.instructor && (
                <Space size={2}>
                  <UserOutlined style={{ fontSize: '12px', color: '#8c8c8c' }} />
                  <Text style={{ fontSize: '12px' }}>{project.instructor}</Text>
                </Space>
              )}
              {project.semester && (
                <Space size={2}>
                  <CalendarOutlined style={{ fontSize: '12px', color: '#8c8c8c' }} />
                  <Text style={{ fontSize: '12px' }}>{project.semester}</Text>
                </Space>
              )}
            </Space>

            {/* 统计信息 */}
            <Row gutter={8}>
              <Col span={8}>
                <Text style={{ fontSize: '12px', color: '#8c8c8c' }}>文件</Text>
                <div style={{ fontWeight: 500 }}>{project.file_count}</div>
              </Col>
              <Col span={8}>
                <Text style={{ fontSize: '12px', color: '#8c8c8c' }}>任务</Text>
                <div style={{ fontWeight: 500 }}>{project.task_count}</div>
              </Col>
              <Col span={8}>
                <Text style={{ fontSize: '12px', color: '#8c8c8c' }}>讲稿</Text>
                <div style={{ fontWeight: 500 }}>{project.script_count}</div>
              </Col>
            </Row>

            {/* 完成进度 */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <Text style={{ fontSize: '12px', color: '#8c8c8c' }}>完成进度</Text>
                <Text style={{ fontSize: '12px' }}>{project.completion_rate}%</Text>
              </div>
              <Progress 
                percent={project.completion_rate} 
                size="small"
                strokeColor={{
                  '0%': '#108ee9',
                  '100%': '#87d068',
                }}
              />
            </div>

            {/* 创建时间 */}
            <Text style={{ fontSize: '11px', color: '#bfbfbf' }}>
              {ProjectService.formatCreateTime(project.created_at)}
            </Text>
          </Space>
        </div>
      </Card>
    </Col>
  );

  return (
    <div className="projects-page">
      {/* 页面头部 */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <Title level={2} style={{ margin: 0 }}>
            项目管理
          </Title>
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={handleCreateProject}
          >
            创建项目
          </Button>
        </div>

        {/* 搜索和筛选 */}
        <Card size="small">
          <Row gutter={16} align="middle">
            <Col xs={24} sm={12} md={8}>
              <Search
                placeholder="搜索项目名称、课程代码、教师"
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                onSearch={handleSearch}
                allowClear
              />
            </Col>
            <Col xs={12} sm={6} md={4}>
              <Select
                placeholder="学期"
                value={filters.semester}
                onChange={(value) => handleFilterChange('semester', value)}
                allowClear
                style={{ width: '100%' }}
              >
                <Option value="2024春季">2024春季</Option>
                <Option value="2024夏季">2024夏季</Option>
                <Option value="2024秋季">2024秋季</Option>
                <Option value="2024冬季">2024冬季</Option>
                <Option value="2025春季">2025春季</Option>
              </Select>
            </Col>
            <Col xs={12} sm={6} md={4}>
              <Select
                placeholder="状态"
                value={filters.activeOnly ? 'active' : 'all'}
                onChange={(value) => handleFilterChange('activeOnly', value === 'active')}
                style={{ width: '100%' }}
              >
                <Option value="all">全部</Option>
                <Option value="active">活跃</Option>
                <Option value="archived">已归档</Option>
              </Select>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Space>
                <Button 
                  icon={<ReloadOutlined />}
                  onClick={refreshProjects}
                  loading={projectsLoading}
                >
                  刷新
                </Button>
                <Text type="secondary">
                  共 {pagination.total} 个项目
                </Text>
              </Space>
            </Col>
          </Row>
        </Card>
      </div>

      {/* 项目列表 */}
      <Spin spinning={projectsLoading}>
        {projects.length === 0 ? (
          <Card>
            <Empty
              description="暂无项目"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            >
              <Button 
                type="primary" 
                icon={<PlusOutlined />}
                onClick={handleCreateProject}
              >
                创建第一个项目
              </Button>
            </Empty>
          </Card>
        ) : (
          <>
            <Row gutter={[16, 16]}>
              {projects.map(renderProjectCard)}
            </Row>

            {/* 分页 */}
            {pagination.total > pagination.pageSize && (
              <div style={{ textAlign: 'center', marginTop: 24 }}>
                <Pagination
                  current={pagination.current}
                  pageSize={pagination.pageSize}
                  total={pagination.total}
                  onChange={handlePageChange}
                  showSizeChanger
                  showQuickJumper
                  showTotal={(total, range) => 
                    `第 ${range[0]}-${range[1]} 项，共 ${total} 项`
                  }
                />
              </div>
            )}
          </>
        )}
      </Spin>

      {/* 项目创建/编辑对话框 */}
      <ProjectModal
        visible={modalVisible}
        onCancel={() => setModalVisible(false)}
        onSuccess={handleModalSuccess}
        editingProject={editingProject}
      />
    </div>
  );
};

export default Projects;