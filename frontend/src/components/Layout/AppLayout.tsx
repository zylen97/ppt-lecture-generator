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
} from 'antd';
import {
  DashboardOutlined,
  UploadOutlined,
  UnorderedListOutlined,
  FileTextOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';

const { Header, Sider, Content } = Layout;
const { Title } = Typography;

const AppLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { token } = theme.useToken();

  // 菜单项配置
  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表盘',
    },
    {
      key: '/upload',
      icon: <UploadOutlined />,
      label: '上传文件',
    },
    {
      key: '/tasks',
      icon: <UnorderedListOutlined />,
      label: '任务管理',
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