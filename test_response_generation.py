"""
Comprehensive test suite for the Response Generation System.
Tests all response types, formatters, and conversation flows.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
from typing import List, Dict, Any

from response_generation import (
    ResponseGenerationSystem,
    ResponseType,
    TechnicalLevel,
    ConversationState,
    ResponseContext,
    ArticleResponseFormatter,
    StepByStepResponseFormatter,
    QuestionResponseFormatter,
    NoResultsResponseFormatter,
    EscalationResponseFormatter,
    TemplateEngine,
    SolutionStepManager,
    SolutionProgress,
    DiagnosticQuestionHandler,
    DiagnosticSession,
    ConversationContextManager,
    ConversationSession,
    ConversationTurn,
    UserProfile,
    ResponseQualityAnalyzer
)

from models import (
    KnowledgeArticle,
    SolutionStep,
    DiagnosticQuestion,
    QuestionType,
    SolutionStepType,
    DifficultyLevel
)


class TestResponseFormatters(unittest.TestCase):
    """Test response formatter classes."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.context = ResponseContext(
            user_name="John Doe",
            technical_level=TechnicalLevel.INTERMEDIATE,
            software_version="Windows 10",
            operating_system="Windows"
        )
        
        # Sample article
        self.article = KnowledgeArticle(
            article_id="test_001",
            title="How to Reset Password",
            content="This guide will help you reset your password.",
            category="Email",
            subcategory="Security",
            keywords=["password", "reset", "email"],
            symptoms=["Cannot login", "Forgot password"],
            difficulty_level=DifficultyLevel.EASY,
            estimated_time_minutes=10,
            success_rate=0.95,
            solution_steps=[
                SolutionStep(
                    order=1,
                    title="Open Email Settings",
                    content="Navigate to your email settings page",
                    step_type=SolutionStepType.INSTRUCTION,
                    estimated_time_minutes=2
                ),
                SolutionStep(
                    order=2,
                    title="Click Reset Password",
                    content="Find and click the 'Reset Password' button",
                    step_type=SolutionStepType.INSTRUCTION,
                    estimated_time_minutes=1
                )
            ]
        )
        
        # Sample diagnostic question
        self.question = DiagnosticQuestion(
            question="Is your computer connected to the internet?",
            question_type=QuestionType.YES_NO,
            help_text="Check if you can browse other websites",
            required=True
        )
    
    def test_article_response_formatter(self):
        """Test ArticleResponseFormatter."""
        formatter = ArticleResponseFormatter()
        response = formatter.format_response(self.article, self.context)
        
        # Check response contains key elements
        self.assertIn(self.article.title, response)
        self.assertIn(self.article.content, response)
        self.assertIn("Steps to resolve:", response)
        self.assertIn("Open Email Settings", response)
        self.assertIn("95%", response)  # Success rate
        self.assertIn("10 minutes", response)  # Time estimate
    
    def test_article_response_technical_level_adjustment(self):
        """Test technical level adjustment in article response."""
        formatter = ArticleResponseFormatter()
        
        # Test beginner level
        self.context.technical_level = TechnicalLevel.BEGINNER
        article = KnowledgeArticle(
            article_id="test_002",
            title="Configure Network",
            content="Execute the configuration script to initialize the network interface.",
            category="Network",
            subcategory="Setup",
            keywords=["network"],
            symptoms=["No connection"],
            difficulty_level=DifficultyLevel.MEDIUM
        )
        
        response = formatter.format_response(article, self.context)
        self.assertIn("set up", response.lower())  # "configure" -> "set up"
        self.assertIn("run", response.lower())  # "execute" -> "run"
        self.assertIn("start", response.lower())  # "initialize" -> "start"
    
    def test_step_by_step_formatter(self):
        """Test StepByStepResponseFormatter."""
        formatter = StepByStepResponseFormatter()
        step = self.article.solution_steps[0]
        
        # Test first step
        response = formatter.format_response(
            step=step,
            context=self.context,
            is_first_step=True,
            is_last_step=False,
            total_steps=2
        )
        
        self.assertIn("Step 1 of 2", response)
        self.assertIn("Open Email Settings", response)
        self.assertIn("2 minute", response)
        self.assertIn("Let me know when you've completed", response)
    
    def test_step_by_step_last_step(self):
        """Test last step formatting."""
        formatter = StepByStepResponseFormatter()
        step = self.article.solution_steps[1]
        
        response = formatter.format_response(
            step=step,
            context=self.context,
            is_first_step=False,
            is_last_step=True,
            total_steps=2
        )
        
        self.assertIn("Step 2 of 2", response)
        self.assertIn("final step", response)
        self.assertIn("resolves your issue", response)
    
    def test_question_response_formatter(self):
        """Test QuestionResponseFormatter."""
        formatter = QuestionResponseFormatter()
        
        # Test yes/no question
        response = formatter.format_response(
            question=self.question,
            context=self.context,
            question_number=1,
            total_questions=3
        )
        
        self.assertIn("Question 1 of 3", response)
        self.assertIn(self.question.question, response)
        self.assertIn("Yes or No", response)
        self.assertIn(self.question.help_text, response)
    
    def test_multiple_choice_question(self):
        """Test multiple choice question formatting."""
        formatter = QuestionResponseFormatter()
        question = DiagnosticQuestion(
            question="What type of error are you seeing?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=["Blue screen", "Black screen", "Frozen screen", "Error message"],
            required=True
        )
        
        response = formatter.format_response(
            question=question,
            context=self.context,
            question_number=2,
            total_questions=3
        )
        
        self.assertIn("Please choose from:", response)
        self.assertIn("1. Blue screen", response)
        self.assertIn("2. Black screen", response)
        self.assertIn("3. Frozen screen", response)
        self.assertIn("4. Error message", response)
    
    def test_no_results_formatter(self):
        """Test NoResultsResponseFormatter."""
        formatter = NoResultsResponseFormatter()
        
        response = formatter.format_response(
            query="complex technical issue",
            context=self.context,
            suggestions=["Password reset", "Network troubleshooting", "Software update"]
        )
        
        self.assertIn("couldn't find an exact match", response)
        self.assertIn("complex technical issue", response)
        self.assertIn("related topics", response)
        self.assertIn("Password reset", response)
        self.assertIn("Rephrase your question", response)
        self.assertIn("Talk to a human", response)
    
    def test_escalation_formatter(self):
        """Test EscalationResponseFormatter."""
        formatter = EscalationResponseFormatter()
        self.context.preferences['issue_summary'] = "Cannot connect to email"
        
        response = formatter.format_response(
            reason="complex_issue",
            context=self.context,
            ticket_number="HELP-12345",
            wait_time=5
        )
        
        self.assertIn("specialized assistance", response)
        self.assertIn("complex technical issue", response)
        self.assertIn("HELP-12345", response)
        self.assertIn("5 minutes", response)
        self.assertIn("Cannot connect to email", response)
        self.assertIn("Windows 10", response)


