from enum import StrEnum


class SourceType(StrEnum):
    ARTICLE = "article"
    GITHUB = "github"
    VIDEO = "video"
    PDF = "pdf"
    TEXT = "text"
    RSS = "rss"


class ContentCategory(StrEnum):
    PROGRAMMING = "programming"
    TECHNOLOGY = "technology"
    SECURITY = "security"
    DAILY_LIFE = "daily_life"
    CAREER = "career"
    TOOLS = "tools"
    CREATION = "creation"
    HEALTH = "health"
    FINANCE = "finance"
    TRAVEL = "travel"
    LEARNING = "learning"
    HOBBY = "hobby"
    PRODUCTIVITY = "productivity"
    OTHER = "other"


DEFAULT_ENABLED_CATEGORIES = [category.value for category in ContentCategory]


class PushChannel(StrEnum):
    IN_APP = "in_app"
    EMAIL = "email"
    DINGTALK = "dingtalk"


class RecommendationStatus(StrEnum):
    PENDING = "pending"
    SAVED = "saved"
    IGNORED = "ignored"
    DISLIKED = "disliked"


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class AgentRunStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    RUNNING = "running"
