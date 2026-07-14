/** HR Admin Dashboard page with navigation (Story 5-1). */
import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/lib/auth/AuthContext";
import { logout } from "@/lib/api/authApi";
import { AssignmentModal } from "@/features/assignments/AssignmentModal";
import { DashboardPage, type DashboardPageHandle } from "@/features/dashboard/DashboardPage";

export function Dashboard() {
  const { signOut } = useAuth();
  const navigate = useNavigate();
  const [assignmentModalOpen, setAssignmentModalOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const dashboardRef = useRef<DashboardPageHandle>(null);

  async function handleSignOut() {
    try {
      await logout();
    } catch {
      // Best-effort server-side revocation
    } finally {
      signOut();
      navigate("/login", { replace: true });
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 font-sans">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-2 font-bold text-lg text-gray-900">
            TalentPilot-AI
          </div>
          <nav className="flex gap-6 text-sm">
            <a href="#" className="text-blue-600 font-medium border-b-2 border-blue-600 pb-3 -mb-3">Dashboard</a>
            <a href="#" className="text-gray-600 hover:text-gray-900 pb-3 -mb-3 transition-colors">Skills</a>
          </nav>
        </div>
        <div className="relative">
          <button
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            className="flex items-center gap-2 text-sm text-gray-700"
          >
            <span className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-medium">R</span>
            Rita
          </button>
          {userMenuOpen && (
            <div className="absolute right-0 mt-2 w-40 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
              <button
                onClick={() => {
                  setUserMenuOpen(false);
                  handleSignOut();
                }}
                className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg"
              >
                Sign Out
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Main content */}
      <main className="px-6 pb-12">
        <DashboardPage ref={dashboardRef} onNewAssignment={() => setAssignmentModalOpen(true)} />
      </main>

      {/* Assignment Modal */}
      <AssignmentModal
        open={assignmentModalOpen}
        onClose={() => setAssignmentModalOpen(false)}
        onAssigned={(_assignment, employeeName, skillName) => {
          setAssignmentModalOpen(false);
          dashboardRef.current?.refreshGrid();
          // Story 5-6, AC5 (FR-1): success toast, wired here since App.tsx no
          // longer routes to DashboardStub.tsx (Story 3.5), which is now
          // dead/unreachable but whose wording this matches. Code review
          // round 2: epics.md has 3 citations for this string -- UX-DR12
          // (line 157) and Story 3.5's own AC (line 1247) both specify
          // "✓ Skill assigned to {Employee first name} -- {Skill name}",
          // outweighing Story 5.6's own AC (line 1965), a looser paraphrase
          // written while focused on accessibility mechanics, not copy
          // fidelity. User decision: checkmark + first name.
          const firstName = employeeName.split(' ')[0];
          dashboardRef.current?.announceToast(`✓ Skill assigned to ${firstName} — ${skillName}`);
        }}
      />
    </div>
  );
}
