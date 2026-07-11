import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from '@/lib/auth/AuthContext';
import { RequireAuth } from '@/lib/auth/RequireAuth';
import { Login } from '@/pages/Login';
import { DashboardStub } from '@/pages/hr/DashboardStub';
import { ContentDiscovery } from '@/pages/employee/ContentDiscovery';
import { AssignmentWatch } from '@/pages/employee/AssignmentWatch';
import { Dashboard } from '@/pages/hr/Dashboard';
import { ContentDiscoveryStub } from '@/pages/employee/ContentDiscoveryStub';
import { VideoPlayerDemo } from '@/pages/dev/VideoPlayerDemo';

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/hr/dashboard"
            element={
              <RequireAuth>
                <Dashboard />
              </RequireAuth>
            }
          />
          <Route
            path="/employee/content"
            element={
              <RequireAuth>
                <ContentDiscovery />
              </RequireAuth>
            }
          />
          <Route
            path="/assignments/:assignmentId/watch"
            element={
              <RequireAuth>
                <AssignmentWatch />
              </RequireAuth>
            }
          />
          <Route
            path="/dev/video-player-demo"
            element={
              <RequireAuth>
                <VideoPlayerDemo />
              </RequireAuth>
            }
          />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
