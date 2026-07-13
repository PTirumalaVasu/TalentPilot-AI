import { Card } from '@/components/ui/card';
import type { AssignmentContentItem } from '@/types/assignments';
import { formatDurationMinutes, parseIso8601DurationSeconds } from '@/lib/utils/duration';

interface AssignmentCardProps {
  item: AssignmentContentItem;
  onSelect: (item: AssignmentContentItem) => void;
}

function StatusBadge({ status }: { status: AssignmentContentItem['status'] }) {
  const config = {
    NOT_STARTED: { icon: '⊕', label: 'To Start', className: 'bg-gray-100 text-gray-800' },
    IN_PROGRESS: { icon: '⟳', label: 'In Progress', className: 'bg-blue-100 text-blue-800' },
    COMPLETED: { icon: '✓', label: 'Completed', className: 'bg-green-100 text-green-800' },
  }[status];

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ${config.className}`}
    >
      <span aria-hidden="true">{config.icon}</span>
      {config.label}
    </span>
  );
}

export function AssignmentCard({ item, onSelect }: AssignmentCardProps) {
  const durationSeconds = item.content?.metadata
    ? parseIso8601DurationSeconds(item.content.metadata.duration)
    : null;
  const durationLabel = formatDurationMinutes(durationSeconds);
  // Sourced from the backend (derive_dashboard_status_and_percent) rather
  // than recomputed here -- this used to independently round watch_position
  // / durationSeconds, which could disagree with the backend's own COMPLETED
  // decision (e.g. 3603/3606s rounds to "100% watched" here while the
  // backend's stricter watch_position >= duration check still said
  // IN_PROGRESS). One derivation authority now for both status and percent.
  const percentWatched = item.status_percentage;

  function handleActivate() {
    if (item.content) onSelect(item);
  }

  return (
    <Card
      role="button"
      tabIndex={0}
      aria-label={`${item.skill_name}, ${item.status === 'NOT_STARTED' ? 'to start' : item.status === 'IN_PROGRESS' ? 'in progress' : 'completed'}`}
      className="flex flex-col gap-2 p-5 cursor-pointer hover:shadow-md hover:border-talentpilot-400 transition-all"
      onClick={handleActivate}
      onKeyDown={(e) => {
        // Only handle Enter/Space when the Card itself is the event target,
        // not a nested interactive element (e.g. the "Contact Rita" link) --
        // otherwise this handler's preventDefault() suppresses the nested
        // element's own default keyboard action (AC10: keyboard operability).
        if (e.target !== e.currentTarget) return;
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleActivate();
        }
      }}
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-semibold text-gray-900">{item.skill_name}</h3>
        <StatusBadge status={item.status} />
      </div>

      {item.content ? (
        <>
          {item.content.metadata?.thumbnail_url ? (
            <img
              src={String(item.content.metadata.thumbnail_url)}
              alt={`${item.content.title}${durationLabel ? ` - ${durationLabel}` : ''}`}
              className="w-full h-24 object-cover rounded-md"
            />
          ) : (
            <div
              role="img"
              aria-label={`${item.content.title}${durationLabel ? ` - ${durationLabel}` : ''}`}
              className="w-full h-24 bg-gray-100 rounded-md flex items-center justify-center text-gray-400 text-xs"
            >
              No preview available
            </div>
          )}
          <p className="text-sm text-gray-600">{item.content.title}</p>
          <div className="flex items-center gap-2 text-xs text-gray-500 flex-wrap">
            <span className="font-medium">{item.content.source}</span>
            {durationLabel && (
              <>
                <span>·</span>
                <span>{durationLabel}</span>
              </>
            )}
          </div>
          {item.content.description && (
            <p className="text-xs text-gray-500 line-clamp-2">{item.content.description}</p>
          )}
          <div className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 w-fit">
            ✓ Approved
          </div>
          {item.status === 'COMPLETED' ? (
            <div className="pt-2 border-t border-gray-100">
              <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                <div className="h-full bg-green-500" style={{ width: '100%' }} />
              </div>
              <p className="text-xs text-gray-600 font-medium mt-1">100% watched</p>
            </div>
          ) : item.watch_position > 0 && percentWatched !== null ? (
            <div className="pt-2 border-t border-gray-100">
              <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                {/* A real but small percentage (e.g. 1%) renders as a few px --
                    functionally invisible against the bar's rounded corners.
                    Floor the visible width at 4% so any nonzero progress reads
                    as a genuine, perceptible sliver rather than an empty bar. */}
                <div className="h-full bg-blue-500" style={{ width: `${Math.max(percentWatched, 4)}%` }} />
              </div>
              <p className="text-xs text-gray-600 font-medium mt-1">{percentWatched}% watched</p>
            </div>
          ) : (
            <p className="text-xs text-gray-500 pt-2 border-t border-gray-100">Not started yet</p>
          )}
        </>
      ) : (
        <div className="text-sm text-gray-500">
          No recommended content yet for this skill.{' '}
          <a href="mailto:rita@sails.example.com" className="text-talentpilot-600 underline" onClick={(e) => e.stopPropagation()}>
            Contact Rita
          </a>
        </div>
      )}
    </Card>
  );
}