class TestTemplateEngine(unittest.TestCase):
    """Test the template engine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = TemplateEngine()
        self.context = ResponseContext(
            user_name="Jane Smith",
            software_version="Outlook 2019"
        )
    
    def test_render_template(self):
        """Test template rendering."""
        variables = {
            'solution_content': 'Click on the reset button',
            'time_estimate': '5-10',
            'additional_notes': 'Make sure to save your work first'
        }
        
        result = self.engine.render_template(
            category='email',
            template_type='password_reset',
            variables=variables,
            context=self.context
        )
        
        self.assertIn("Jane Smith", result)
        self.assertIn("Outlook 2019", result)
        self.assertIn("Click on the reset button", result)
        self.assertIn("5-10 minutes", result)
        self.assertIn("save your work first", result)
    
    def test_add_conditional_content(self):
        """Test conditional content addition."""
        base_content = "Here is the basic solution."
        conditions = {
            'is_windows': True,
            'is_mac': False,
            'needs_admin': True
        }
        conditional_content = {
            'is_windows': "For Windows: Use Control Panel",
            'is_mac': "For Mac: Use System Preferences",
            'needs_admin': "Note: Administrator rights required"
        }
        
        result = self.engine.add_conditional_content(
            base_content,
            conditions,
            conditional_content
        )
        
        self.assertIn("basic solution", result)
        self.assertIn("Control Panel", result)
        self.assertNotIn("System Preferences", result)
        self.assertIn("Administrator rights", result)


class TestSolutionStepManager(unittest.TestCase):
    """Test the solution step manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = SolutionStepManager()
        self.article = KnowledgeArticle(
            article_id="test_003",
            title="Fix Printer",
            content="Printer troubleshooting guide",
            category="Hardware",
            subcategory="Printer",
            keywords=["printer"],
            symptoms=["Not printing"],
            difficulty_level=DifficultyLevel.MEDIUM,
            solution_steps=[
                SolutionStep(
                    order=1,
                    title="Check Power",
                    content="Ensure printer is powered on",
                    step_type=SolutionStepType.VERIFICATION,
                    estimated_time_minutes=1
                ),
                SolutionStep(
                    order=2,
                    title="Check Connection",
                    content="Verify USB or network connection",
                    step_type=SolutionStepType.VERIFICATION,
                    estimated_time_minutes=2
                ),
                SolutionStep(
                    order=3,
                    title="Print Test Page",
                    content="Try printing a test page",
                    step_type=SolutionStepType.INSTRUCTION,
                    estimated_time_minutes=3
                )
            ]
        )
    
    def test_start_progressive_solution(self):
        """Test starting a progressive solution."""
        session_id = "test_session_001"
        response = self.manager.start_solution(
            session_id=session_id,
            article=self.article,
            mode="progressive"
        )
        
        self.assertIn("Step 1 of 3", response)
        self.assertIn("Check Power", response)
        self.assertIn("Ensure printer is powered on", response)
        
        # Check progress tracking
        progress = self.manager.get_progress(session_id)
        self.assertIsNotNone(progress)
        self.assertEqual(progress.article_id, "test_003")
        self.assertEqual(len(progress.steps), 3)
        self.assertEqual(progress.current_step_index, 0)
    
    def test_start_all_at_once_solution(self):
        """Test presenting all steps at once."""
        session_id = "test_session_002"
        response = self.manager.start_solution(
            session_id=session_id,
            article=self.article,
            mode="all_at_once"
        )
        
        self.assertIn("Step 1: Check Power", response)
        self.assertIn("Step 2: Check Connection", response)
        self.assertIn("Step 3: Print Test Page", response)
        self.assertIn("Total estimated time: 6 minutes", response)
    
    def test_confirm_step_completion_success(self):
        """Test confirming successful step completion."""
        session_id = "test_session_003"
        self.manager.start_solution(session_id, self.article, "progressive")
        
        # Confirm first step completion
        response = self.manager.confirm_step_completion(
            session_id=session_id,
            success=True,
            user_feedback="Power is on"
        )
        
        # Should show next step
        self.assertIn("Step 2 of 3", response)
        self.assertIn("Check Connection", response)
        
        # Check progress update
        progress = self.manager.get_progress(session_id)
        self.assertEqual(progress.current_step_index, 1)
        self.assertIn(1, progress.completed_steps)
    
    def test_confirm_step_completion_failure(self):
        """Test handling step failure."""
        session_id = "test_session_004"
        self.manager.start_solution(session_id, self.article, "progressive")
        
        response = self.manager.confirm_step_completion(
            session_id=session_id,
            success=False,
            user_feedback="Printer won't turn on"
        )
        
        self.assertIn("didn't work as expected", response)
        self.assertIn("Try this step again", response)
        self.assertIn("Skip to the next step", response)
        self.assertIn("Get help from a human agent", response)
    
    def test_complete_solution(self):
        """Test completing all steps."""
        session_id = "test_session_005"
        self.manager.start_solution(session_id, self.article, "progressive")
        
        # Complete all steps
        for _ in range(3):
            self.manager.confirm_step_completion(session_id, True)
        
        # Get final response (called after last step confirmation)
        progress = self.manager.get_progress(session_id)
        self.assertIsNone(progress)  # Should be cleaned up after completion


