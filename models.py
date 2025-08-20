"""
Pydantic models for the Helpdesk Knowledge Base system.
Provides data validation, serialization, and type safety for all system components.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator, root_validator
import re
import uuid


class DifficultyLevel(str, Enum):
    """Difficulty levels for helpdesk articles."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionType(str, Enum):
    """Types of diagnostic questions."""
    YES_NO = "yes_no"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT_INPUT = "text_input"
    NUMERIC = "numeric"
    SCALE = "scale"


class SolutionStepType(str, Enum):
    """Types of solution steps."""
    INSTRUCTION = "instruction"
    VERIFICATION = "verification"
    TROUBLESHOOTING = "troubleshooting"
    WARNING = "warning"
    NOTE = "note"


class MessageType(str, Enum):
    """Types of chat messages."""
    USER_QUERY = "user_query"
    BOT_RESPONSE = "bot_response"
    SYSTEM_MESSAGE = "system_message"
    ERROR_MESSAGE = "error_message"


class SolutionStep(BaseModel):
    """Model for individual solution steps within an article."""
    
    order: int = Field(..., ge=1, le=100, description="Step order number")
    title: str = Field(..., min_length=1, max_length=200, description="Step title")
    content: str = Field(..., min_length=1, max_length=2000, description="Step content")
    step_type: SolutionStepType = Field(default=SolutionStepType.INSTRUCTION, description="Type of step")
    condition: Optional[str] = Field(None, max_length=500, description="Condition for this step")
    estimated_time_minutes: Optional[int] = Field(None, ge=1, le=60, description="Estimated time for this step")
    
    @validator('title')
    def validate_title(cls, v):
        """Validate step title format."""
        if not v.strip():
            raise ValueError("Step title cannot be empty")
        return v.strip()
    
    @validator('content')
    def validate_content(cls, v):
        """Validate step content."""
        if not v.strip():
            raise ValueError("Step content cannot be empty")
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "order": 1,
                "title": "Check Physical Connections",
                "content": "Ensure the printer is powered on and properly connected to your computer or network",
                "step_type": "instruction",
                "condition": None,
                "estimated_time_minutes": 2
            }
        }


class DiagnosticQuestion(BaseModel):
    """Model for diagnostic questions to help users troubleshoot issues."""
    
    question: str = Field(..., min_length=1, max_length=500, description="Question text")
    question_type: QuestionType = Field(..., description="Type of question")
    options: Optional[List[str]] = Field(None, description="Available options for multiple choice questions")
    required: bool = Field(default=True, description="Whether this question is required")
    help_text: Optional[str] = Field(None, max_length=1000, description="Help text for the question")
    expected_answer: Optional[Union[str, int, bool]] = Field(None, description="Expected answer for validation")
    follow_up_questions: Optional[List[str]] = Field(None, description="IDs of follow-up questions")
    
    @validator('question')
    def validate_question(cls, v):
        """Validate question text."""
        if not v.strip():
            raise ValueError("Question text cannot be empty")
        return v.strip()
    
    @validator('options')
    def validate_options(cls, v, values):
        """Validate options for multiple choice questions."""
        if values.get('question_type') == QuestionType.MULTIPLE_CHOICE:
            if not v or len(v) < 2:
                raise ValueError("Multiple choice questions must have at least 2 options")
            if len(v) > 10:
                raise ValueError("Multiple choice questions cannot have more than 10 options")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "question": "Do you have access to your recovery email or phone number?",
                "question_type": "yes_no",
                "options": None,
                "required": True,
                "help_text": "You'll need access to at least one recovery method to reset your password",
                "expected_answer": True,
                "follow_up_questions": None
            }
        }


