/**
 * TypeScript types for Content Discovery (Story 2.5).
 * Mirror backend/app/assignments/schemas.py's AssignmentContentItem /
 * MyAssignmentsResponse exactly.
 */

export interface ContentItem {
  id: string;
  skill_id: string;
  title: string;
  description: string | null;
  type: 'VIDEO' | 'DOCUMENT' | 'WEBSITE';
  url: string;
  source: 'YOUTUBE' | 'MANUAL';
  ingested_at: string;
  metadata: Record<string, unknown> | null;
}

export type AssignmentStatus = 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED';
export type AssignmentGroup = 'TO_START' | 'IN_PROGRESS';

export interface AssignmentContentItem {
  assignment_id: string;
  skill_id: string;
  skill_name: string;
  content: ContentItem | null;
  watch_position: number;
  status: AssignmentStatus;
  group: AssignmentGroup;
}

export interface MyAssignmentsResponse {
  total: number;
  in_progress_count: number;
  to_start_count: number;
  assignments: AssignmentContentItem[];
}
