import type { SkillWithContent } from '@/lib/api/skillsApi';
import { estimateDaysToComplete } from '@/lib/utils/duration';

export interface SkillCardViewContent {
  title: string;
  source: 'YOUTUBE' | 'UDEMY' | 'MANUAL';
  url: string;
  durationHours: number | null;
}

export interface SkillCardProps {
  skill: SkillWithContent;
  onEdit: (skill: SkillWithContent) => void;
  onDelete: (skill: SkillWithContent) => void;
  onView: (content: SkillCardViewContent) => void;
}

/**
 * One Skills Card Grid card (Story 6.10 AC1, UX-DR25/26). Exactly one
 * approved link if any exists -- already enforced server-side (the API
 * returns at most one `approved_content`), this component just renders
 * whatever it's given. Locked (ever_assigned) Skills show only the 🔒 text
 * indicator, never Edit/Delete or any lookup entry point (AC10, UX-DR33 --
 * PRD Open Question 17 stays an intentional gap).
 */
export function SkillCard({ skill, onEdit, onDelete, onView }: SkillCardProps) {
  const content = skill.approved_content;
  const days = content ? estimateDaysToComplete(content.metadata?.duration_hours as number | undefined ?? null) : null;

  return (
    <div
      className="flex flex-col rounded-lg bg-white p-4 shadow-sm"
      data-testid="skills-tab-skill-card"
    >
      <div className="mb-1 flex items-start justify-between gap-2">
        <h2 className="text-sm font-semibold leading-snug text-gray-900">{skill.name}</h2>
        {content ? (
          <span className="shrink-0 rounded-full bg-green-50 px-2 py-0.5 text-xs font-medium text-green-700">
            ✓ Approved
          </span>
        ) : (
          <span className="shrink-0 rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700">
            ⚠ None yet
          </span>
        )}
      </div>

      <div className="mb-2 flex items-center gap-3">
        {skill.ever_assigned ? (
          <span
            className="inline-flex items-center gap-1 text-xs text-gray-400"
            data-testid="skills-tab-skill-card-lock"
          >
            🔒 Locked — assigned to an Employee
          </span>
        ) : (
          <>
            <button
              type="button"
              aria-label="Edit"
              className="text-xs text-gray-500 hover:text-blue-600"
              onClick={() => onEdit(skill)}
              data-testid="skills-tab-btn-edit-skill"
            >
              ✎ Edit
            </button>
            <button
              type="button"
              aria-label="Delete"
              className="text-xs text-gray-500 hover:text-red-600"
              onClick={() => onDelete(skill)}
              data-testid="skills-tab-btn-delete-skill"
            >
              🗑 Delete
            </button>
          </>
        )}
      </div>

      {content ? (
        <div className="mb-3 flex flex-1 items-center gap-2 text-xs" data-testid="skills-tab-skill-card-link-row">
          <span className="w-14 shrink-0 font-semibold uppercase text-gray-400">{content.source}</span>
          <button
            type="button"
            className="min-w-0 flex-1 truncate text-left text-blue-600 hover:underline"
            onClick={() =>
              onView({
                title: content.title,
                source: content.source,
                url: content.url,
                durationHours: (content.metadata?.duration_hours as number | undefined) ?? null,
              })
            }
            data-testid="skills-tab-skill-card-link"
          >
            {content.title}
          </button>
          {days != null && <span className="shrink-0 text-gray-400">≈{days}d</span>}
        </div>
      ) : (
        <p className="mb-3 flex-1 text-xs text-gray-400">No approved content yet for this skill.</p>
      )}
    </div>
  );
}
