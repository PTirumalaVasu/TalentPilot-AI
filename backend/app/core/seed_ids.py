"""Canonical seed UUIDs for the 5 demo accounts (Rita, Casey, Morgan, Jordan,
Sam). Shared between `core/seeds.py` (real Employee/Account rows) and
`auth/repository.py`'s mock credential store, so a login's JWT `user_id`
always matches a real `Employee.id` — code that treats `user_id` as a UUID
(e.g. `assignments/service.py`) depends on this holding.

Kept dependency-free (no `sentence_transformers`/`torch`) so importing it
doesn't pull heavy ML deps into the auth request path."""
import uuid

RITA_ID = uuid.UUID("550e8400-e29b-41d4-a716-446655440001")
CASEY_ID = uuid.UUID("550e8400-e29b-41d4-a716-446655440002")
MORGAN_ID = uuid.UUID("550e8400-e29b-41d4-a716-446655440003")
JORDAN_ID = uuid.UUID("550e8400-e29b-41d4-a716-446655440004")
SAM_ID = uuid.UUID("550e8400-e29b-41d4-a716-446655440005")
