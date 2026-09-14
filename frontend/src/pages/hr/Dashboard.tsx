/** HR Admin Dashboard page (Story 5-1). Left-pane nav shell: Story 7.7. */
import { useState, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import { HrAppShell } from "@/components/layout/HrAppShell";
import { AssignmentModal } from "@/features/assignments/AssignmentModal";
import { DashboardPage, type DashboardPageHandle } from "@/features/dashboard/DashboardPage";

export function Dashboard() {
  const [assignmentModalOpen, setAssignmentModalOpen] = useState(false);
  const dashboardRef = useRef<DashboardPageHandle>(null);
  // Story 9.4: `?assignmentId=` deep-links straight into the Provenance
  // Drill-Down modal -- reached via the Skill Assignment Dashboard's Needs
  // Attention popover (`/dashboard` -> `/hr/dashboard?assignmentId=...`).
  const [searchParams, setSearchParams] = useSearchParams();
  const initialAssignmentId = searchParams.get("assignmentId");

  return (
    <HrAppShell>
      {/* Main content */}
      <main className="px-6 pb-12">
        <DashboardPage
          ref={dashboardRef}
          onNewAssignment={() => setAssignmentModalOpen(true)}
          initialAssignmentId={initialAssignmentId}
          onInitialAssignmentConsumed={() => {
            if (!searchParams.has("assignmentId")) return;
            const next = new URLSearchParams(searchParams);
            next.delete("assignmentId");
            setSearchParams(next, { replace: true });
          }}
        />
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
    </HrAppShell>
  );
}