class KnowledgeArticle(BaseModel):
    """Main model for helpdesk knowledge base articles."""
    
    article_id: Optional[int] = Field(None, ge=1, description="Unique article identifier")
    title: str = Field(..., min_length=1, max_length=200, description="Article title")
    content: str = Field(..., min_length=10, max_length=10000, description="Article content")
    category: str = Field(..., min_length=1, max_length=100, description="Article category")
    subcategory: Optional[str] = Field(None, max_length=100, description="Article subcategory")
    difficulty_level: DifficultyLevel = Field(..., description="Difficulty level")
    keywords: List[str] = Field(default_factory=list, max_items=20, description="Search keywords")
    symptoms: List[str] = Field(default_factory=list, max_items=15, description="Problem symptoms")
    solution_steps: List[SolutionStep] = Field(default_factory=list, max_items=20, description="Solution steps")
    diagnostic_questions: List[DiagnosticQuestion] = Field(default_factory=list, max_items=10, description="Diagnostic questions")
    success_rate: float = Field(0.0, ge=0.0, le=1.0, description="Success rate (0.0 to 1.0)")
    estimated_time_minutes: int = Field(..., ge=1, le=480, description="Estimated resolution time in minutes")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    is_active: bool = Field(default=True, description="Whether the article is active")
    author: Optional[str] = Field(None, max_length=100, description="Article author")
    tags: List[str] = Field(default_factory=list, max_items=10, description="Additional tags")
    version: Optional[str] = Field(None, max_length=20, description="Article version")
    last_reviewed: Optional[datetime] = Field(None, description="Last review timestamp")
    
    @validator('title')
    def validate_title(cls, v):
        """Validate article title."""
        if not v.strip():
            raise ValueError("Article title cannot be empty")
        return v.strip()
    
    @validator('content')
    def validate_content(cls, v):
        """Validate article content."""
        if not v.strip():
            raise ValueError("Article content cannot be empty")
        return v.strip()
    
    @validator('keywords')
    def validate_keywords(cls, v):
        """Validate and clean keywords."""
        cleaned = []
        for keyword in v:
            if keyword and keyword.strip():
                cleaned.append(keyword.strip().lower())
        return list(set(cleaned))  # Remove duplicates
    
    @validator('symptoms')
    def validate_symptoms(cls, v):
        """Validate and clean symptoms."""
        cleaned = []
        for symptom in v:
            if symptom and symptom.strip():
                cleaned.append(symptom.strip())
        return cleaned
    
    @validator('solution_steps')
    def validate_solution_steps(cls, v):
        """Validate solution steps order."""
        if v:
            orders = [step.order for step in v]
            if len(orders) != len(set(orders)):
                raise ValueError("Solution step orders must be unique")
            if orders != sorted(orders):
                raise ValueError("Solution steps must be in ascending order")
        return v
    
    @root_validator
    def validate_article_data(cls, values):
        """Validate article data consistency."""
        if values.get('solution_steps') and not values.get('content'):
            raise ValueError("Articles with solution steps must have content")
        
        if values.get('difficulty_level') == DifficultyLevel.EASY and values.get('estimated_time_minutes', 0) > 30:
            raise ValueError("Easy articles should take 30 minutes or less")
        
        if values.get('difficulty_level') == DifficultyLevel.HARD and values.get('estimated_time_minutes', 0) < 30:
            raise ValueError("Hard articles should take at least 30 minutes")
        
        return values
    
    def generate_slug(self) -> str:
        """Generate a URL-friendly slug from the title."""
        slug = re.sub(r'[^\w\s-]', '', self.title.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    def get_summary(self, max_length: int = 200) -> str:
        """Get a summary of the article content."""
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length].rsplit(' ', 1)[0] + '...'
    
    class Config:
        schema_extra = {
            "example": {
                "article_id": 1,
                "title": "How to Reset Your Email Password",
                "content": "If you've forgotten your email password...",
                "category": "Email",
                "subcategory": "Password Management",
                "difficulty_level": "easy",
                "keywords": ["password reset", "email password"],
                "symptoms": ["Cannot log into email account"],
                "solution_steps": [],
                "diagnostic_questions": [],
                "success_rate": 0.95,
                "estimated_time_minutes": 10,
                "is_active": True
            }
        }


