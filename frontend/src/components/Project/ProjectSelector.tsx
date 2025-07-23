import React, { useState, useMemo } from 'react';
import { Select, Space, Typography, Button, Avatar, Spin, Empty } from 'antd';
import { 
  FolderOutlined, 
  PlusOutlined, 
  SearchOutlined,
  BookOutlined,
  UserOutlined,
  CalendarOutlined
} from '@ant-design/icons';
import { useCurrentProject, useProjectList } from '@/contexts';
import { ProjectSummary } from '@/types';

const { Option } = Select;
const { Text } = Typography;

interface ProjectSelectorProps {
  placeholder?: string;
  allowClear?: boolean;
  showCreateBtn?: boolean;
  size?: 'small' | 'middle' | 'large';
  style?: React.CSSProperties;
  onCreateProject?: () => void;
  disabled?: boolean;
  dropdownClassName?: string;
}

const ProjectSelector: React.FC<ProjectSelectorProps> = ({
  placeholder = "选择项目",
  allowClear = true,
  showCreateBtn = true,
  size = 'middle',
  style,
  onCreateProject,
  disabled = false,
  dropdownClassName,
}) => {
  const [searchValue, setSearchValue] = useState('');
  const { currentProject, selectProject, clearCurrentProject } = useCurrentProject();
  const { projects, projectsLoading, searchProjects } = useProjectList();

  // 过滤项目
  const filteredProjects = useMemo(() => {
    if (!searchValue) return projects;
    
    const searchLower = searchValue.toLowerCase();
    return projects.filter(project => 
      project.name.toLowerCase().includes(searchLower) ||
      project.course_code?.toLowerCase().includes(searchLower) ||
      project.instructor?.toLowerCase().includes(searchLower) ||
      project.semester?.toLowerCase().includes(searchLower)
    );
  }, [projects, searchValue]);

  // 处理项目选择
  const handleProjectSelect = (projectId: number | null) => {
    if (projectId === null) {
      clearCurrentProject();
    } else {
      selectProject(projectId);
    }
  };

  // 处理搜索
  const handleSearch = (value: string) => {
    setSearchValue(value);
    if (value && value.length > 1) {
      searchProjects(value);
    }
  };

  // 渲染项目选项
  const renderProjectOption = (project: ProjectSummary) => (
    <Option key={project.id} value={project.id}>
      <div style={{ display: 'flex', alignItems: 'center', padding: '4px 0' }}>
        <Avatar 
          size="small" 
          icon={<FolderOutlined />} 
          style={{ 
            backgroundColor: project.is_active ? '#1890ff' : '#d9d9d9',
            marginRight: 8,
            flexShrink: 0,
          }} 
        />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ 
            fontWeight: 500, 
            fontSize: '14px',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap'
          }}>
            {project.name}
          </div>
          <Space size={8} style={{ fontSize: '12px', color: '#8c8c8c' }}>
            {project.course_code && (
              <Space size={2}>
                <BookOutlined />
                <span>{project.course_code}</span>
              </Space>
            )}
            {project.instructor && (
              <Space size={2}>
                <UserOutlined />
                <span>{project.instructor}</span>
              </Space>
            )}
            {project.semester && (
              <Space size={2}>
                <CalendarOutlined />
                <span>{project.semester}</span>
              </Space>
            )}
          </Space>
        </div>
        <div style={{ 
          textAlign: 'right', 
          fontSize: '12px', 
          color: '#8c8c8c',
          marginLeft: 8,
          flexShrink: 0,
        }}>
          <div>{project.completion_rate}% 完成</div>
          <div>{project.file_count} 文件</div>
        </div>
      </div>
    </Option>
  );

  // 渲染空状态
  const renderEmpty = () => (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <Empty 
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        description={
          searchValue ? `未找到"${searchValue}"相关项目` : '暂无项目'
        }
      >
        {showCreateBtn && (
          <Button 
            type="primary" 
            icon={<PlusOutlined />} 
            onClick={onCreateProject}
            size="small"
          >
            创建项目
          </Button>
        )}
      </Empty>
    </div>
  );

  // 渲染下拉菜单底部
  const renderDropdownFooter = () => {
    if (!showCreateBtn) return null;
    
    return (
      <div style={{ 
        borderTop: '1px solid #f0f0f0', 
        padding: '8px 12px',
        backgroundColor: '#fafafa' 
      }}>
        <Button 
          type="link" 
          icon={<PlusOutlined />} 
          onClick={onCreateProject}
          style={{ padding: 0, height: 'auto' }}
        >
          创建新项目
        </Button>
      </div>
    );
  };

  return (
    <Select
      value={currentProject?.id || undefined}
      placeholder={placeholder}
      allowClear={allowClear}
      showSearch
      size={size}
      style={{ minWidth: 200, ...style }}
      disabled={disabled}
      loading={projectsLoading}
      searchValue={searchValue}
      onSearch={handleSearch}
      onChange={handleProjectSelect}
      dropdownClassName={dropdownClassName}
      optionFilterProp="children"
      notFoundContent={projectsLoading ? <Spin size="small" /> : renderEmpty()}
      dropdownRender={(menu) => (
        <div>
          {menu}
          {renderDropdownFooter()}
        </div>
      )}
      dropdownStyle={{ maxHeight: 400 }}
    >
      {filteredProjects.map(renderProjectOption)}
    </Select>
  );
};

export default ProjectSelector;