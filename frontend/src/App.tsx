import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from 'antd'
import AppLayout from '@/components/Layout/AppLayout'
import Dashboard from '@/pages/Dashboard'
import Upload from '@/pages/Upload'
import Tasks from '@/pages/Tasks'
import Scripts from '@/pages/Scripts'
import Settings from '@/pages/Settings'
import NotFound from '@/pages/NotFound'

const App: React.FC = () => {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          {/* 默认重定向到仪表盘 */}
          <Route index element={<Navigate to="/dashboard" replace />} />
          
          {/* 主要页面 */}
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="upload" element={<Upload />} />
          <Route path="tasks" element={<Tasks />} />
          <Route path="scripts" element={<Scripts />} />
          <Route path="settings" element={<Settings />} />
          
          {/* 404页面 */}
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </Layout>
  )
}

export default App