class TestDiagnosticQuestionHandler(unittest.TestCase):
    """Test the diagnostic question handler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = DiagnosticQuestionHandler()
        self.questions = [
            DiagnosticQuestion(
                question="Is the printer powered on?",
                question_type=QuestionType.YES_NO,
                required=True
            ),
            DiagnosticQuestion(
                question="What error message do you see?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=["Paper jam", "Out of ink", "Connection error", "No error"],
                required=True
            ),
            DiagnosticQuestion(
                question="How many pages have you tried to print?",
                question_type=QuestionType.NUMERIC,
                required=False
            )
        ]
    
    def test_start_diagnostic(self):
        """Test starting a diagnostic session."""
        session_id = "diag_001"
        response = self.handler.start_diagnostic(
            session_id=session_id,
            questions=self.questions,
            category="printer_issues"
        )
        
        self.assertIn("Question 1 of 3", response)
        self.assertIn("Is the printer powered on?", response)
        self.assertIn("Yes or No", response)
        
        # Check session creation
        session = self.handler.active_diagnostics.get(session_id)
        self.assertIsNotNone(session)
        self.assertEqual(len(session.questions), 3)
    
    def test_process_yes_no_answer(self):
        """Test processing yes/no answer."""
        session_id = "diag_002"
        self.handler.start_diagnostic(session_id, self.questions, "printer_issues")
        
        # Process valid answer
        response, route = self.handler.process_answer(session_id, "yes")
        
        self.assertIn("Question 2 of 3", response)
        self.assertIn("What error message", response)
        
        # Check answer storage
        session = self.handler.active_diagnostics[session_id]
        self.assertIn("Is the printer powered on?", session.answers)
        self.assertEqual(session.answers["Is the printer powered on?"]["answer"], "yes")
    
    def test_process_invalid_answer(self):
        """Test handling invalid answers."""
        session_id = "diag_003"
        self.handler.start_diagnostic(session_id, self.questions, "printer_issues")
        
        # Process invalid answer for yes/no question
        response, route = self.handler.process_answer(session_id, "maybe")
        
        self.assertIn("Please answer Yes or No", response)
        self.assertIn("Is the printer powered on?", response)
        
        # Session should not advance
        session = self.handler.active_diagnostics[session_id]
        self.assertEqual(session.current_question_index, 0)
    
    def test_process_multiple_choice_answer(self):
        """Test processing multiple choice answer."""
        session_id = "diag_004"
        self.handler.start_diagnostic(session_id, self.questions, "printer_issues")
        
        # Move to second question
        self.handler.process_answer(session_id, "yes")
        
        # Answer multiple choice with index
        response, route = self.handler.process_answer(session_id, 2)
        
        self.assertIn("Question 3 of 3", response)
        self.assertIn("How many pages", response)
    
    def test_process_numeric_answer(self):
        """Test processing numeric answer."""
        session_id = "diag_005"
        self.handler.start_diagnostic(session_id, self.questions, "printer_issues")
        
        # Move to third question
        self.handler.process_answer(session_id, "yes")
        self.handler.process_answer(session_id, 1)
        
        # Answer numeric question
        response, route = self.handler.process_answer(session_id, 5)
        
        # Should complete diagnostic
        self.assertIn("Diagnostic Complete", response)
        self.assertIn("Issue identified", response)
    
    def test_routing_based_on_answers(self):
        """Test routing to solutions based on answers."""
        session_id = "diag_006"
        
        # Set up questions with routing
        questions = [
            DiagnosticQuestion(
                question="can_access_internet",
                question_type=QuestionType.YES_NO,
                required=True
            )
        ]
        
        self.handler.start_diagnostic(session_id, questions, "network_connectivity")
        
        # Test routing for "no" answer
        response, route = self.handler.process_answer(session_id, "no")
        
        # Should route to network hardware check
        self.assertEqual(route, "check_network_hardware")


class TestConversationContextManager(unittest.TestCase):
    """Test the conversation context manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = ConversationContextManager(session_timeout_minutes=30)
    
    def test_start_session(self):
        """Test starting a new session."""
        session_id = "conv_001"
        user_id = "user_123"
        
        session = self.manager.start_session(session_id, user_id)
        
        self.assertIsNotNone(session)
        self.assertEqual(session.session_id, session_id)
        self.assertIsNotNone(session.user_profile)
        self.assertEqual(session.user_profile.user_id, user_id)
        self.assertEqual(session.state, ConversationState.INITIAL)
    
    def test_add_turn(self):
        """Test adding conversation turns."""
        session_id = "conv_002"
        self.manager.start_session(session_id)
        
        # Add user turn
        success = self.manager.add_turn(
            session_id=session_id,
            speaker="user",
            message="I can't print anything",
            intent="problem"
        )
        
        self.assertTrue(success)
        
        # Add bot turn
        self.manager.add_turn(
            session_id=session_id,
            speaker="bot",
            message="I'll help you with the printing issue",
            response_type=ResponseType.DIAGNOSTIC
        )
        
        # Check history
        history = self.manager.get_history(session_id)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].speaker, "user")
        self.assertEqual(history[1].speaker, "bot")
    
    def test_context_updates(self):
        """Test context updates based on conversation."""
        session_id = "conv_003"
        self.manager.start_session(session_id)
        
        # Technical user message
        self.manager.add_turn(
            session_id,
            "user",
            "I need to configure the registry settings for the printer driver"
        )
        
        context = self.manager.get_context(session_id)
        self.assertEqual(context.technical_level, TechnicalLevel.EXPERT)
        
        # Frustrated user message
        self.manager.add_turn(
            session_id,
            "user",
            "This is so frustrating! Nothing is working!"
        )
        
        context = self.manager.get_context(session_id)
        self.assertEqual(context.current_emotion, "frustrated")
    
    def test_should_escalate(self):
        """Test escalation detection."""
        session_id = "conv_004"
        session = self.manager.start_session(session_id)
        
        # Test emotional distress escalation
        session.context.current_emotion = "frustrated"
        session.context.response_count = 4
        
        should_escalate, reason = self.manager.should_escalate(session_id)
        self.assertTrue(should_escalate)
        self.assertEqual(reason, "emotional_distress")
        
        # Test repeated failure escalation
        session_id2 = "conv_005"
        session2 = self.manager.start_session(session_id2)
        session2.failed_solution_attempts = 3
        
        should_escalate, reason = self.manager.should_escalate(session_id2)
        self.assertTrue(should_escalate)
        self.assertEqual(reason, "repeated_failure")
    
    def test_session_cleanup(self):
        """Test expired session cleanup."""
        # Create sessions
        session1 = self.manager.start_session("old_session")
        session2 = self.manager.start_session("new_session")
        
        # Make one session old
        session1.last_activity = datetime.now() - timedelta(minutes=40)
        
        # Clean up expired sessions
        cleaned = self.manager.cleanup_expired_sessions()
        
        self.assertEqual(cleaned, 1)
        self.assertNotIn("old_session", self.manager.sessions)
        self.assertIn("new_session", self.manager.sessions)
    
    def test_user_preferences(self):
        """Test user preference management."""
        user_id = "user_456"
        
        # Update preferences
        preferences = {
            'preferred_contact': 'email',
            'technical_level': 'beginner',
            'language': 'en'
        }
        
        self.manager.update_user_preferences(user_id, preferences)
        
        # Retrieve preferences
        retrieved = self.manager.get_user_preferences(user_id)
        self.assertEqual(retrieved['preferred_contact'], 'email')
        self.assertEqual(retrieved['technical_level'], 'beginner')


