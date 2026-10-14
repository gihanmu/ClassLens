"""Thread-safe durable repository for local development and tenant isolation, backed by SQLite."""

from __future__ import annotations

from services.api.repository.sqlite_repository import (
    SqliteAssessmentRepository,
    UserDoc,
    QuestionConfig,
    AssessmentDoc,
    ResponseDoc,
    AuditEventDoc,
    AnalysisJobDoc,
    utc_now,
    parse_datetime,
)


class MemoryRepository(SqliteAssessmentRepository):
    """Thread-safe durable repository backed by SQLite and cached in-memory."""
    pass


# Singleton instance
memory_repo = MemoryRepository()
