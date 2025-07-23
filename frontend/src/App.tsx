import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from 'antd'
import { ProjectProvider } from '@/contexts'
import AppLayout from '@/components/Layout/AppLayout'
import Dashboard from '@/pages/Dashboard'
import PPTProcessor from '@/pages/PPTProcessor'
import AudioVideoProcessor from '@/pages/AudioVideoProcessor'
import Scripts from '@/pages/Scripts'
import Settings from '@/pages/Settings'
import Projects from '@/pages/Projects'
import ProjectDetail from '@/pages/ProjectDetail'
import NotFound from '@/pages/NotFound'

const App: React.FC = () => {
  return (
    <ProjectProvider>
      <Layout style={{ minHeight: '100vh' }}>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            {/* 默认重定向到仪表盘 */}
            <Route index element={<Navigate to="/dashboard" replace />} />
            
            {/* 主要页面 */}
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="projects" element={<Projects />} />
            <Route path="projects/:projectId" element={<ProjectDetail />} />
            <Route path="ppt-processor" element={<PPTProcessor />} />
            <Route path="media-processor" element={<AudioVideoProcessor />} />
            <Route path="scripts" element={<Scripts />} />
            <Route path="settings" element={<Settings />} />
            
            {/* 兼容旧路由的重定向 */}
            <Route path="upload" element={<Navigate to="/ppt-processor" replace />} />
            <Route path="tasks" element={<Navigate to="/ppt-processor" replace />} />
            
            {/* 404页面 */}
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </Layout>
    </ProjectProvider>
  )
}

export default App