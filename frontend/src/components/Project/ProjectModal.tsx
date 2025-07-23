import React, { useState, useEffect } from 'react';
import { 
  Modal, 
  Form, 
  Input, 
  Select, 
  Switch, 
  Button, 
  Space,
  Divider,
  Spin,
  Card,
  Tag
} from 'antd';
import { 
  BookOutlined, 
  UserOutlined,
  TeamOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { Project, ProjectTemplate, ProjectCreate } from '@/types';
import { ProjectService } from '@/services';

const { Option } = Select;
const { TextArea } = Input;

interface ProjectModalProps {
  visible: boolean;
  onCancel: () => void;
  onSuccess: (project: Project) => void;
  editingProject?: Project | null;
  initialTemplate?: string;
}

const ProjectModal: React.FC<ProjectModalProps> = ({
  visible,
  onCancel,
  onSuccess,
  editingProject,
  initialTemplate,
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [templatesLoading, setTemplatesLoading] = useState(false);
  const [templates, setTemplates] = useState<ProjectTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<ProjectTemplate | null>(null);

  const isEditing = !!editingProject;
  const modalTitle = isEditing ? '编辑项目' : '创建项目';

  // 加载项目模板
  const loadTemplates = async () => {
    try {
      setTemplatesLoading(true);
      const templatesData = await ProjectService.getProjectTemplates();
      setTemplates(templatesData);
      
      // 如果有初始模板，设置选中状态
      if (initialTemplate) {
        const template = templatesData.find(t => t.id === initialTemplate);
        if (template) {
          setSelectedTemplate(template);
          applyTemplate(template);
        }
      }
    } catch (error) {
      console.error('Failed to load templates:', error);
    } finally {
      setTemplatesLoading(false);
    }
  };

  // 应用模板
  const applyTemplate = (template: ProjectTemplate) => {
    const templateData: Partial<ProjectCreate> = {};
    
    // 根据模板字段设置表单值
    template.fields.forEach(field => {
      if (template.example[field] && template.example[field] !== `{{${field}}}`) {
        (templateData as any)[field] = template.example[field];
      }
    });

    form.setFieldsValue(templateData as any);
  };

  // 处理模板选择
  const handleTemplateSelect = (templateId: string) => {
    const template = templates.find(t => t.id === templateId);
    if (template) {
      setSelectedTemplate(template);
      applyTemplate(template);
    }
  };

  // 处理表单提交
  const handleSubmit = async (values: any) => {
    try {
      setLoading(true);
      
      const projectData = {
        ...values,
        is_active: values.is_active !== false, // 默认为true
      };

      let project: Project;
      if (isEditing) {
        project = await ProjectService.updateProject(editingProject.id, projectData);
      } else {
        project = await ProjectService.createProject(projectData);
      }

      onSuccess(project);
      handleClose();
    } catch (error) {
      console.error('Failed to save project:', error);
    } finally {
      setLoading(false);
    }
  };

  // 关闭对话框
  const handleClose = () => {
    form.resetFields();
    setSelectedTemplate(null);
    onCancel();
  };

  // 验证项目名称
  const validateProjectName = async (_: any, value: string) => {
    if (!value) return Promise.resolve();
    
    const validation = ProjectService.validateProjectName(value);
    if (!validation.valid) {
      return Promise.reject(new Error(validation.message));
    }
  };

  // 验证课程代码
  const validateCourseCode = async (_: any, value: string) => {
    if (!value) return Promise.resolve();
    
    const validation = ProjectService.validateCourseCode(value);
    if (!validation.valid) {
      return Promise.reject(new Error(validation.message));
    }
  };

  // 初始化表单数据
  useEffect(() => {
    if (visible) {
      if (isEditing && editingProject) {
        // 编辑模式：填充现有项目数据
        form.setFieldsValue({
          name: editingProject.name,
          description: editingProject.description,
          course_code: editingProject.course_code,
          semester: editingProject.semester,
          instructor: editingProject.instructor,
          target_audience: editingProject.target_audience,
          is_active: editingProject.is_active,
        });
      } else {
        // 创建模式：加载模板
        loadTemplates();
      }
    }
  }, [visible, isEditing, editingProject]);

  // 渲染模板选择区域
  const renderTemplateSelection = () => {
    if (isEditing) return null;

    return (
      <>
        <Form.Item label="项目模板">
          <Spin spinning={templatesLoading}>
            <Select
              placeholder="选择项目模板（可选）"
              allowClear
              onChange={handleTemplateSelect}
              value={selectedTemplate?.id}
            >
              {templates.map(template => (
                <Option key={template.id} value={template.id}>
                  <Space>
                    <strong>{template.name}</strong>
                    <span style={{ color: '#8c8c8c' }}>- {template.description}</span>
                  </Space>
                </Option>
              ))}
            </Select>
          </Spin>
        </Form.Item>

        {selectedTemplate && (
          <Card size="small" style={{ marginBottom: 16 }}>
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <Space>
                <InfoCircleOutlined style={{ color: '#1890ff' }} />
                <strong>模板信息：{selectedTemplate.name}</strong>
              </Space>
              <div style={{ color: '#8c8c8c' }}>{selectedTemplate.description}</div>
              <div>
                <span style={{ marginRight: 8 }}>包含字段：</span>
                {selectedTemplate.fields.map(field => (
                  <Tag key={field} color="blue" style={{ marginBottom: 4 }}>
                    {field}
                  </Tag>
                ))}
              </div>
            </Space>
          </Card>
        )}

        <Divider />
      </>
    );
  };

  return (
    <Modal
      title={modalTitle}
      open={visible}
      onCancel={handleClose}
      footer={[
        <Button key="cancel" onClick={handleClose}>
          取消
        </Button>,
        <Button 
          key="submit" 
          type="primary" 
          loading={loading}
          onClick={() => form.submit()}
        >
          {isEditing ? '更新' : '创建'}
        </Button>,
      ]}
      width={600}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          is_active: true,
        }}
      >
        {renderTemplateSelection()}

        <Form.Item
          label="项目名称"
          name="name"
          rules={[
            { required: true, message: '请输入项目名称' },
            { validator: validateProjectName }
          ]}
        >
          <Input 
            prefix={<BookOutlined />}
            placeholder="输入项目名称"
            maxLength={100}
            showCount
          />
        </Form.Item>

        <Form.Item
          label="项目描述"
          name="description"
        >
          <TextArea 
            placeholder="项目描述（可选）"
            rows={3}
            maxLength={500}
            showCount
          />
        </Form.Item>

        <Space style={{ width: '100%' }} size="large">
          <Form.Item
            label="课程代码"
            name="course_code"
            style={{ flex: 1 }}
            rules={[{ validator: validateCourseCode }]}
          >
            <Input 
              prefix={<BookOutlined />}
              placeholder="如：CS101"
            />
          </Form.Item>

          <Form.Item
            label="学期"
            name="semester"
            style={{ flex: 1 }}
          >
            <Select placeholder="选择学期">
              <Option value="2024春季">2024春季</Option>
              <Option value="2024夏季">2024夏季</Option>
              <Option value="2024秋季">2024秋季</Option>
              <Option value="2024冬季">2024冬季</Option>
              <Option value="2025春季">2025春季</Option>
              <Option value="2025夏季">2025夏季</Option>
              <Option value="2025秋季">2025秋季</Option>
              <Option value="2025冬季">2025冬季</Option>
            </Select>
          </Form.Item>
        </Space>

        <Space style={{ width: '100%' }} size="large">
          <Form.Item
            label="授课教师"
            name="instructor"
            style={{ flex: 1 }}
          >
            <Input 
              prefix={<UserOutlined />}
              placeholder="教师姓名"
            />
          </Form.Item>

          <Form.Item
            label="目标群体"
            name="target_audience"
            style={{ flex: 1 }}
          >
            <Input 
              prefix={<TeamOutlined />}
              placeholder="如：本科生、研究生"
            />
          </Form.Item>
        </Space>

        <Form.Item
          label="项目状态"
          name="is_active"
          valuePropName="checked"
          extra="非活跃项目将被归档，不会在主列表中显示"
        >
          <Switch 
            checkedChildren="活跃" 
            unCheckedChildren="归档"
          />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default ProjectModal;