"""
Response Generation System for Helpdesk Chatbot
Provides intelligent response formatting, template management, and conversation handling.
"""

import re
import json
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import textstat
from jinja2 import Template, Environment, FileSystemLoader, select_autoescape

from models import (
    KnowledgeArticle, SolutionStep, DiagnosticQuestion,
    QuestionType, SolutionStepType, DifficultyLevel
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResponseType(str, Enum):
    """Types of responses the system can generate."""
    ARTICLE_FULL = "article_full"
    STEP_BY_STEP = "step_by_step"
    DIAGNOSTIC = "diagnostic"
    NO_RESULTS = "no_results"
    ESCALATION = "escalation"
    CLARIFICATION = "clarification"
    CONFIRMATION = "confirmation"
    GREETING = "greeting"
    FAREWELL = "farewell"


class TechnicalLevel(str, Enum):
    """Technical level of the user."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


class ConversationState(str, Enum):
    """Current state of the conversation."""
    INITIAL = "initial"
    GATHERING_INFO = "gathering_info"
    PRESENTING_SOLUTION = "presenting_solution"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    COMPLETED = "completed"
    ESCALATED = "escalated"


@dataclass
class ResponseContext:
    """Context information for generating responses."""
    user_name: Optional[str] = None
    technical_level: TechnicalLevel = TechnicalLevel.INTERMEDIATE
    software_version: Optional[str] = None
    operating_system: Optional[str] = None
    previous_issues: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    current_emotion: Optional[str] = None  # frustrated, confused, satisfied, etc.
    response_count: int = 0
    session_start: datetime = field(default_factory=datetime.now)


@dataclass
class ConversationTurn:
    """Represents a single turn in the conversation."""
    timestamp: datetime
    speaker: str  # "user" or "bot"
    message: str
    intent: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None
    response_type: Optional[ResponseType] = None
    article_id: Optional[str] = None
    step_index: Optional[int] = None
    question_id: Optional[str] = None


class BaseResponseFormatter(ABC):
    """Abstract base class for response formatters."""
    
    def __init__(self, template_engine: Optional['TemplateEngine'] = None):
        """Initialize the response formatter."""
        self.template_engine = template_engine or TemplateEngine()
        self.response_variations = self._load_response_variations()
    
    @abstractmethod
    def format_response(self, data: Any, context: ResponseContext) -> str:
        """Format the response based on data and context."""
        pass
    
    def _load_response_variations(self) -> Dict[str, List[str]]:
        """Load response variations to avoid repetition."""
        return {
            'greeting': [
                "Hello {user_name}! How can I help you today?",
                "Hi {user_name}! What can I assist you with?",
                "Welcome {user_name}! I'm here to help with your technical issues.",
                "Good to see you {user_name}! What seems to be the problem?"
            ],
            'acknowledgment': [
                "I understand you're having trouble with {issue}.",
                "I see you're experiencing issues with {issue}.",
                "Thank you for explaining the problem with {issue}.",
                "I've noted that you're facing {issue}."
            ],
            'solution_intro': [
                "I found a solution that should help:",
                "Here's what you can try to resolve this:",
                "Let me guide you through the solution:",
                "I have a solution that has worked for similar issues:"
            ],
            'step_completion': [
                "Great! Let's move to the next step.",
                "Excellent! Here's what to do next.",
                "Perfect! Now for the next part.",
                "Well done! Let's continue."
            ],
            'clarification': [
                "Could you provide more details about {topic}?",
                "I need a bit more information about {topic}.",
                "Can you elaborate on {topic}?",
                "Please tell me more about {topic}."
            ]
        }
    
    def get_random_variation(self, variation_type: str, **kwargs) -> str:
        """Get a random variation of a response type."""
        variations = self.response_variations.get(variation_type, [""])
        template = random.choice(variations)
        return template.format(**kwargs)
    
    def adjust_technical_level(self, content: str, level: TechnicalLevel) -> str:
        """Adjust the technical level of the content."""
        if level == TechnicalLevel.BEGINNER:
            # Simplify technical terms
            content = re.sub(r'\b(configure|configuration)\b', 'set up', content, flags=re.IGNORECASE)
            content = re.sub(r'\b(execute|execution)\b', 'run', content, flags=re.IGNORECASE)
            content = re.sub(r'\b(terminate|termination)\b', 'stop', content, flags=re.IGNORECASE)
            content = re.sub(r'\b(initialize|initialization)\b', 'start', content, flags=re.IGNORECASE)
        elif level == TechnicalLevel.EXPERT:
            # Add technical details (in practice, would be more sophisticated)
            content = content.replace('restart', 'restart (systemctl restart or service restart)')
            content = content.replace('check the logs', 'check the logs (/var/log/ or Event Viewer)')
        
        return content


class ArticleResponseFormatter(BaseResponseFormatter):
    """Formats full article responses."""
    
    def format_response(self, article: KnowledgeArticle, context: ResponseContext) -> str:
        """Format a full article response."""
        # Adjust content for technical level
        content = self.adjust_technical_level(article.content, context.technical_level)
        
        # Build the response
        response_parts = []
        
        # Add greeting if it's the first response
        if context.response_count == 0 and context.user_name:
            response_parts.append(self.get_random_variation('greeting', user_name=context.user_name))
        
        # Add acknowledgment
        response_parts.append(self.get_random_variation('acknowledgment', issue=article.title))
        
        # Add solution introduction
        response_parts.append(self.get_random_variation('solution_intro'))
        
        # Add article content
        response_parts.append(f"\n**{article.title}**\n")
        response_parts.append(content)
        
        # Add solution steps if available
        if article.solution_steps:
            response_parts.append("\n**Steps to resolve:**")
            for step in sorted(article.solution_steps, key=lambda x: x.order):
                step_content = self.adjust_technical_level(step.content, context.technical_level)
                response_parts.append(f"\n{step.order}. **{step.title}**")
                response_parts.append(f"   {step_content}")
                if step.estimated_time_minutes:
                    response_parts.append(f"   ⏱️ Estimated time: {step.estimated_time_minutes} minutes")
        
        # Add estimated total time
        if article.estimated_time_minutes:
            response_parts.append(f"\n**Total estimated time:** {article.estimated_time_minutes} minutes")
        
        # Add success rate if available
        if article.success_rate:
            response_parts.append(f"\n**Success rate:** {article.success_rate:.0%}")
        
        # Add follow-up question
        response_parts.append("\nDoes this help resolve your issue?")
        
        return "\n".join(response_parts)


class StepByStepResponseFormatter(BaseResponseFormatter):
    """Formats progressive step-by-step responses."""
    
    def format_response(self, 
                       step: SolutionStep, 
                       context: ResponseContext,
                       is_first_step: bool = False,
                       is_last_step: bool = False,
                       total_steps: int = 1) -> str:
        """Format a single step response."""
        response_parts = []
        
        # Add introduction for first step
        if is_first_step:
            response_parts.append(self.get_random_variation('solution_intro'))
            response_parts.append(f"I'll guide you through {total_steps} steps to resolve this issue.\n")
        
        # Format the step
        step_content = self.adjust_technical_level(step.content, context.technical_level)
        
        response_parts.append(f"**Step {step.order} of {total_steps}: {step.title}**")
        response_parts.append(step_content)
        
        # Add warnings or notes
        if step.step_type == SolutionStepType.WARNING:
            response_parts.append("\n⚠️ **Warning:** Please be careful with this step.")
        elif step.step_type == SolutionStepType.NOTE:
            response_parts.append("\n📝 **Note:** This information is important for the next steps.")
        
        # Add time estimate
        if step.estimated_time_minutes:
            response_parts.append(f"\n⏱️ This step should take about {step.estimated_time_minutes} minute(s).")
        
        # Add completion prompt
        if not is_last_step:
            response_parts.append("\n✅ Let me know when you've completed this step, and I'll guide you to the next one.")
        else:
            response_parts.append("\n🎉 This is the final step! Let me know if this resolves your issue.")
        
        return "\n".join(response_parts)


class QuestionResponseFormatter(BaseResponseFormatter):
    """Formats diagnostic question responses."""
    
    def format_response(self, 
                       question: DiagnosticQuestion,
                       context: ResponseContext,
                       question_number: int = 1,
                       total_questions: int = 1) -> str:
        """Format a diagnostic question."""
        response_parts = []
        
        # Add introduction if first question
        if question_number == 1:
            response_parts.append("I need to ask you a few questions to better understand the issue.")
            response_parts.append(f"This will help me provide the most accurate solution.\n")
        
        # Format the question
        response_parts.append(f"**Question {question_number} of {total_questions}:**")
        response_parts.append(question.question)
        
        # Add help text if available
        if question.help_text:
            help_text = self.adjust_technical_level(question.help_text, context.technical_level)
            response_parts.append(f"\n💡 *{help_text}*")
        
        # Add options for multiple choice
        if question.question_type == QuestionType.MULTIPLE_CHOICE and question.options:
            response_parts.append("\nPlease choose from:")
            for i, option in enumerate(question.options, 1):
                response_parts.append(f"{i}. {option}")
        elif question.question_type == QuestionType.YES_NO:
            response_parts.append("\nPlease answer: Yes or No")
        elif question.question_type == QuestionType.NUMERIC:
            response_parts.append("\nPlease provide a number.")
        elif question.question_type == QuestionType.SCALE:
            response_parts.append("\nPlease rate on a scale of 1-10.")
        
        return "\n".join(response_parts)


class NoResultsResponseFormatter(BaseResponseFormatter):
    """Formats responses when no matching articles are found."""
    
    def format_response(self, 
                       query: str,
                       context: ResponseContext,
                       suggestions: Optional[List[str]] = None) -> str:
        """Format a no results response with helpful alternatives."""
        response_parts = []
        
        # Acknowledge the query
        response_parts.append(f"I couldn't find an exact match for '{query}' in our knowledge base.")
        
        # Provide suggestions if available
        if suggestions:
            response_parts.append("\nHowever, here are some related topics that might help:")
            for i, suggestion in enumerate(suggestions[:5], 1):
                response_parts.append(f"{i}. {suggestion}")
        
        # Offer alternative actions
        response_parts.append("\nHere's what you can try:")
        response_parts.append("1. 🔍 **Rephrase your question** - Try using different keywords")
        response_parts.append("2. 📚 **Browse categories** - I can show you available categories")
        response_parts.append("3. 🎯 **Be more specific** - Include error messages or software names")
        response_parts.append("4. 💬 **Talk to a human** - I can escalate this to our support team")
        
        # Add a helpful prompt
        response_parts.append("\nWould you like to try a different search or speak with a support agent?")
        
        return "\n".join(response_parts)


class EscalationResponseFormatter(BaseResponseFormatter):
    """Formats escalation responses when transferring to human support."""
    
    def format_response(self,
                       reason: str,
                       context: ResponseContext,
                       ticket_number: Optional[str] = None,
                       wait_time: Optional[int] = None) -> str:
        """Format an escalation response."""
        response_parts = []
        
        # Acknowledge the need for escalation
        response_parts.append("I understand this issue requires specialized assistance.")
        
        # Explain the reason
        if reason == "complex_issue":
            response_parts.append("This appears to be a complex technical issue that would be better handled by our expert support team.")
        elif reason == "user_request":
            response_parts.append("As requested, I'll connect you with a human support agent.")
        elif reason == "repeated_failure":
            response_parts.append("Since the suggested solutions haven't resolved your issue, let me get you additional help.")
        elif reason == "emotional_distress":
            response_parts.append("I can see this is frustrating. Let me connect you with someone who can provide more personalized assistance.")
        
        # Provide ticket information
        if ticket_number:
            response_parts.append(f"\n📋 **Support Ticket:** #{ticket_number}")
            response_parts.append("Please reference this number when speaking with the agent.")
        
        # Add wait time if available
        if wait_time:
            response_parts.append(f"\n⏰ **Estimated wait time:** {wait_time} minutes")
        
        # Collect summary information
        response_parts.append("\n**Information I'm passing to the agent:**")
        response_parts.append(f"• Issue summary: {context.preferences.get('issue_summary', 'Technical support needed')}")
        response_parts.append(f"• Technical level: {context.technical_level.value}")
        if context.software_version:
            response_parts.append(f"• Software version: {context.software_version}")
        if context.operating_system:
            response_parts.append(f"• Operating system: {context.operating_system}")
        
        # Add connection instructions
        response_parts.append("\n**Next steps:**")
        response_parts.append("1. An agent will join this conversation shortly")
        response_parts.append("2. They have access to our conversation history")
        response_parts.append("3. Feel free to provide any additional details")
        
        # Add a polite closing
        response_parts.append("\nThank you for your patience. An agent will be with you soon!")
        
        return "\n".join(response_parts)


class TemplateEngine:
    """Manages dynamic templates for response generation."""
    
    def __init__(self, template_dir: Optional[str] = None):
        """Initialize the template engine."""
        self.template_dir = template_dir or "templates"
        self.templates = self._load_templates()
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir) if template_dir else None,
            autoescape=select_autoescape(['html', 'xml'])
        )
    
    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        """Load response templates organized by category and type."""
        return {
            'email': {
                'password_reset': """
Hi {user_name},

I'll help you reset your email password. {acknowledgment}

**Solution for {software_version}:**
{solution_content}

{additional_notes}

This typically takes {time_estimate} minutes.
{closing}
                """,
                'connection_issues': """
{greeting}

I see you're having trouble connecting to your email. {acknowledgment}

**Troubleshooting steps:**
{solution_steps}

{diagnostic_questions}

{closing}
                """
            },
            'hardware': {
                'printer': """
{greeting}

Let's troubleshoot your printer issue. {acknowledgment}

**{printer_model} Troubleshooting:**
{solution_content}

{verification_steps}

{closing}
                """,
                'network': """
{greeting}

I'll help you resolve the network connectivity issue. {acknowledgment}

**Network Diagnostics:**
{diagnostic_steps}

**Solution:**
{solution_content}

{closing}
                """
            },
            'software': {
                'installation': """
{greeting}

I'll guide you through the {software_name} installation. {acknowledgment}

**Installation Steps:**
{installation_steps}

**Post-installation:**
{verification_steps}

{closing}
                """,
                'update': """
{greeting}

Let's update {software_name} to the latest version. {acknowledgment}

**Update Process:**
{update_steps}

**Important Notes:**
{important_notes}

{closing}
                """
            }
        }
    
    def render_template(self, 
                       category: str,
                       template_type: str,
                       variables: Dict[str, Any],
                       context: ResponseContext) -> str:
        """Render a template with the given variables and context."""
        # Get the appropriate template
        template_str = self.templates.get(category, {}).get(template_type)
        
        if not template_str:
            # Fallback to a generic template
            template_str = """
{greeting}

{acknowledgment}

{solution_content}

{closing}
            """
        
        # Prepare variables
        template_vars = {
            'user_name': context.user_name or 'there',
            'greeting': f"Hello {context.user_name or 'there'}",
            'acknowledgment': "I understand your concern.",
            'closing': "Let me know if you need further assistance!",
            'software_version': context.software_version or 'your version',
            'time_estimate': '10-15',
            **variables
        }
        
        # Render the template
        template = Template(template_str)
        return template.render(**template_vars).strip()
    
    def add_conditional_content(self,
                               base_content: str,
                               conditions: Dict[str, bool],
                               conditional_content: Dict[str, str]) -> str:
        """Add conditional content based on user responses or context."""
        result = base_content
        
        for condition_key, is_true in conditions.items():
            if is_true and condition_key in conditional_content:
                result += f"\n\n{conditional_content[condition_key]}"
        
        return result


class SolutionStepManager:
    """Manages the presentation and tracking of solution steps."""
    
    def __init__(self):
        """Initialize the solution step manager."""
        self.active_solutions: Dict[str, 'SolutionProgress'] = {}
        self.formatter = StepByStepResponseFormatter()
    
    def start_solution(self,
                      session_id: str,
                      article: KnowledgeArticle,
                      mode: str = "progressive") -> str:
        """Start a new solution process."""
        if not article.solution_steps:
            return "No solution steps available for this article."
        
        # Create solution progress tracker
        progress = SolutionProgress(
            article_id=article.article_id,
            steps=sorted(article.solution_steps, key=lambda x: x.order),
            mode=mode,
            started_at=datetime.now()
        )
        
        self.active_solutions[session_id] = progress
        
        if mode == "all_at_once":
            return self._format_all_steps(progress)
        else:
            return self._get_next_step(session_id)
    
    def _format_all_steps(self, progress: 'SolutionProgress') -> str:
        """Format all steps at once."""
        response_parts = ["Here are all the steps to resolve your issue:\n"]
        
        for i, step in enumerate(progress.steps):
            response_parts.append(f"**Step {step.order}: {step.title}**")
            response_parts.append(step.content)
            if step.estimated_time_minutes:
                response_parts.append(f"⏱️ Time: {step.estimated_time_minutes} minutes")
            response_parts.append("")
        
        total_time = sum(s.estimated_time_minutes or 0 for s in progress.steps)
        if total_time:
            response_parts.append(f"**Total estimated time:** {total_time} minutes")
        
        return "\n".join(response_parts)
    
    def _get_next_step(self, session_id: str) -> str:
        """Get the next step in the solution."""
        progress = self.active_solutions.get(session_id)
        if not progress:
            return "No active solution found. Please start over."
        
        if progress.current_step_index >= len(progress.steps):
            return self._complete_solution(session_id)
        
        step = progress.steps[progress.current_step_index]
        context = ResponseContext()  # In practice, would get actual context
        
        return self.formatter.format_response(
            step=step,
            context=context,
            is_first_step=(progress.current_step_index == 0),
            is_last_step=(progress.current_step_index == len(progress.steps) - 1),
            total_steps=len(progress.steps)
        )
    
    def confirm_step_completion(self,
                               session_id: str,
                               success: bool,
                               user_feedback: Optional[str] = None) -> str:
        """Confirm completion of the current step."""
        progress = self.active_solutions.get(session_id)
        if not progress:
            return "No active solution found."
        
        current_step = progress.steps[progress.current_step_index]
        progress.step_outcomes[current_step.order] = {
            'success': success,
            'feedback': user_feedback,
            'completed_at': datetime.now()
        }
        
        if not success:
            # Handle step failure
            return self._handle_step_failure(session_id, current_step, user_feedback)
        
        # Move to next step
        progress.current_step_index += 1
        progress.completed_steps.append(current_step.order)
        
        return self._get_next_step(session_id)
    
    def _handle_step_failure(self,
                            session_id: str,
                            step: SolutionStep,
                            feedback: Optional[str]) -> str:
        """Handle when a step fails."""
        response_parts = ["I see that step didn't work as expected."]
        
        # Provide alternative actions
        if step.step_type == SolutionStepType.TROUBLESHOOTING:
            response_parts.append("\nLet's try an alternative approach:")
            response_parts.append("• Double-check the previous steps")
            response_parts.append("• Try restarting the application")
            response_parts.append("• Check for any error messages")
        
        response_parts.append("\nWould you like to:")
        response_parts.append("1. Try this step again")
        response_parts.append("2. Skip to the next step")
        response_parts.append("3. Get help from a human agent")
        
        return "\n".join(response_parts)
    
    def _complete_solution(self, session_id: str) -> str:
        """Complete the solution process."""
        progress = self.active_solutions.get(session_id)
        if not progress:
            return "No active solution found."
        
        progress.completed_at = datetime.now()
        duration = (progress.completed_at - progress.started_at).seconds // 60
        
        response_parts = ["🎉 **Solution Complete!**\n"]
        response_parts.append(f"You've completed all {len(progress.steps)} steps.")
        response_parts.append(f"Total time: {duration} minutes")
        
        # Calculate success rate
        successful_steps = sum(1 for outcome in progress.step_outcomes.values() if outcome['success'])
        success_rate = (successful_steps / len(progress.steps)) * 100 if progress.steps else 0
        response_parts.append(f"Success rate: {success_rate:.0f}%")
        
        response_parts.append("\nDid this resolve your issue?")
        
        # Clean up
        del self.active_solutions[session_id]
        
        return "\n".join(response_parts)
    
    def get_progress(self, session_id: str) -> Optional['SolutionProgress']:
        """Get the current solution progress."""
        return self.active_solutions.get(session_id)


@dataclass
class SolutionProgress:
    """Tracks progress through solution steps."""
    article_id: str
    steps: List[SolutionStep]
    mode: str  # "progressive" or "all_at_once"
    started_at: datetime
    current_step_index: int = 0
    completed_steps: List[int] = field(default_factory=list)
    step_outcomes: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    completed_at: Optional[datetime] = None


class DiagnosticQuestionHandler:
    """Handles diagnostic questions and routing based on answers."""
    
    def __init__(self):
        """Initialize the diagnostic question handler."""
        self.active_diagnostics: Dict[str, 'DiagnosticSession'] = {}
        self.formatter = QuestionResponseFormatter()
        self.routing_rules = self._load_routing_rules()
    
    def _load_routing_rules(self) -> Dict[str, Any]:
        """Load routing rules for diagnostic answers."""
        return {
            'network_connectivity': {
                'can_access_internet': {
                    'yes': 'check_specific_service',
                    'no': 'check_network_hardware'
                },
                'lights_on_router': {
                    'yes': 'check_wifi_settings',
                    'no': 'power_cycle_router'
                }
            },
            'printer_issues': {
                'printer_powered_on': {
                    'yes': 'check_connection_type',
                    'no': 'check_power_cable'
                },
                'error_message_displayed': {
                    'yes': 'identify_error_code',
                    'no': 'run_printer_diagnostics'
                }
            }
        }
    
    def start_diagnostic(self,
                        session_id: str,
                        questions: List[DiagnosticQuestion],
                        category: str) -> str:
        """Start a diagnostic question session."""
        if not questions:
            return "No diagnostic questions available."
        
        session = DiagnosticSession(
            category=category,
            questions=questions,
            started_at=datetime.now()
        )
        
        self.active_diagnostics[session_id] = session
        return self._get_next_question(session_id)
    
    def _get_next_question(self, session_id: str) -> str:
        """Get the next diagnostic question."""
        session = self.active_diagnostics.get(session_id)
        if not session:
            return "No active diagnostic session found."
        
        if session.current_question_index >= len(session.questions):
            return self._complete_diagnostic(session_id)
        
        question = session.questions[session.current_question_index]
        context = ResponseContext()  # In practice, would get actual context
        
        return self.formatter.format_response(
            question=question,
            context=context,
            question_number=session.current_question_index + 1,
            total_questions=len(session.questions)
        )
    
    def process_answer(self,
                       session_id: str,
                       answer: Union[str, int, bool, List[str]]) -> Tuple[str, Optional[str]]:
        """Process a diagnostic answer and determine next action."""
        session = self.active_diagnostics.get(session_id)
        if not session:
            return "No active diagnostic session found.", None
        
        current_question = session.questions[session.current_question_index]
        
        # Validate answer
        validation_result = self._validate_answer(current_question, answer)
        if not validation_result['valid']:
            return self._handle_invalid_answer(current_question, validation_result['reason']), None
        
        # Store answer
        session.answers[current_question.question] = {
            'answer': answer,
            'timestamp': datetime.now(),
            'question_type': current_question.question_type
        }
        
        # Determine routing
        next_action = self._determine_routing(session, current_question, answer)
        
        if next_action == 'next_question':
            session.current_question_index += 1
            return self._get_next_question(session_id), None
        elif next_action == 'complete':
            return self._complete_diagnostic(session_id)
        else:
            # Route to specific solution
            return self._route_to_solution(session, next_action)
    
    def _validate_answer(self,
                        question: DiagnosticQuestion,
                        answer: Union[str, int, bool, List[str]]) -> Dict[str, Any]:
        """Validate an answer based on question type."""
        result = {'valid': True, 'reason': None}
        
        if question.question_type == QuestionType.YES_NO:
            if not isinstance(answer, (bool, str)):
                result = {'valid': False, 'reason': 'Please answer Yes or No'}
            elif isinstance(answer, str) and answer.lower() not in ['yes', 'no', 'y', 'n']:
                result = {'valid': False, 'reason': 'Please answer Yes or No'}
        
        elif question.question_type == QuestionType.MULTIPLE_CHOICE:
            if question.options:
                if isinstance(answer, int):
                    if answer < 1 or answer > len(question.options):
                        result = {'valid': False, 'reason': f'Please choose a number between 1 and {len(question.options)}'}
                elif isinstance(answer, str):
                    if answer not in question.options:
                        result = {'valid': False, 'reason': 'Please choose from the provided options'}
        
        elif question.question_type == QuestionType.NUMERIC:
            if not isinstance(answer, (int, float)):
                try:
                    float(answer)
                except (ValueError, TypeError):
                    result = {'valid': False, 'reason': 'Please provide a valid number'}
        
        elif question.question_type == QuestionType.SCALE:
            try:
                value = int(answer)
                if value < 1 or value > 10:
                    result = {'valid': False, 'reason': 'Please provide a number between 1 and 10'}
            except (ValueError, TypeError):
                result = {'valid': False, 'reason': 'Please provide a number between 1 and 10'}
        
        return result
    
    def _handle_invalid_answer(self, question: DiagnosticQuestion, reason: str) -> str:
        """Handle invalid answers with helpful guidance."""
        response_parts = [f"❌ {reason}\n"]
        response_parts.append("Let me ask the question again:\n")
        response_parts.append(question.question)
        
        if question.question_type == QuestionType.MULTIPLE_CHOICE and question.options:
            response_parts.append("\nPlease choose from:")
            for i, option in enumerate(question.options, 1):
                response_parts.append(f"{i}. {option}")
        
        return "\n".join(response_parts)
    
    def _determine_routing(self,
                          session: 'DiagnosticSession',
                          question: DiagnosticQuestion,
                          answer: Any) -> str:
        """Determine the next action based on the answer."""
        # Check routing rules
        category_rules = self.routing_rules.get(session.category, {})
        question_key = question.question.lower().replace(' ', '_')[:20]  # Simple key generation
        
        if question_key in category_rules:
            answer_key = str(answer).lower()
            if answer_key in category_rules[question_key]:
                return category_rules[question_key][answer_key]
        
        # Check if there are follow-up questions
        if question.follow_up_questions:
            # In practice, would load and add follow-up questions
            return 'next_question'
        
        # Default behavior
        if session.current_question_index < len(session.questions) - 1:
            return 'next_question'
        else:
            return 'complete'
    
    def _route_to_solution(self,
                          session: 'DiagnosticSession',
                          solution_key: str) -> Tuple[str, str]:
        """Route to a specific solution based on diagnostic results."""
        # In practice, would look up the appropriate solution
        response_parts = ["Based on your answers, I've identified the issue.\n"]
        
        # Provide solution based on routing key
        solutions = {
            'check_network_hardware': "Let's check your network hardware connections.",
            'check_wifi_settings': "Let's review your WiFi settings.",
            'power_cycle_router': "Let's try restarting your router.",
            'check_power_cable': "Let's ensure the printer is properly connected to power.",
            'identify_error_code': "Let's look up that error code.",
            'run_printer_diagnostics': "Let's run the printer's built-in diagnostics."
        }
        
        solution = solutions.get(solution_key, "Let me find the best solution for you.")
        response_parts.append(solution)
        
        return "\n".join(response_parts), solution_key
    
    def _complete_diagnostic(self, session_id: str) -> Tuple[str, Optional[str]]:
        """Complete the diagnostic session and provide recommendations."""
        session = self.active_diagnostics.get(session_id)
        if not session:
            return "No active diagnostic session found.", None
        
        session.completed_at = datetime.now()
        
        # Analyze answers to determine issue
        analysis = self._analyze_answers(session)
        
        response_parts = ["**Diagnostic Complete**\n"]
        response_parts.append("Based on your answers, here's what I found:\n")
        response_parts.append(f"**Issue identified:** {analysis['issue']}")
        response_parts.append(f"**Confidence:** {analysis['confidence']:.0%}")
        response_parts.append(f"\n**Recommended solution:** {analysis['solution']}")
        
        # Clean up
        del self.active_diagnostics[session_id]
        
        return "\n".join(response_parts), analysis.get('article_id')
    
    def _analyze_answers(self, session: 'DiagnosticSession') -> Dict[str, Any]:
        """Analyze diagnostic answers to determine the issue."""
        # Simple analysis - in practice would be more sophisticated
        answers_list = list(session.answers.values())
        
        # Count negative responses
        negative_count = sum(1 for a in answers_list 
                           if str(a['answer']).lower() in ['no', 'false', 'n'])
        
        confidence = 0.8 if len(answers_list) >= 3 else 0.6
        
        if negative_count > len(answers_list) / 2:
            return {
                'issue': 'Hardware or connectivity problem',
                'confidence': confidence,
                'solution': 'Check physical connections and restart devices',
                'article_id': 'hw_001'
            }
        else:
            return {
                'issue': 'Software or configuration issue',
                'confidence': confidence,
                'solution': 'Review settings and update software',
                'article_id': 'sw_001'
            }


@dataclass
class DiagnosticSession:
    """Tracks a diagnostic question session."""
    category: str
    questions: List[DiagnosticQuestion]
    started_at: datetime
    current_question_index: int = 0
    answers: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    completed_at: Optional[datetime] = None


class ConversationContextManager:
    """Manages conversation context and history."""
    
    def __init__(self, session_timeout_minutes: int = 30):
        """Initialize the conversation context manager."""
        self.sessions: Dict[str, 'ConversationSession'] = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.user_profiles: Dict[str, 'UserProfile'] = {}
    
    def start_session(self,
                     session_id: str,
                     user_id: Optional[str] = None) -> 'ConversationSession':
        """Start a new conversation session."""
        # Load or create user profile
        profile = None
        if user_id:
            profile = self.user_profiles.get(user_id)
            if not profile:
                profile = UserProfile(user_id=user_id)
                self.user_profiles[user_id] = profile
        
        # Create new session
        session = ConversationSession(
            session_id=session_id,
            user_profile=profile,
            started_at=datetime.now()
        )
        
        self.sessions[session_id] = session
        return session
    
    def add_turn(self,
                session_id: str,
                speaker: str,
                message: str,
                **metadata) -> bool:
        """Add a conversation turn to the session."""
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        turn = ConversationTurn(
            timestamp=datetime.now(),
            speaker=speaker,
            message=message,
            **metadata
        )
        
        session.turns.append(turn)
        session.last_activity = datetime.now()
        
        # Update context based on the turn
        self._update_context(session, turn)
        
        return True
    
    def _update_context(self,
                       session: 'ConversationSession',
                       turn: ConversationTurn):
        """Update session context based on the conversation turn."""
        # Extract and store relevant information
        if turn.speaker == "user":
            # Update technical level based on language complexity
            if any(term in turn.message.lower() for term in ['config', 'registry', 'terminal', 'CLI']):
                session.context.technical_level = TechnicalLevel.EXPERT
            elif any(term in turn.message.lower() for term in ['click', 'button', 'screen', 'icon']):
                session.context.technical_level = TechnicalLevel.BEGINNER
            
            # Detect emotion
            if any(word in turn.message.lower() for word in ['frustrated', 'annoying', 'angry', 'upset']):
                session.context.current_emotion = 'frustrated'
            elif any(word in turn.message.lower() for word in ['confused', "don't understand", 'lost']):
                session.context.current_emotion = 'confused'
            elif any(word in turn.message.lower() for word in ['thanks', 'great', 'perfect', 'worked']):
                session.context.current_emotion = 'satisfied'
        
        # Update response count
        if turn.speaker == "bot":
            session.context.response_count += 1
        
        # Update state
        if turn.response_type == ResponseType.ESCALATION:
            session.state = ConversationState.ESCALATED
        elif turn.response_type in [ResponseType.ARTICLE_FULL, ResponseType.STEP_BY_STEP]:
            session.state = ConversationState.PRESENTING_SOLUTION
        elif turn.response_type == ResponseType.DIAGNOSTIC:
            session.state = ConversationState.GATHERING_INFO
    
    def get_context(self, session_id: str) -> Optional[ResponseContext]:
        """Get the current context for a session."""
        session = self.sessions.get(session_id)
        return session.context if session else None
    
    def get_history(self,
                   session_id: str,
                   last_n_turns: Optional[int] = None) -> List[ConversationTurn]:
        """Get conversation history for a session."""
        session = self.sessions.get(session_id)
        if not session:
            return []
        
        if last_n_turns:
            return session.turns[-last_n_turns:]
        return session.turns
    
    def should_escalate(self, session_id: str) -> Tuple[bool, str]:
        """Determine if the conversation should be escalated."""
        session = self.sessions.get(session_id)
        if not session:
            return False, ""
        
        # Check for escalation conditions
        if session.context.current_emotion == 'frustrated' and session.context.response_count > 3:
            return True, "emotional_distress"
        
        if session.failed_solution_attempts >= 3:
            return True, "repeated_failure"
        
        if session.state == ConversationState.ESCALATED:
            return True, "already_escalated"
        
        # Check conversation duration
        duration = datetime.now() - session.started_at
        if duration > timedelta(minutes=20) and session.state != ConversationState.COMPLETED:
            return True, "complex_issue"
        
        return False, ""
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions."""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if current_time - session.last_activity > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self._save_session_history(self.sessions[session_id])
            del self.sessions[session_id]
        
        return len(expired_sessions)
    
    def _save_session_history(self, session: 'ConversationSession'):
        """Save session history for future reference."""
        # In practice, would save to database
        if session.user_profile:
            # Update user profile with session information
            session.user_profile.total_sessions += 1
            if session.state == ConversationState.COMPLETED:
                session.user_profile.successful_sessions += 1
            
            # Add to recent issues
            for turn in session.turns:
                if turn.article_id:
                    session.user_profile.previous_issues.append({
                        'article_id': turn.article_id,
                        'timestamp': turn.timestamp,
                        'resolved': session.state == ConversationState.COMPLETED
                    })
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences from profile."""
        profile = self.user_profiles.get(user_id)
        if profile:
            return profile.preferences
        return {}
    
    def update_user_preferences(self,
                               user_id: str,
                               preferences: Dict[str, Any]):
        """Update user preferences."""
        profile = self.user_profiles.get(user_id)
        if not profile:
            profile = UserProfile(user_id=user_id)
            self.user_profiles[user_id] = profile
        
        profile.preferences.update(preferences)


@dataclass
class ConversationSession:
    """Represents a conversation session."""
    session_id: str
    started_at: datetime
    user_profile: Optional['UserProfile'] = None
    context: ResponseContext = field(default_factory=ResponseContext)
    turns: List[ConversationTurn] = field(default_factory=list)
    state: ConversationState = ConversationState.INITIAL
    last_activity: datetime = field(default_factory=datetime.now)
    failed_solution_attempts: int = 0


@dataclass
class UserProfile:
    """User profile with preferences and history."""
    user_id: str
    created_at: datetime = field(default_factory=datetime.now)
    preferences: Dict[str, Any] = field(default_factory=dict)
    previous_issues: List[Dict[str, Any]] = field(default_factory=list)
    total_sessions: int = 0
    successful_sessions: int = 0
    preferred_technical_level: Optional[TechnicalLevel] = None


class ResponseQualityAnalyzer:
    """Analyzes and optimizes response quality."""
    
    def __init__(self):
        """Initialize the response quality analyzer."""
        self.target_readability_score = 60  # Flesch Reading Ease target
        self.optimal_length_range = (50, 300)  # words
        self.tone_keywords = self._load_tone_keywords()
    
    def _load_tone_keywords(self) -> Dict[str, List[str]]:
        """Load keywords for tone analysis."""
        return {
            'professional': ['please', 'thank you', 'kindly', 'appreciate', 'assist'],
            'friendly': ['happy', 'glad', 'help', 'sure', 'great'],
            'empathetic': ['understand', 'frustrating', 'sorry', 'appreciate', 'concern'],
            'technical': ['configure', 'system', 'process', 'execute', 'parameter'],
            'casual': ['hey', 'gonna', 'stuff', 'thing', 'yeah']
        }
    
    def analyze_response(self, response: str) -> Dict[str, Any]:
        """Analyze response quality metrics."""
        return {
            'readability_score': self.calculate_readability(response),
            'length_words': len(response.split()),
            'tone': self.analyze_tone(response),
            'technical_level': self.assess_technical_level(response),
            'quality_score': self.calculate_quality_score(response),
            'suggestions': self.generate_suggestions(response)
        }
    
    def calculate_readability(self, text: str) -> float:
        """Calculate Flesch Reading Ease score."""
        try:
            return textstat.flesch_reading_ease(text)
        except:
            return 0.0
    
    def analyze_tone(self, text: str) -> Dict[str, float]:
        """Analyze the tone of the response."""
        text_lower = text.lower()
        tone_scores = {}
        
        for tone, keywords in self.tone_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            tone_scores[tone] = score / len(keywords) if keywords else 0
        
        # Normalize scores
        total = sum(tone_scores.values())
        if total > 0:
            tone_scores = {k: v/total for k, v in tone_scores.items()}
        
        return tone_scores
    
    def assess_technical_level(self, text: str) -> TechnicalLevel:
        """Assess the technical level of the response."""
        technical_terms = ['configuration', 'parameter', 'protocol', 'interface', 
                          'registry', 'terminal', 'command', 'syntax']
        simple_terms = ['click', 'button', 'screen', 'icon', 'menu', 'window']
        
        text_lower = text.lower()
        technical_count = sum(1 for term in technical_terms if term in text_lower)
        simple_count = sum(1 for term in simple_terms if term in text_lower)
        
        if technical_count > simple_count * 2:
            return TechnicalLevel.EXPERT
        elif simple_count > technical_count * 2:
            return TechnicalLevel.BEGINNER
        else:
            return TechnicalLevel.INTERMEDIATE
    
    def calculate_quality_score(self, response: str) -> float:
        """Calculate overall quality score (0-100)."""
        scores = []
        
        # Readability score (normalized to 0-100)
        readability = self.calculate_readability(response)
        readability_score = min(100, max(0, readability))
        scores.append(readability_score)
        
        # Length score
        word_count = len(response.split())
        if self.optimal_length_range[0] <= word_count <= self.optimal_length_range[1]:
            length_score = 100
        else:
            if word_count < self.optimal_length_range[0]:
                length_score = (word_count / self.optimal_length_range[0]) * 100
            else:
                length_score = max(0, 100 - ((word_count - self.optimal_length_range[1]) / 10))
        scores.append(length_score)
        
        # Tone consistency score
        tone_scores = self.analyze_tone(response)
        if tone_scores:
            # Higher score for more consistent tone (one dominant tone)
            max_tone_score = max(tone_scores.values())
            tone_consistency = max_tone_score * 100
            scores.append(tone_consistency)
        
        # Structure score (presence of formatting, lists, etc.)
        structure_score = 0
        if '**' in response or '##' in response:  # Headers
            structure_score += 25
        if '\n•' in response or '\n-' in response or '\n1.' in response:  # Lists
            structure_score += 25
        if '\n\n' in response:  # Paragraphs
            structure_score += 25
        if '```' in response or '`' in response:  # Code blocks
            structure_score += 25
        scores.append(structure_score)
        
        return sum(scores) / len(scores) if scores else 0
    
    def generate_suggestions(self, response: str) -> List[str]:
        """Generate improvement suggestions for the response."""
        suggestions = []
        
        # Check readability
        readability = self.calculate_readability(response)
        if readability < 30:
            suggestions.append("Simplify language - the text is too complex")
        elif readability > 80:
            suggestions.append("Consider adding more detail - the text might be too simple")
        
        # Check length
        word_count = len(response.split())
        if word_count < self.optimal_length_range[0]:
            suggestions.append(f"Response is too short ({word_count} words). Add more detail.")
        elif word_count > self.optimal_length_range[1]:
            suggestions.append(f"Response is too long ({word_count} words). Consider breaking it up.")
        
        # Check structure
        if '\n' not in response and word_count > 50:
            suggestions.append("Add paragraph breaks for better readability")
        
        if not any(marker in response for marker in ['**', '##', '•', '-', '1.']):
            suggestions.append("Consider using formatting (headers, lists) for better structure")
        
        # Check tone
        tone_scores = self.analyze_tone(response)
        if not any(score > 0.3 for score in tone_scores.values()):
            suggestions.append("Establish a clearer tone (professional, friendly, or empathetic)")
        
        return suggestions
    
    def optimize_response(self,
                         response: str,
                         target_level: TechnicalLevel,
                         target_tone: str = "professional") -> str:
        """Optimize response for target technical level and tone."""
        optimized = response
        
        # Adjust technical level
        current_level = self.assess_technical_level(response)
        if current_level != target_level:
            if target_level == TechnicalLevel.BEGINNER:
                # Simplify technical terms
                replacements = {
                    'configure': 'set up',
                    'execute': 'run',
                    'parameter': 'setting',
                    'interface': 'screen',
                    'protocol': 'method'
                }
                for old, new in replacements.items():
                    optimized = re.sub(rf'\b{old}\b', new, optimized, flags=re.IGNORECASE)
            elif target_level == TechnicalLevel.EXPERT:
                # Add technical details (simplified example)
                optimized = optimized.replace('restart the service', 
                                            'restart the service (systemctl restart <service-name>)')
        
        # Adjust tone
        if target_tone == "friendly":
            optimized = optimized.replace("Please", "Feel free to")
            optimized = optimized.replace("You must", "You'll want to")
        elif target_tone == "empathetic":
            if "error" in optimized.lower() or "problem" in optimized.lower():
                optimized = "I understand this can be frustrating. " + optimized
        
        # Ensure optimal length
        word_count = len(optimized.split())
        if word_count > self.optimal_length_range[1]:
            # Truncate or summarize (simplified)
            sentences = optimized.split('. ')
            if len(sentences) > 5:
                # Keep first 3 and last 2 sentences
                optimized = '. '.join(sentences[:3] + ['...'] + sentences[-2:])
        
        return optimized


class ResponseGenerationSystem:
    """Main system for generating chatbot responses."""
    
    def __init__(self):
        """Initialize the response generation system."""
        self.formatters = {
            ResponseType.ARTICLE_FULL: ArticleResponseFormatter(),
            ResponseType.STEP_BY_STEP: StepByStepResponseFormatter(),
            ResponseType.DIAGNOSTIC: QuestionResponseFormatter(),
            ResponseType.NO_RESULTS: NoResultsResponseFormatter(),
            ResponseType.ESCALATION: EscalationResponseFormatter()
        }
        
        self.template_engine = TemplateEngine()
        self.step_manager = SolutionStepManager()
        self.question_handler = DiagnosticQuestionHandler()
        self.context_manager = ConversationContextManager()
        self.quality_analyzer = ResponseQualityAnalyzer()
        
        logger.info("Response Generation System initialized")
    
    def generate_response(self,
                         response_type: ResponseType,
                         data: Any,
                         session_id: str,
                         user_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate a response based on type and data."""
        # Get or create session
        session = self.context_manager.sessions.get(session_id)
        if not session:
            session = self.context_manager.start_session(session_id, user_id)
        
        # Get context
        context = session.context
        
        # Generate response based on type
        formatter = self.formatters.get(response_type)
        if not formatter:
            response_text = "I'm not sure how to respond to that."
        else:
            response_text = formatter.format_response(data, context)
        
        # Analyze and optimize response
        quality_metrics = self.quality_analyzer.analyze_response(response_text)
        
        if quality_metrics['quality_score'] < 70:
            # Optimize if quality is low
            response_text = self.quality_analyzer.optimize_response(
                response_text,
                context.technical_level,
                "professional"
            )
            # Re-analyze after optimization
            quality_metrics = self.quality_analyzer.analyze_response(response_text)
        
        # Add turn to conversation history
        self.context_manager.add_turn(
            session_id=session_id,
            speaker="bot",
            message=response_text,
            response_type=response_type
        )
        
        # Check if escalation is needed
        should_escalate, escalation_reason = self.context_manager.should_escalate(session_id)
        
        return {
            'response': response_text,
            'type': response_type.value,
            'quality_metrics': quality_metrics,
            'should_escalate': should_escalate,
            'escalation_reason': escalation_reason,
            'session_id': session_id,
            'context': {
                'technical_level': context.technical_level.value,
                'response_count': context.response_count,
                'emotion': context.current_emotion
            }
        }
    
    def handle_user_input(self,
                         user_input: str,
                         session_id: str,
                         user_id: Optional[str] = None) -> Dict[str, Any]:
        """Process user input and generate appropriate response."""
        # Add user turn to history
        self.context_manager.add_turn(
            session_id=session_id,
            speaker="user",
            message=user_input
        )
        
        # Determine response type and data based on conversation state
        session = self.context_manager.sessions.get(session_id)
        
        if not session:
            # New session - generate greeting
            return self.generate_response(
                ResponseType.GREETING,
                {},
                session_id,
                user_id
            )
        
        # Check current state and generate appropriate response
        if session.state == ConversationState.GATHERING_INFO:
            # Process diagnostic answer
            response_text, article_id = self.question_handler.process_answer(
                session_id,
                user_input
            )
            return {
                'response': response_text,
                'type': ResponseType.DIAGNOSTIC.value,
                'article_id': article_id,
                'session_id': session_id
            }
        
        elif session.state == ConversationState.PRESENTING_SOLUTION:
            # Check if user is confirming step completion
            if any(word in user_input.lower() for word in ['done', 'completed', 'finished', 'yes']):
                response = self.step_manager.confirm_step_completion(
                    session_id,
                    success=True,
                    user_feedback=user_input
                )
                return {
                    'response': response,
                    'type': ResponseType.STEP_BY_STEP.value,
                    'session_id': session_id
                }
        
        # Default: generate clarification request
        return self.generate_response(
            ResponseType.CLARIFICATION,
            {'topic': 'your issue'},
            session_id,
            user_id
        )


# Export main components
__all__ = [
    'ResponseGenerationSystem',
    'ResponseType',
    'TechnicalLevel',
    'ConversationState',
    'ResponseContext',
    'ArticleResponseFormatter',
    'StepByStepResponseFormatter',
    'QuestionResponseFormatter',
    'NoResultsResponseFormatter',
    'EscalationResponseFormatter',
    'TemplateEngine',
    'SolutionStepManager',
    'DiagnosticQuestionHandler',
    'ConversationContextManager',
    'ResponseQualityAnalyzer'
]