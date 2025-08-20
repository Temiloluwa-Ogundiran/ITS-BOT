#!/usr/bin/env python3
"""
Response Formatter Classes for Helpdesk Chatbot
Provides various response formatting capabilities for different types of chatbot interactions.
"""

import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from models import KnowledgeArticle, SolutionStep, DiagnosticQuestion, DifficultyLevel

logger = logging.getLogger(__name__)


class ResponseType(str, Enum):
    """Types of responses the chatbot can generate."""
    ARTICLE = "article"
    STEP_BY_STEP = "step_by_step"
    QUESTION = "question"
    NO_RESULTS = "no_results"
    ESCALATION = "escalation"
    GREETING = "greeting"
    ERROR = "error"
    CONFIRMATION = "confirmation"


class ResponseFormat(str, Enum):
    """Formatting options for responses."""
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    RICH_TEXT = "rich_text"


@dataclass
class ResponseContext:
    """Context information for response generation."""
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    software_version: Optional[str] = None
    os_type: Optional[str] = None
    difficulty_preference: Optional[str] = None
    previous_issues: List[str] = field(default_factory=list)
    conversation_start: Optional[datetime] = None
    current_step: Optional[int] = None
    completed_steps: List[int] = field(default_factory=list)
    diagnostic_answers: Dict[str, Any] = field(default_factory=dict)


