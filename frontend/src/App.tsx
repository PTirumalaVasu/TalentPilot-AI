import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from '@/lib/auth/AuthContext';
import { RequireAuth } from '@/lib/auth/RequireAuth';
import { Login } from '@/pages/Login';
import { DashboardStub } from '@/pages/hr/DashboardStub';
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
                <DashboardStub />
              </RequireAuth>
            }
          />
          <Route
            path="/employee/content"
            element={
              <RequireAuth>
                <ContentDiscoveryStub />
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