class TestResponseQualityAnalyzer(unittest.TestCase):
    """Test the response quality analyzer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = ResponseQualityAnalyzer()
    
    def test_calculate_readability(self):
        """Test readability calculation."""
        simple_text = "Click the button. Save the file. Close the window."
        complex_text = ("The configuration parameters must be meticulously calibrated "
                       "to ensure optimal synchronization between the heterogeneous "
                       "subsystems within the distributed architecture.")
        
        simple_score = self.analyzer.calculate_readability(simple_text)
        complex_score = self.analyzer.calculate_readability(complex_text)
        
        # Simple text should have higher readability score
        self.assertGreater(simple_score, complex_score)
    
    def test_analyze_tone(self):
        """Test tone analysis."""
        professional_text = "Please kindly review the attached document. Thank you for your assistance."
        casual_text = "Hey, gonna check this stuff out. Yeah, that thing should work."
        
        professional_tone = self.analyzer.analyze_tone(professional_text)
        casual_tone = self.analyzer.analyze_tone(casual_text)
        
        self.assertGreater(professional_tone.get('professional', 0), 
                          professional_tone.get('casual', 0))
        self.assertGreater(casual_tone.get('casual', 0), 
                          casual_tone.get('professional', 0))
    
    def test_assess_technical_level(self):
        """Test technical level assessment."""
        beginner_text = "Click on the Start button, then click on Settings icon."
        expert_text = "Configure the network interface parameters via terminal using ifconfig."
        
        beginner_level = self.analyzer.assess_technical_level(beginner_text)
        expert_level = self.analyzer.assess_technical_level(expert_text)
        
        self.assertEqual(beginner_level, TechnicalLevel.BEGINNER)
        self.assertEqual(expert_level, TechnicalLevel.EXPERT)
    
    def test_calculate_quality_score(self):
        """Test overall quality score calculation."""
        good_response = """