class ArticleResponse:
    """Formats full article responses with solution steps."""
    
    def __init__(self, format_type: ResponseFormat = ResponseFormat.TEXT):
        self.format_type = format_type
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, str]:
        """Load response templates."""
        return {
            "full_article": """🔧 **{title}**

**Category:** {category}
**Difficulty:** {difficulty}
**Estimated Time:** {time} minutes
**Success Rate:** {success_rate}%

**Problem Description:**
{content}

**Solution Steps:**
{steps}

**Diagnostic Questions:**
{questions}

**Additional Tips:**
- Make sure to follow each step in order
- If you encounter issues, try the diagnostic questions
- Contact support if the problem persists""",
            
            "simple_article": """**{title}**

{content}

**Quick Steps:**
{steps}""",
            
            "technical_article": """# {title}

## Technical Details
- **Category:** {category}
- **Difficulty:** {difficulty}
- **Time:** {time} minutes
- **Success Rate:** {success_rate}%

## Content
{content}

## Solution Steps
{steps}

## Diagnostic Questions
{questions}

## Troubleshooting
If the above steps don't resolve the issue, please provide:
1. Error messages you're seeing
2. Steps you've already tried
3. Your system configuration"""
        }
    
    def format_response(self, article: KnowledgeArticle, context: ResponseContext, 
                       template_name: str = "full_article") -> str:
        """Format a full article response."""
        try:
            template = self.templates.get(template_name, self.templates["full_article"])
            
            # Format solution steps
            steps_text = self._format_solution_steps(article.solution_steps)
            
            # Format diagnostic questions
            questions_text = self._format_diagnostic_questions(article.diagnostic_questions)
            
            # Prepare variables for template
            variables = {
                "title": article.title,
                "category": article.category,
                "difficulty": article.difficulty_level.value,
                "time": article.estimated_time_minutes,
                "success_rate": int(article.success_rate * 100),
                "content": article.content,
                "steps": steps_text,
                "questions": questions_text
            }
            
            # Apply template with variable substitution
            response = template.format(**variables)
            
            # Apply final formatting based on type
            if self.format_type == ResponseFormat.MARKDOWN:
                response = self._format_markdown(response)
            elif self.format_type == ResponseFormat.HTML:
                response = self._format_html(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error formatting article response: {e}")
            return f"Sorry, I encountered an error formatting the article '{article.title}'. Please try again."
    
    def _format_solution_steps(self, steps: List[SolutionStep]) -> str:
        """Format solution steps for display."""
        if not steps:
            return "No specific steps provided."
        
        formatted_steps = []
        for step in steps:
            step_text = f"{step.order}. **{step.title}**\n   {step.content}"
            if hasattr(step, 'estimated_time_minutes') and step.estimated_time_minutes:
                step_text += f" (Estimated: {step.estimated_time_minutes} min)"
            formatted_steps.append(step_text)
        
        return "\n\n".join(formatted_steps)
    
    def _format_diagnostic_questions(self, questions: List[DiagnosticQuestion]) -> str:
        """Format diagnostic questions for display."""
        if not questions:
            return "No diagnostic questions available."
        
        formatted_questions = []
        for question in questions:
            q_text = f"• {question.question}"
            if hasattr(question, 'help_text') and question.help_text:
                q_text += f"\n  *{question.help_text}*"
            formatted_questions.append(q_text)
        
        return "\n".join(formatted_questions)
    
    def _format_markdown(self, text: str) -> str:
        """Apply markdown formatting."""
        # Convert basic formatting to markdown
        text = re.sub(r'\*\*(.*?)\*\*', r'**\1**', text)
        text = re.sub(r'\*(.*?)\*', r'*\1*', text)
        return text
    
    def _format_html(self, text: str) -> str:
        """Convert to HTML format."""
        # Convert markdown-style formatting to HTML
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        text = re.sub(r'\n', r'<br>', text)
        return f"<div class='article-response'>{text}</div>"


class StepByStepResponse:
    """Manages progressive step revelation and user progress tracking."""
    
    def __init__(self):
        self.step_templates = {
            "step_intro": "Let's solve this step by step. Here's step {current_step} of {total_steps}:",
            "step_content": "**Step {step_number}: {title}**\n\n{content}",
            "step_completion": "Great! Step {step_number} is complete. Ready for the next step?",
            "all_steps_complete": "🎉 Excellent! You've completed all {total_steps} steps. The issue should now be resolved!",
            "step_help": "Need help with this step? You can:\n• Ask me to clarify\n• Request a hint\n• Move to the next step\n• Start over"
        }
    
    def get_next_step(self, article: KnowledgeArticle, context: ResponseContext) -> str:
        """Get the next step to present to the user."""
        if not article.solution_steps:
            return "This article doesn't have specific steps to follow."
        
        current_step_num = context.current_step or 0
        total_steps = len(article.solution_steps)
        
        if current_step_num >= total_steps:
            return self.step_templates["all_steps_complete"].format(total_steps=total_steps)
        
        step = article.solution_steps[current_step_num]
        
        # Build step response
        if current_step_num == 0:
            response = self.step_templates["step_intro"].format(
                current_step=current_step_num + 1, 
                total_steps=total_steps
            )
        else:
            response = ""
        
        response += "\n\n" + self.step_templates["step_content"].format(
            step_number=current_step_num + 1,
            title=step.title,
            content=step.content
        )
        
        # Add estimated time if available
        if hasattr(step, 'estimated_time_minutes') and step.estimated_time_minutes:
            response += f"\n\n⏱️ Estimated time: {step.estimated_time_minutes} minutes"
        
        # Add help options
        response += "\n\n" + self.step_templates["step_help"]
        
        return response
    
    def confirm_step_completion(self, step_number: int, context: ResponseContext) -> str:
        """Confirm that a step has been completed."""
        context.completed_steps.append(step_number)
        context.current_step = step_number
        
        return self.step_templates["step_completion"].format(step_number=step_number)
    
    def get_step_progress(self, context: ResponseContext, total_steps: int) -> str:
        """Get current progress information."""
        completed = len(context.completed_steps)
        current = context.current_step or 0
        
        progress_bar = self._create_progress_bar(completed, total_steps)
        
        return f"""**Progress: {completed}/{total_steps} steps completed**

{progress_bar}

**Current Status:**
• Completed: {', '.join(map(str, context.completed_steps)) if context.completed_steps else 'None'}
• Current: Step {current + 1 if current < total_steps else 'Complete'}
• Remaining: {total_steps - completed} steps"""
    
    def _create_progress_bar(self, completed: int, total: int, width: int = 20) -> str:
        """Create a visual progress bar."""
        if total == 0:
            return "█" * width
        
        filled = int((completed / total) * width)
        empty = width - filled
        
        return "█" * filled + "░" * empty
    
    def can_skip_step(self, step_number: int, context: ResponseContext) -> bool:
        """Check if a step can be skipped."""
        # Allow skipping if previous step is completed
        return step_number > 0 and (step_number - 1) in context.completed_steps
    
    def get_step_summary(self, article: KnowledgeArticle, context: ResponseContext) -> str:
        """Get a summary of all steps and completion status."""
        if not article.solution_steps:
            return "No steps available for this article."
        
        summary = "**Step Summary:**\n\n"
        
        for i, step in enumerate(article.solution_steps):
            status = "✅" if i in context.completed_steps else "⏳"
            current = "📍" if i == context.current_step else ""
            
            summary += f"{status} {current} Step {i + 1}: {step.title}\n"
            
            if i in context.completed_steps:
                summary += f"   Completed at: {datetime.now().strftime('%H:%M:%S')}\n"
            elif i == context.current_step:
                summary += f"   **Currently working on this step**\n"
            
            summary += "\n"
        
        return summary


class QuestionResponse:
    """Handles diagnostic questions and user answer processing."""
    
    def __init__(self):
        self.question_templates = {
            "question_intro": "To help you better, I need to ask a few questions:",
            "question_format": "**Question {current}/{total}:** {question}",
            "question_options": "**Options:** {options}",
            "question_help": "💡 {help_text}",
            "answer_confirmation": "Got it! Your answer: {answer}",
            "next_question": "Thanks! Here's the next question:",
            "all_questions_complete": "Perfect! Based on your answers, here's the best solution:"
        }
    
    def get_next_question(self, questions: List[DiagnosticQuestion], 
                         context: ResponseContext) -> str:
        """Get the next diagnostic question to ask."""
        if not questions:
            return "No diagnostic questions available for this issue."
        
        answered_count = len(context.diagnostic_answers)
        total_questions = len(questions)
        
        if answered_count >= total_questions:
            return self.question_templates["all_questions_complete"]
        
        question = questions[answered_count]
        
        # Build question response
        if answered_count == 0:
            response = self.question_templates["question_intro"] + "\n\n"
        else:
            response = self.question_templates["next_question"] + "\n\n"
        
        response += self.question_templates["question_format"].format(
            current=answered_count + 1,
            total=total_questions,
            question=question.question
        )
        
        # Add options if available
        if hasattr(question, 'options') and question.options:
            response += "\n\n" + self.question_templates["question_options"].format(
                options=", ".join(question.options)
            )
        
        # Add help text if available
        if hasattr(question, 'help_text') and question.help_text:
            response += "\n\n" + self.question_templates["question_help"].format(
                help_text=question.help_text
            )
        
        # Add answer format guidance
        response += "\n\n**Please provide your answer below.**"
        
        return response
    
    def process_answer(self, question: DiagnosticQuestion, answer: str, 
                      context: ResponseContext) -> Tuple[str, bool]:
        """Process a user's answer to a diagnostic question."""
        try:
            # Validate answer based on question type
            if hasattr(question, 'question_type'):
                if question.question_type == 'yes_no':
                    processed_answer = self._process_yes_no_answer(answer)
                elif question.question_type == 'multiple_choice':
                    processed_answer = self._process_multiple_choice_answer(answer, question.options)
                elif question.question_type == 'numeric':
                    processed_answer = self._process_numeric_answer(answer)
                else:
                    processed_answer = answer
            else:
                processed_answer = answer
            
            # Store the answer
            question_key = f"q_{len(context.diagnostic_answers)}"
            context.diagnostic_answers[question_key] = {
                'question': question.question,
                'answer': processed_answer,
                'timestamp': datetime.now().isoformat()
            }
            
            # Generate confirmation message
            confirmation = self.question_templates["answer_confirmation"].format(
                answer=processed_answer
            )
            
            return confirmation, True
            
        except ValueError as e:
            return f"Sorry, I couldn't understand your answer. {str(e)} Please try again.", False
    
    def _process_yes_no_answer(self, answer: str) -> str:
        """Process yes/no answers."""
        answer_lower = answer.lower().strip()
        
        if answer_lower in ['yes', 'y', 'true', '1', 'ok', 'sure']:
            return 'yes'
        elif answer_lower in ['no', 'n', 'false', '0', 'not', "don't"]:
            return 'no'
        else:
            raise ValueError("Please answer with 'yes' or 'no'.")
    
    def _process_multiple_choice_answer(self, answer: str, options: List[str]) -> str:
        """Process multiple choice answers."""
        answer_lower = answer.lower().strip()
        
        # Try exact match first
        for option in options:
            if answer_lower == option.lower():
                return option
        
        # Try partial match
        for option in options:
            if answer_lower in option.lower() or option.lower() in answer_lower:
                return option
        
        # Try number selection
        try:
            num = int(answer)
            if 1 <= num <= len(options):
                return options[num - 1]
        except ValueError:
            pass
        
        raise ValueError(f"Please choose from: {', '.join(options)}")
    
    def _process_numeric_answer(self, answer: str) -> str:
        """Process numeric answers."""
        try:
            # Remove common non-numeric characters
            clean_answer = re.sub(r'[^\d.]', '', answer)
            float(clean_answer)  # Validate it's a number
            return clean_answer
        except ValueError:
            raise ValueError("Please provide a valid number.")
    
    def get_answers_summary(self, context: ResponseContext) -> str:
        """Get a summary of all diagnostic answers."""
        if not context.diagnostic_answers:
            return "No diagnostic questions have been answered yet."
        
        summary = "**Diagnostic Summary:**\n\n"
        
        for key, data in context.diagnostic_answers.items():
            summary += f"**Q:** {data['question']}\n"
            summary += f"**A:** {data['answer']}\n"
            summary += f"**Time:** {data['timestamp'][:19]}\n\n"
        
        return summary
    
    def can_route_to_solution(self, context: ResponseContext, 
                             required_answers: int) -> bool:
        """Check if we have enough answers to route to a solution."""
        return len(context.diagnostic_answers) >= required_answers


class NoResultsResponse:
    """Handles cases when no search results are found."""
    
    def __init__(self):
        self.suggestion_templates = {
            "no_results": """I couldn't find an exact match for your query: **"{query}"**

Here are some suggestions to help you:""",
            
            "alternative_search": """**Try these alternative searches:**
{alternatives}""",
            
            "category_suggestions": """**Browse by category:**
{categories}""",
            
            "general_help": """**General troubleshooting tips:**
• Check if you're using the correct terminology
• Try searching for broader terms
• Look in related categories
• Contact support for specific issues""",
            
            "escalation_prompt": """**Still need help?**
If none of these suggestions help, I can:
• Transfer you to a human agent
• Create a support ticket
• Schedule a callback
• Provide general IT resources"""
        }
    
    def generate_response(self, query: str, context: ResponseContext, 
                         available_categories: List[str] = None) -> str:
        """Generate a helpful response when no results are found."""
        try:
            response = self.suggestion_templates["no_results"].format(query=query)
            
            # Add alternative search suggestions
            alternatives = self._generate_alternative_searches(query)
            response += "\n\n" + self.suggestion_templates["alternative_search"].format(
                alternatives=alternatives
            )
            
            # Add category suggestions if available
            if available_categories:
                response += "\n\n" + self.suggestion_templates["category_suggestions"].format(
                    categories=self._format_categories(available_categories)
                )
            
            # Add general help
            response += "\n\n" + self.suggestion_templates["general_help"]
            
            # Add escalation prompt
            response += "\n\n" + self.suggestion_templates["escalation_prompt"]
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating no results response: {e}")
            return "I'm sorry, I couldn't find what you're looking for. Please try rephrasing your question or contact support for assistance."
    
    def _generate_alternative_searches(self, query: str) -> str:
        """Generate alternative search suggestions."""
        alternatives = []
        
        # Remove common words and try variations
        words = query.lower().split()
        common_words = {'how', 'to', 'fix', 'solve', 'help', 'with', 'the', 'a', 'an', 'is', 'are', 'was', 'were'}
        
        # Try without common words
        filtered_words = [w for w in words if w not in common_words]
        if filtered_words:
            alternatives.append(f"• {' '.join(filtered_words)}")
        
        # Try with synonyms
        synonyms = {
            'error': ['problem', 'issue', 'bug', 'fault'],
            'fix': ['resolve', 'solve', 'repair', 'troubleshoot'],
            'password': ['pwd', 'pass', 'login', 'credential'],
            'email': ['mail', 'outlook', 'gmail', 'message']
        }
        
        for word in words:
            if word in synonyms:
                for synonym in synonyms[word][:2]:  # Limit to 2 synonyms
                    new_query = query.lower().replace(word, synonym)
                    alternatives.append(f"• {new_query}")
        
        # Add general alternatives
        alternatives.extend([
            f"• {query} troubleshooting",
            f"• {query} guide",
            f"• {query} instructions"
        ])
        
        return "\n".join(alternatives[:5])  # Limit to 5 alternatives
    
    def _format_categories(self, categories: List[str]) -> str:
        """Format category suggestions."""
        return "\n".join([f"• {cat}" for cat in categories[:8]])  # Limit to 8 categories


class EscalationResponse:
    """Handles escalation to human agents and support."""
    
    def __init__(self):
        self.escalation_templates = {
            "escalation_intro": """I understand you need additional help. Let me connect you with a human agent.""",
            
            "escalation_reasons": """**Common reasons for escalation:**
• Complex technical issues
• Multiple failed solutions
• Need for hands-on assistance
• Account or security concerns
• Custom configuration requirements""",
            
            "wait_time_info": """**Current wait times:**
• Chat support: {chat_wait} minutes
• Phone support: {phone_wait} minutes
• Email support: {email_wait} hours""",
            
            "escalation_options": """**How would you like to proceed?**

1. **Live Chat** - Connect with an agent now
2. **Phone Call** - Speak with a technician
3. **Email Ticket** - Get detailed response within 24 hours
4. **Callback** - Schedule a call at your convenience
5. **Continue with me** - Try a different approach""",
            
            "escalation_confirmation": """Perfect! I'm transferring you to {option}.

**Transfer Details:**
• Issue: {issue_summary}
• Priority: {priority}
• Estimated wait: {wait_time}

You'll be connected shortly. Thank you for your patience!"""
        }
    
    def should_escalate(self, context: ResponseContext, 
                       failed_attempts: int = 0,
                       issue_complexity: str = "medium") -> bool:
        """Determine if escalation is needed."""
        escalation_triggers = [
            failed_attempts >= 3,  # Multiple failed solution attempts
            context.current_step and context.current_step > 5,  # Too many steps
            len(context.diagnostic_answers) > 8,  # Too many questions
            issue_complexity == "high",  # High complexity issues
            self._has_escalation_keywords(context)  # User explicitly requests help
        ]
        
        return any(escalation_triggers)
    
    def _has_escalation_keywords(self, context: ResponseContext) -> bool:
        """Check if user has used escalation-related keywords."""
        escalation_keywords = [
            'human', 'agent', 'person', 'real', 'live', 'speak', 'talk',
            'call', 'phone', 'escalate', 'transfer', 'help', 'support'
        ]
        
        # This would typically check conversation history
        # For now, return False as a placeholder
        return False
    
    def generate_escalation_prompt(self, context: ResponseContext,
                                 wait_times: Dict[str, str] = None) -> str:
        """Generate escalation prompt with options."""
        if wait_times is None:
            wait_times = {
                'chat': '5-10',
                'phone': '15-20',
                'email': '2-4'
            }
        
        response = self.escalation_templates["escalation_intro"] + "\n\n"
        response += self.escalation_templates["escalation_reasons"] + "\n\n"
        response += self.escalation_templates["wait_time_info"].format(
            chat_wait=wait_times['chat'],
            phone_wait=wait_times['phone'],
            email_wait=wait_times['email']
        )
        response += "\n\n" + self.escalation_templates["escalation_options"]
        
        return response
    
    def confirm_escalation(self, option: str, context: ResponseContext,
                          priority: str = "normal") -> str:
        """Confirm escalation choice."""
        # Create issue summary from context
        issue_summary = self._create_issue_summary(context)
        
        # Determine wait time based on option
        wait_times = {
            'Live Chat': '5-10 minutes',
            'Phone Call': '15-20 minutes',
            'Email Ticket': '2-4 hours',
            'Callback': '1-2 hours',
            'Continue with me': 'immediate'
        }
        
        wait_time = wait_times.get(option, 'varies')
        
        return self.escalation_templates["escalation_confirmation"].format(
            option=option,
            issue_summary=issue_summary,
            priority=priority,
            wait_time=wait_time
        )
    
    def _create_issue_summary(self, context: ResponseContext) -> str:
        """Create a summary of the current issue for escalation."""
        summary_parts = []
        
        if context.current_step:
            summary_parts.append(f"Working on step {context.current_step}")
        
        if context.diagnostic_answers:
            summary_parts.append(f"{len(context.diagnostic_answers)} diagnostic questions answered")
        
        if context.previous_issues:
            summary_parts.append(f"Previous related issues: {', '.join(context.previous_issues[:3])}")
        
        if not summary_parts:
            summary_parts.append("General technical assistance needed")
        
        return "; ".join(summary_parts)
    
    def get_escalation_priority(self, context: ResponseContext,
                               issue_type: str = "general") -> str:
        """Determine escalation priority."""
        priority_factors = {
            'high': [
                'security', 'password', 'login', 'access',
                'data', 'backup', 'critical', 'urgent'
            ],
            'medium': [
                'performance', 'slow', 'error', 'broken',
                'not working', 'failed', 'issue'
            ],
            'low': [
                'question', 'how to', 'guide', 'tutorial',
                'information', 'help', 'learn'
            ]
        }
        
        # Check context for priority indicators
        for priority, keywords in priority_factors.items():
            if any(keyword in str(context).lower() for keyword in keywords):
                return priority
        
        return 'normal'

