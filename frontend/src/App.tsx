import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from '@/lib/auth/AuthContext';
import { RequireAuth } from '@/lib/auth/RequireAuth';
import { Login } from '@/pages/Login';
import { ContentDiscovery } from '@/pages/employee/ContentDiscovery';
import { AssignmentWatch } from '@/pages/employee/AssignmentWatch';
import { Dashboard } from '@/pages/hr/Dashboard';
import { VideoPlayerDemo } from '@/pages/dev/VideoPlayerDemo';
import { ApiKeysModalDemo } from '@/pages/dev/ApiKeysModalDemo';
import { ManualContentEntryDemo } from '@/pages/dev/ManualContentEntryDemo';
import { CurrentlyApprovedContentDemo } from '@/pages/dev/CurrentlyApprovedContentDemo';

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
          <Route
            path="/dev/api-keys-modal-demo"
            element={
              <RequireAuth>
                <ApiKeysModalDemo />
              </RequireAuth>
            }
          />
          <Route
            path="/dev/manual-content-entry-demo"
            element={
              <RequireAuth>
                <ManualContentEntryDemo />
              </RequireAuth>
            }
          />
          <Route
            path="/dev/currently-approved-content-demo"
            element={
              <RequireAuth>
                <CurrentlyApprovedContentDemo />
              </RequireAuth>
            }
          />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
