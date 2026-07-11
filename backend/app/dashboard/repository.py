"""Repository layer for the dashboard module (read-composition, no table ownership)."""
# Dashboard is a read-composition module that relies on assignments/ and progress/
# repositories. No direct database access needed here; all reads go through service APIs.