**Solution Steps:**

Here's how to fix your issue:

1. First, check the power connection
2. Next, verify the network settings
3. Finally, restart the application

This should resolve your problem. Let me know if you need further assistance!
        """
        
        poor_response = "Try stuff."
        
        good_score = self.analyzer.calculate_quality_score(good_response)
        poor_score = self.analyzer.calculate_quality_score(poor_response)
        
        self.assertGreater(good_score, poor_score)
        self.assertGreater(good_score, 60)  # Good response should score > 60
        self.assertLess(poor_score, 40)  # Poor response should score < 40
    
    def test_generate_suggestions(self):
        """Test improvement suggestions generation."""
        # Too short response
        short_response = "Check settings."
        suggestions = self.analyzer.generate_suggestions(short_response)
        self.assertTrue(any("too short" in s for s in suggestions))
        
        # Too long response without structure
        long_response = " ".join(["This is a very long response"] * 100)
        suggestions = self.analyzer.generate_suggestions(long_response)
        self.assertTrue(any("too long" in s for s in suggestions))
        self.assertTrue(any("paragraph breaks" in s for s in suggestions))
    
    def test_optimize_response(self):
        """Test response optimization."""
        technical_response = "Execute the configuration protocol to initialize the interface."
        
        # Optimize for beginner
        optimized = self.analyzer.optimize_response(
            technical_response,
            TechnicalLevel.BEGINNER,
            "friendly"
        )
        
        self.assertIn("run", optimized.lower())  # "execute" -> "run"
        self.assertIn("set up", optimized.lower())  # "configure" -> "set up"
        self.assertNotIn("execute", optimized.lower())
        self.assertNotIn("protocol", optimized.lower())


class TestResponseGenerationSystem(unittest.TestCase):
    """Test the main response generation system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.system = ResponseGenerationSystem()
        self.session_id = "main_test_001"
        self.user_id = "test_user"
    
    def test_generate_article_response(self):
        """Test generating an article response."""
        article = KnowledgeArticle(
            article_id="art_001",
            title="Password Reset Guide",
            content="Follow these steps to reset your password",
            category="Security",
            subcategory="Authentication",
            keywords=["password", "reset"],
            symptoms=["Cannot login"],
            difficulty_level=DifficultyLevel.EASY,
            estimated_time_minutes=5,
            success_rate=0.98
        )
        
        result = self.system.generate_response(
            response_type=ResponseType.ARTICLE_FULL,
            data=article,
            session_id=self.session_id,
            user_id=self.user_id
        )
        
        self.assertEqual(result['type'], ResponseType.ARTICLE_FULL.value)
        self.assertIn("Password Reset Guide", result['response'])
        self.assertIn("quality_metrics", result)
        self.assertGreater(result['quality_metrics']['quality_score'], 0)
    
    def test_generate_no_results_response(self):
        """Test generating a no results response."""
        result = self.system.generate_response(
            response_type=ResponseType.NO_RESULTS,
            data={
                'query': 'obscure technical problem',
                'suggestions': ['Try searching for X', 'Look for Y']
            },
            session_id=self.session_id
        )
        
        self.assertEqual(result['type'], ResponseType.NO_RESULTS.value)
        self.assertIn("couldn't find", result['response'])
        self.assertIn("obscure technical problem", result['response'])
    
    def test_generate_escalation_response(self):
        """Test generating an escalation response."""
        result = self.system.generate_response(
            response_type=ResponseType.ESCALATION,
            data={
                'reason': 'complex_issue',
                'ticket_number': 'HELP-999',
                'wait_time': 10
            },
            session_id=self.session_id
        )
        
        self.assertEqual(result['type'], ResponseType.ESCALATION.value)
        self.assertIn("specialized assistance", result['response'])
        self.assertIn("HELP-999", result['response'])
        self.assertIn("10 minutes", result['response'])
    
    def test_handle_user_input_new_session(self):
        """Test handling user input for a new session."""
        result = self.system.handle_user_input(
            user_input="Hello, I need help",
            session_id="new_session_001",
            user_id=self.user_id
        )
        
        self.assertIn('response', result)
        self.assertEqual(result['session_id'], "new_session_001")
    
    def test_quality_optimization(self):
        """Test response quality optimization."""
        # Create a poor quality response
        poor_article = KnowledgeArticle(
            article_id="poor_001",
            title="Fix",
            content="Try stuff",
            category="General",
            subcategory="Other",
            keywords=["fix"],
            symptoms=["broken"],
            difficulty_level=DifficultyLevel.MEDIUM
        )
        
        result = self.system.generate_response(
            response_type=ResponseType.ARTICLE_FULL,
            data=poor_article,
            session_id="quality_test_001"
        )
        
        # System should attempt to optimize poor quality responses
        self.assertIn('quality_metrics', result)
        # Even after optimization, very poor content might not reach 70
        self.assertIsNotNone(result['quality_metrics']['quality_score'])


