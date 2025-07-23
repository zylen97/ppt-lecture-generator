import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Layout,
  Menu,
  Typography,
  Avatar,
  Dropdown,
  Space,
  Button,
  theme,
  Divider,
} from 'antd';
import {
  DashboardOutlined,
  UnorderedListOutlined,
  FileTextOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SoundOutlined,
  FolderOutlined,
} from '@ant-design/icons';
import { useCurrentProject } from '@/contexts';
import { ProjectSelector } from '@/components/Project';

const { Header, Sider, Content } = Layout;
const { Title, Text } = Typography;

const AppLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { token } = theme.useToken();
  const { currentProject } = useCurrentProject();

  // 菜单项配置
  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表盘',
    },
    {
      key: '/projects',
      icon: <UnorderedListOutlined />,
      label: '项目管理',
    },
    {
      key: '/ppt-processor',
      icon: <FileTextOutlined />,
      label: 'PPT生成讲稿',
    },
    {
      key: '/media-processor',
      icon: <SoundOutlined />,
      label: '音视频转讲稿',
    },
    {
      key: '/scripts',
      icon: <FileTextOutlined />,
      label: '讲稿管理',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '系统设置',
    },
  ];

  // 用户菜单
  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人设置',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  const handleUserMenuClick = ({ key }: { key: string }) => {
    switch (key) {
      case 'profile':
        // 处理个人设置
        break;
      case 'logout':
        // 处理退出登录
        break;
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        width={240}
        style={{
          background: token.colorBgContainer,
          borderRight: `1px solid ${token.colorBorder}`,
        }}
      >
        {/* Logo区域 */}
        <div
          style={{
            height: 64,
            padding: '16px',
            display: 'flex',
            alignItems: 'center',
            borderBottom: `1px solid ${token.colorBorder}`,
          }}
        >
          <div
            style={{
              width: 32,
              height: 32,
              background: token.colorPrimary,
              borderRadius: 8,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginRight: collapsed ? 0 : 12,
              color: 'white',
              fontWeight: 'bold',
              fontSize: 18,
            }}
          >
            P
          </div>
          {!collapsed && (
            <Title level={5} style={{ margin: 0, color: token.colorText }}>
              PPT讲稿生成器
            </Title>
          )}
        </div>

        {/* 导航菜单 */}
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{
            border: 'none',
            background: 'transparent',
          }}
        />
      </Sider>

      <Layout>
        {/* 头部 */}
        <Header
          style={{
            padding: '0 24px',
            background: token.colorBgContainer,
            borderBottom: `1px solid ${token.colorBorder}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              style={{
                fontSize: '16px',
                width: 64,
                height: 64,
              }}
            />
          </div>

          {/* 全局项目选择器 */}
          <div style={{ display: 'flex', alignItems: 'center', flex: 1, justifyContent: 'center' }}>
            <Space align="center" size="middle">
              <FolderOutlined style={{ color: token.colorTextSecondary }} />
              <Text strong style={{ color: token.colorText }}>
                {currentProject ? currentProject.name : '未选择项目'}
              </Text>
              <Divider type="vertical" />
              <ProjectSelector 
                style={{ minWidth: 220 }}
                placeholder="选择或创建项目"
                onCreateProject={() => navigate('/projects')}
              />
            </Space>
          </div>

          <div>
            <Dropdown
              menu={{
                items: userMenuItems,
                onClick: handleUserMenuClick,
              }}
              placement="bottomRight"
            >
              <Space style={{ cursor: 'pointer' }}>
                <Avatar size={32} icon={<UserOutlined />} />
                {!collapsed && <span>用户</span>}
              </Space>
            </Dropdown>
          </div>
        </Header>

        {/* 内容区域 */}
        <Content
          style={{
            margin: '24px',
            padding: '24px',
            background: token.colorBgContainer,
            borderRadius: token.borderRadius,
            minHeight: 360,
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default AppLayout;