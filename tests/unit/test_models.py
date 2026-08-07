from skill_analytics.models import JobPosting, JobPostingSkill


def test_composite_indexes_are_declared() -> None:
    posting_indexes = {index.name for index in JobPosting.__table__.indexes}
    bridge_indexes = {index.name for index in JobPostingSkill.__table__.indexes}
    assert "ix_job_postings_composite_key_posted" in posting_indexes
    assert "ix_job_postings_filters" in posting_indexes
    assert "ix_job_posting_skills_skill_posting" in bridge_indexes
