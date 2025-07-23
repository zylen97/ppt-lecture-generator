import React, { useState, useEffect } from 'react';
import {
  Card,
  Statistic,
  Row,
  Col,
} from 'antd';
import {
  SoundOutlined,
  VideoCameraOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import type { FileInfo, Task, FileType, TaskStatus } from '@/types';

interface MediaStatisticsProps {
  files: FileInfo[];
  tasks: Task[];
}

// 数字动画组件
const AnimatedStatistic: React.FC<{
  title: string;
  value: number;
  prefix: React.ReactNode;
  delay?: number;
}> = ({ title, value, prefix, delay = 0 }) => {
  const [displayValue, setDisplayValue] = useState(0);
  
  useEffect(() => {
    const timer = setTimeout(() => {
      const interval = setInterval(() => {
        setDisplayValue(prev => {
          if (prev >= value) {
            clearInterval(interval);
            return value;
          }
          return prev + 1;
        });
      }, 50);
      
      return () => clearInterval(interval);
    }, delay);
    
    return () => clearTimeout(timer);
  }, [value, delay]);
  
  return (
    <Statistic
      title={title}
      value={displayValue}
      prefix={prefix}
      style={{
        animation: `fadeIn 0.6s ease-out ${delay}ms both`
      }}
    />
  );
};

const MediaStatistics: React.FC<MediaStatisticsProps> = ({
  files,
  tasks,
}) => {
  const audioFiles = files.filter((f: FileInfo) => f.file_type === 'audio' as FileType);
  const videoFiles = files.filter((f: FileInfo) => f.file_type === 'video' as FileType);
  const processingTasks = tasks.filter((t: Task) => t.status === 'processing' as TaskStatus);
  const completedTasks = tasks.filter((t: Task) => t.status === 'completed' as TaskStatus);

  return (
    <Row gutter={16} style={{ marginBottom: 24 }}>
      <Col xs={12} sm={6}>
        <Card 
          style={{
            background: '#ffffff',
            boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px 0 rgba(0, 0, 0, 0.02)',
            borderRadius: '8px',
            border: '1px solid #f0f0f0',
            transition: 'all 0.3s ease',
          }}
          className="stat-card-audio"
        >
          <AnimatedStatistic
            title="音频文件"
            value={audioFiles.length}
            prefix={<SoundOutlined style={{ color: '#52c41a' }} />}
            delay={0}
          />
        </Card>
      </Col>
      <Col xs={12} sm={6}>
        <Card 
          style={{
            background: '#ffffff',
            boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px 0 rgba(0, 0, 0, 0.02)',
            borderRadius: '8px',
            border: '1px solid #f0f0f0',
            transition: 'all 0.3s ease',
          }}
          className="stat-card-video"
        >
          <AnimatedStatistic
            title="视频文件"
            value={videoFiles.length}
            prefix={<VideoCameraOutlined style={{ color: '#1890ff' }} />}
            delay={100}
          />
        </Card>
      </Col>
      <Col xs={12} sm={6}>
        <Card 
          style={{
            background: '#ffffff',
            boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px 0 rgba(0, 0, 0, 0.02)',
            borderRadius: '8px',
            border: '1px solid #f0f0f0',
            transition: 'all 0.3s ease',
          }}
          className="stat-card-processing"
        >
          <AnimatedStatistic
            title="转录中"
            value={processingTasks.length}
            prefix={<ClockCircleOutlined style={{ color: '#fa8c16' }} />}
            delay={200}
          />
        </Card>
      </Col>
      <Col xs={12} sm={6}>
        <Card 
          style={{
            background: '#ffffff',
            boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px 0 rgba(0, 0, 0, 0.02)',
            borderRadius: '8px',
            border: '1px solid #f0f0f0',
            transition: 'all 0.3s ease',
          }}
          className="stat-card-completed"
        >
          <AnimatedStatistic
            title="已完成"
            value={completedTasks.length}
            prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
            delay={300}
          />
        </Card>
      </Col>
    </Row>
  );
};

export default MediaStatistics;