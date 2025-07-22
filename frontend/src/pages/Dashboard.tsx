import React from 'react';
import {
  Row,
  Col,
  Card,
  Statistic,
  Progress,
  Timeline,
  List,
  Avatar,
  Typography,
  Space,
  Tag,
  Button,
  Empty,
} from 'antd';
import {
  FileTextOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  UploadOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import { useQuery } from 'react-query';
import { TaskService, FileService, ScriptService } from '@/services';
import { formatDateTime, formatFileSize } from '@/utils';

const { Title, Text, Paragraph } = Typography;

const Dashboard: React.FC = () => {
  // 获取统计数据
  const { data: taskStats } = useQuery(
    'taskStats',
    TaskService.getTaskStats,
    {
      refetchInterval: 30000, // 30秒刷新一次
    }
  );

  const { data: recentFiles } = useQuery(
    'recentFiles',
    () => FileService.getFiles({ limit: 5 }),
    {
      refetchInterval: 30000,
    }
  );

  const { data: recentScripts } = useQuery(
    'recentScripts',
    () => ScriptService.getScripts({ limit: 5 }),
    {
      refetchInterval: 30000,
    }
  );

  // 模拟数据（实际应用中从API获取）
  const systemStatus = {
    apiStatus: 'online',
    uptime: '7天 12小时 30分钟',
    version: '1.0.0',
  };

  const recentActivities = [
    {
      id: 1,
      action: '完成讲稿生成',
      resource: '机器学习基础.pptx',
      time: '2分钟前',
      status: 'success',
    },
    {
      id: 2,
      action: '开始处理文件',
      resource: '数据结构与算法.pptx',
      time: '15分钟前',
      status: 'processing',
    },
    {
      id: 3,
      action: '上传新文件',
      resource: 'Python编程入门.pptx',
      time: '1小时前',
      status: 'info',
    },
    {
      id: 4,
      action: '导出讲稿',
      resource: '计算机网络概论_讲稿.md',
      time: '2小时前',
      status: 'default',
    },
  ];

  const getStatusColor = (status: string) => {
    const colors = {
      success: '#52c41a',
      processing: '#1890ff',
      info: '#722ed1',
      default: '#8c8c8c',
    };
    return colors[status] || colors.default;
  };

  const getStatusIcon = (status: string) => {
    const icons = {
      success: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
      processing: <ClockCircleOutlined style={{ color: '#1890ff' }} />,
      info: <FileTextOutlined style={{ color: '#722ed1' }} />,
      default: <EyeOutlined style={{ color: '#8c8c8c' }} />,
    };
    return icons[status] || icons.default;
  };

  return (
    <div className="dashboard">
      {/* 页面标题 */}
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>仪表盘</Title>
        <Paragraph type="secondary">
          欢迎使用PPT讲稿生成器，这里是系统的总体概况
        </Paragraph>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总任务数"
              value={taskStats?.total || 0}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="处理中"
              value={taskStats?.processing || 0}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="已完成"
              value={taskStats?.completed || 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="失败任务"
              value={taskStats?.failed || 0}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* 系统状态 */}
        <Col xs={24} lg={8}>
          <Card
            title="系统状态"
            extra={
              <Tag color="green">
                {systemStatus.apiStatus === 'online' ? '在线' : '离线'}
              </Tag>
            }
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text strong>运行时间：</Text>
                <Text>{systemStatus.uptime}</Text>
              </div>
              <div>
                <Text strong>版本号：</Text>
                <Text>{systemStatus.version}</Text>
              </div>
              <div>
                <Text strong>API状态：</Text>
                <Tag color={systemStatus.apiStatus === 'online' ? 'green' : 'red'}>
                  {systemStatus.apiStatus === 'online' ? '正常' : '异常'}
                </Tag>
              </div>
              {taskStats && (
                <div style={{ marginTop: 16 }}>
                  <Text strong>完成率：</Text>
                  <Progress
                    percent={
                      taskStats.total > 0
                        ? Math.round((taskStats.completed / taskStats.total) * 100)
                        : 0
                    }
                    status="active"
                    strokeColor={{
                      from: '#108ee9',
                      to: '#87d068',
                    }}
                  />
                </div>
              )}
            </Space>
          </Card>
        </Col>

        {/* 最近文件 */}
        <Col xs={24} lg={8}>
          <Card
            title="最近上传"
            extra={
              <Button
                type="link"
                icon={<UploadOutlined />}
                href="/upload"
              >
                上传文件
              </Button>
            }
          >
            {recentFiles && recentFiles.length > 0 ? (
              <List
                dataSource={recentFiles}
                renderItem={(file) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={<Avatar icon={<FileTextOutlined />} />}
                      title={
                        <Text ellipsis title={file.original_name}>
                          {file.original_name}
                        </Text>
                      }
                      description={
                        <Space size="small">
                          <Text type="secondary">
                            {formatFileSize(file.file_size)}
                          </Text>
                          <Text type="secondary">
                            {formatDateTime(file.upload_time, 'MM-DD HH:mm')}
                          </Text>
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            ) : (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="暂无文件"
              />
            )}
          </Card>
        </Col>

        {/* 最近活动 */}
        <Col xs={24} lg={8}>
          <Card title="最近活动">
            <Timeline
              items={recentActivities.map((activity) => ({
                dot: getStatusIcon(activity.status),
                children: (
                  <div>
                    <div>
                      <Text strong>{activity.action}</Text>
                    </div>
                    <div>
                      <Text ellipsis title={activity.resource}>
                        {activity.resource}
                      </Text>
                    </div>
                    <div>
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        {activity.time}
                      </Text>
                    </div>
                  </div>
                ),
              }))}
            />
          </Card>
        </Col>
      </Row>

      {/* 最近生成的讲稿 */}
      {recentScripts && recentScripts.length > 0 && (
        <Row style={{ marginTop: 16 }}>
          <Col span={24}>
            <Card
              title="最近生成的讲稿"
              extra={
                <Button type="link" href="/scripts">
                  查看全部
                </Button>
              }
            >
              <List
                grid={{ gutter: 16, xs: 1, sm: 2, md: 3, lg: 4, xl: 4 }}
                dataSource={recentScripts}
                renderItem={(script) => (
                  <List.Item>
                    <Card
                      size="small"
                      hoverable
                      actions={[
                        <EyeOutlined key="view" />,
                      ]}
                    >
                      <Card.Meta
                        title={
                          <Text ellipsis title={script.title}>
                            {script.title}
                          </Text>
                        }
                        description={
                          <Space direction="vertical" size="small">
                            <Text type="secondary">
                              {script.word_count ? `${script.word_count}字` : '未统计'}
                            </Text>
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                              {formatDateTime(script.created_at, 'MM-DD HH:mm')}
                            </Text>
                          </Space>
                        }
                      />
                    </Card>
                  </List.Item>
                )}
              />
            </Card>
          </Col>
        </Row>
      )}
    </div>
  );
};

export default Dashboard;