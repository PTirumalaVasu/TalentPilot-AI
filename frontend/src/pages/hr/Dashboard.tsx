/**HR Admin Dashboard page with navigation (Story 5-1)."""
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth/AuthContext";
import { logout } from "@/lib/api/authApi";
import { AssignmentModal } from "@/features/assignments/AssignmentModal";
import { DashboardPage } from "@/features/dashboard/DashboardPage";

export function Dashboard() {
  const { signOut } = useAuth();
  const navigate = useNavigate();
  const [assignmentModalOpen, setAssignmentModalOpen] = useState(false);

  async function handleSignOut() {
    try {
      await logout();
    } catch {
      // Best-effort server-side revocation: if the request fails (network
      // error, 5xx), the user's intent to sign out is still honored
      // client-side below, matching AC6's guarantee.
    } finally {
      signOut();
      navigate("/login", { replace: true });
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header/Navigation */}
      <header className="bg-white border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">TalentPilot</h1>
            <nav className="text-sm text-gray-600 ml-6">
              <span className="font-medium text-gray-900">Dashboard</span>
            </nav>
          </div>
          <div className="flex items-center gap-2">
            <Button onClick={() => setAssignmentModalOpen(true)}>+ New Assignment</Button>
            <Button variant="outline" onClick={handleSignOut}>
              Sign Out
            </Button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="py-6">
        <DashboardPage />
      </main>

      {/* Assignment Modal */}
      <AssignmentModal
        open={assignmentModalOpen}
        onClose={() => setAssignmentModalOpen(false)}
      />
    </div>
  );
}