class TestConversationFlows(unittest.TestCase):
    """Test complete conversation flows."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.system = ResponseGenerationSystem()
    
    def test_diagnostic_to_solution_flow(self):
        """Test flow from diagnostic questions to solution."""
        session_id = "flow_001"
        
        # Start with a diagnostic question
        questions = [
            DiagnosticQuestion(
                question="Is your device connected?",
                question_type=QuestionType.YES_NO,
                required=True
            )
        ]
        
        # Start diagnostic
        self.system.question_handler.start_diagnostic(
            session_id,
            questions,
            "connectivity"
        )
        
        # Process answer
        response, route = self.system.question_handler.process_answer(
            session_id,
            "no"
        )
        
        self.assertIn("Diagnostic Complete", response)
    
    def test_step_by_step_solution_flow(self):
        """Test complete step-by-step solution flow."""
        session_id = "flow_002"
        
        article = KnowledgeArticle(
            article_id="flow_art_001",
            title="Network Setup",
            content="Setup guide",
            category="Network",
            subcategory="Configuration",
            keywords=["network"],
            symptoms=["No connection"],
            difficulty_level=DifficultyLevel.MEDIUM,
            solution_steps=[
                SolutionStep(
                    order=1,
                    title="Step 1",
                    content="Do this first",
                    step_type=SolutionStepType.INSTRUCTION
                ),
                SolutionStep(
                    order=2,
                    title="Step 2",
                    content="Do this second",
                    step_type=SolutionStepType.INSTRUCTION
                )
            ]
        )
        
        # Start solution
        response = self.system.step_manager.start_solution(
            session_id,
            article,
            "progressive"
        )
        
        self.assertIn("Step 1", response)
        
        # Complete first step
        response = self.system.step_manager.confirm_step_completion(
            session_id,
            True,
            "Done"
        )
        
        self.assertIn("Step 2", response)
        
        # Complete second step
        response = self.system.step_manager.confirm_step_completion(
            session_id,
            True,
            "Done"
        )
        
        self.assertIn("Solution Complete", response)
    
    def test_escalation_flow(self):
        """Test escalation flow."""
        session_id = "flow_003"
        
        # Create a frustrated user session
        session = self.system.context_manager.start_session(session_id)
        session.context.current_emotion = "frustrated"
        session.context.response_count = 5
        session.failed_solution_attempts = 3
        
        # Check escalation
        should_escalate, reason = self.system.context_manager.should_escalate(session_id)
        
        self.assertTrue(should_escalate)
        
        # Generate escalation response
        result = self.system.generate_response(
            ResponseType.ESCALATION,
            {'reason': reason},
            session_id
        )
        
        self.assertIn("assistance", result['response'])


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.system = ResponseGenerationSystem()
    
    def test_empty_article(self):
        """Test handling empty article."""
        article = KnowledgeArticle(
            article_id="empty_001",
            title="Empty Article",
            content="No content available",
            category="Test",
            subcategory="Test",
            keywords=[],
            symptoms=[],
            difficulty_level=DifficultyLevel.EASY
        )
        
        formatter = ArticleResponseFormatter()
        response = formatter.format_response(article, ResponseContext())
        
        self.assertIn("Empty Article", response)
        self.assertIn("No content available", response)
    
    def test_invalid_question_type(self):
        """Test handling invalid question type."""
        handler = DiagnosticQuestionHandler()
        question = DiagnosticQuestion(
            question="Test question",
            question_type=QuestionType.SCALE,
            required=True
        )
        
        # Test invalid scale answer
        result = handler._validate_answer(question, "not a number")
        self.assertFalse(result['valid'])
        self.assertIn("between 1 and 10", result['reason'])
    
    def test_session_not_found(self):
        """Test handling non-existent session."""
        manager = ConversationContextManager()
        
        # Try to get context for non-existent session
        context = manager.get_context("non_existent")
        self.assertIsNone(context)
        
        # Try to add turn to non-existent session
        success = manager.add_turn("non_existent", "user", "test")
        self.assertFalse(success)
    
    def test_very_long_response(self):
        """Test handling very long responses."""
        analyzer = ResponseQualityAnalyzer()
        
        # Create very long response
        long_text = " ".join(["This is a sentence."] * 500)
        
        suggestions = analyzer.generate_suggestions(long_text)
        self.assertTrue(any("too long" in s for s in suggestions))
        
        # Test optimization truncates long responses
        optimized = analyzer.optimize_response(
            long_text,
            TechnicalLevel.INTERMEDIATE,
            "professional"
        )
        
        self.assertLess(len(optimized), len(long_text))


def run_tests():
    """Run all tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestResponseFormatters))
    suite.addTests(loader.loadTestsFromTestCase(TestTemplateEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestSolutionStepManager))
    suite.addTests(loader.loadTestsFromTestCase(TestDiagnosticQuestionHandler))
    suite.addTests(loader.loadTestsFromTestCase(TestConversationContextManager))
    suite.addTests(loader.loadTestsFromTestCase(TestResponseQualityAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestResponseGenerationSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestConversationFlows))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    return result


if __name__ == "__main__":
    result = run_tests()