class SearchResult(BaseModel):
    """Model for search result summaries."""
    
    article_id: str = Field(..., description="Article ID")
    title: str = Field(..., description="Article title")
    content_summary: str = Field(..., description="Content summary")
    category: str = Field(..., description="Article category")
    difficulty_level: DifficultyLevel = Field(..., description="Difficulty level")
    score: float = Field(..., description="Search relevance score")
    estimated_time_minutes: int = Field(..., description="Estimated resolution time")
    success_rate: float = Field(..., description="Success rate")
    keywords: List[str] = Field(default_factory=list, description="Relevant keywords")
    symptoms: List[str] = Field(default_factory=list, description="Matching symptoms")
    last_updated: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "article_id": "abc123",
                "title": "How to Reset Your Email Password",
                "content_summary": "Step-by-step guide to reset your email password...",
                "category": "Email",
                "difficulty_level": "easy",
                "score": 0.95,
                "estimated_time_minutes": 10,
                "success_rate": 0.95,
                "keywords": ["password", "reset"],
                "symptoms": ["Cannot log in"],
                "last_updated": "2024-01-01T00:00:00Z"
            }
        }


class ChatMessage(BaseModel):
    """Model for chat messages between users and the helpdesk system."""
    
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique message ID")
    session_id: str = Field(..., description="Chat session identifier")
    message_type: MessageType = Field(..., description="Type of message")
    content: str = Field(..., min_length=1, max_length=2000, description="Message content")
    sender: str = Field(..., description="Message sender (user_id or 'bot')")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional message metadata")
    intent: Optional[str] = Field(None, description="Detected user intent")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Intent confidence score")
    related_articles: Optional[List[str]] = Field(None, description="Related article IDs")
    
    @validator('content')
    def validate_content(cls, v):
        """Validate message content."""
        if not v.strip():
            raise ValueError("Message content cannot be empty")
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "message_id": "msg_123",
                "session_id": "session_456",
                "message_type": "user_query",
                "content": "I can't log into my email",
                "sender": "user_789",
                "timestamp": "2024-01-01T12:00:00Z",
                "intent": "email_login_issue",
                "confidence": 0.85,
                "related_articles": ["article_1", "article_2"]
            }
        }


class SearchQuery(BaseModel):
    """Model for search queries."""
    
    query: str = Field(..., min_length=1, max_length=500, description="Search query text")
    category: Optional[str] = Field(None, description="Filter by category")
    difficulty_level: Optional[DifficultyLevel] = Field(None, description="Filter by difficulty")
    max_time_minutes: Optional[int] = Field(None, ge=1, le=480, description="Maximum time filter")
    min_success_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum success rate")
    include_inactive: bool = Field(default=False, description="Include inactive articles")
    size: int = Field(default=10, ge=1, le=100, description="Number of results")
    from_: int = Field(default=0, ge=0, description="Starting offset")
    sort_by: str = Field(default="relevance", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order")
    
    @validator('query')
    def validate_query(cls, v):
        """Validate search query."""
        if not v.strip():
            raise ValueError("Search query cannot be empty")
        return v.strip()
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        """Validate sort field."""
        valid_fields = ['relevance', 'title', 'created_at', 'updated_at', 'success_rate', 'estimated_time_minutes']
        if v not in valid_fields:
            raise ValueError(f"Invalid sort field. Must be one of: {valid_fields}")
        return v
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        """Validate sort order."""
        if v not in ['asc', 'desc']:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "query": "password reset",
                "category": "Email",
                "difficulty_level": "easy",
                "max_time_minutes": 30,
                "min_success_rate": 0.8,
                "size": 10,
                "from_": 0,
                "sort_by": "relevance",
                "sort_order": "desc"
            }
        }


class ArticleImportResult(BaseModel):
    """Model for article import operation results."""
    
    total_articles: int = Field(..., description="Total articles processed")
    successful_imports: int = Field(..., description="Successfully imported articles")
    failed_imports: int = Field(..., description="Failed imports")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Import errors")
    warnings: List[Dict[str, Any]] = Field(default_factory=list, description="Import warnings")
    processing_time_seconds: float = Field(..., description="Total processing time")
    
    @property
    def success_rate(self) -> float:
        """Calculate import success rate."""
        if self.total_articles == 0:
            return 0.0
        return self.successful_imports / self.total_articles
    
    class Config:
        schema_extra = {
            "example": {
                "total_articles": 100,
                "successful_imports": 95,
                "failed_imports": 5,
                "errors": [],
                "warnings": [],
                "processing_time_seconds": 2.5
            }
        }
