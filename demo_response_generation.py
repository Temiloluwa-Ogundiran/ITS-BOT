"""
Interactive demo of the Response Generation System for Helpdesk Chatbot.
Demonstrates various response types and conversation flows.
"""

import json
from datetime import datetime
from typing import Optional
import random

from response_generation import (
    ResponseGenerationSystem,
    ResponseType,
    TechnicalLevel,
    ResponseContext,
    ConversationState
)

from models import (
    KnowledgeArticle,
    SolutionStep,
    DiagnosticQuestion,
    QuestionType,
    SolutionStepType,
    DifficultyLevel
)


class ResponseGenerationDemo:
    """Interactive demo for the response generation system."""
    
    def __init__(self):
        """Initialize the demo."""
        self.system = ResponseGenerationSystem()
        self.session_id = f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.user_id = "demo_user"
        self.sample_articles = self._create_sample_articles()
        self.sample_questions = self._create_sample_questions()
        
        print("="*80)
        print("HELPDESK CHATBOT RESPONSE GENERATION SYSTEM DEMO")
        print("="*80)
        print(f"Session ID: {self.session_id}")
        print(f"User ID: {self.user_id}")
        print()
    
    def _create_sample_articles(self):
        """Create sample articles for demo."""
        return [
            KnowledgeArticle(
                article_id="demo_001",
                title="How to Reset Your Email Password",
                content="""If you've forgotten your email password, don't worry! 
                This guide will walk you through the password reset process step by step. 
                The process is secure and typically takes about 10 minutes to complete.""",
                category="Email",
                subcategory="Security",
                keywords=["password", "reset", "email", "forgot", "security"],
                symptoms=["Cannot login", "Forgot password", "Access denied"],
                difficulty_level=DifficultyLevel.EASY,
                estimated_time_minutes=10,
                success_rate=0.95,
                solution_steps=[
                    SolutionStep(
                        order=1,
                        title="Navigate to Email Login Page",
                        content="Open your web browser and go to your email provider's login page.",
                        step_type=SolutionStepType.INSTRUCTION,
                        estimated_time_minutes=1
                    ),
                    SolutionStep(
                        order=2,
                        title="Click 'Forgot Password'",
                        content="Look for the 'Forgot Password' or 'Can't access your account?' link below the login form and click it.",
                        step_type=SolutionStepType.INSTRUCTION,
                        estimated_time_minutes=1
                    ),
                    SolutionStep(
                        order=3,
                        title="Enter Your Email Address",
                        content="Type your email address in the provided field and click 'Continue' or 'Next'.",
                        step_type=SolutionStepType.INSTRUCTION,
                        estimated_time_minutes=2
                    ),
                    SolutionStep(
                        order=4,
                        title="Check Your Recovery Email",
                        content="Check your recovery email account for a password reset link. This may take a few minutes to arrive.",
                        step_type=SolutionStepType.VERIFICATION,
                        estimated_time_minutes=3
                    ),
                    SolutionStep(
                        order=5,
                        title="Create New Password",
                        content="Click the reset link and create a new, strong password. Make sure it's at least 8 characters with a mix of letters, numbers, and symbols.",
                        step_type=SolutionStepType.INSTRUCTION,
                        estimated_time_minutes=3
                    )
                ]
            ),
            KnowledgeArticle(
                article_id="demo_002",
                title="Troubleshooting Printer Connection Issues",
                content="""Having trouble getting your printer to work? This comprehensive guide 
                covers the most common printer connection problems and their solutions. 
                We'll help you identify and fix the issue quickly.""",
                category="Hardware",
                subcategory="Printer",
                keywords=["printer", "connection", "not printing", "offline"],
                symptoms=["Printer offline", "Cannot print", "Printer not found"],
                difficulty_level=DifficultyLevel.MEDIUM,
                estimated_time_minutes=20,
                success_rate=0.85,
                solution_steps=[
                    SolutionStep(
                        order=1,
                        title="Check Physical Connections",
                        content="Ensure the printer is properly connected via USB or network cable. Try unplugging and reconnecting.",
                        step_type=SolutionStepType.VERIFICATION,
                        estimated_time_minutes=3
                    ),
                    SolutionStep(
                        order=2,
                        title="Power Cycle the Printer",
                        content="Turn off the printer, wait 30 seconds, then turn it back on.",
                        step_type=SolutionStepType.TROUBLESHOOTING,
                        estimated_time_minutes=2
                    ),
                    SolutionStep(
                        order=3,
                        title="Check Printer Status",
                        content="Go to Settings > Devices > Printers & Scanners and check if your printer shows as 'Ready'.",
                        step_type=SolutionStepType.VERIFICATION,
                        estimated_time_minutes=2
                    )
                ]
            ),
            KnowledgeArticle(
                article_id="demo_003",
                title="Optimizing Computer Performance",
                content="""Is your computer running slowly? This guide provides advanced techniques 
                to optimize your system performance, including disk cleanup, startup optimization, 
                and memory management strategies.""",
                category="Software",
                subcategory="Performance",
                keywords=["slow", "performance", "optimization", "speed"],
                symptoms=["Computer slow", "System lag", "High CPU usage"],
                difficulty_level=DifficultyLevel.HARD,
                estimated_time_minutes=45,
                success_rate=0.75
            )
        ]
    
    def _create_sample_questions(self):
        """Create sample diagnostic questions."""
        return [
            DiagnosticQuestion(
                question="Is your computer connected to the internet?",
                question_type=QuestionType.YES_NO,
                help_text="Check if you can browse other websites or if the WiFi/Ethernet icon shows connected.",
                required=True
            ),
            DiagnosticQuestion(
                question="What type of error message are you seeing?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=[
                    "Connection timeout",
                    "Access denied",
                    "Page not found",
                    "No error message"
                ],
                required=True
            ),
            DiagnosticQuestion(
                question="When did this issue start occurring?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=[
                    "Today",
                    "Yesterday",
                    "This week",
                    "More than a week ago"
                ],
                required=False
            ),
            DiagnosticQuestion(
                question="On a scale of 1-10, how urgent is this issue?",
                question_type=QuestionType.SCALE,
                help_text="1 = Not urgent at all, 10 = Extremely urgent",
                required=True
            )
        ]
    
    def demo_article_response(self):
        """Demo full article response formatting."""
        print("\n" + "="*60)
        print("DEMO: Full Article Response")
        print("="*60)
        
        article = self.sample_articles[0]  # Email password reset
        
        # Create context with user info
        context = ResponseContext(
            user_name="John Smith",
            technical_level=TechnicalLevel.BEGINNER,
            software_version="Outlook 2019",
            operating_system="Windows 10"
        )
        
        # Generate response
        result = self.system.generate_response(
            response_type=ResponseType.ARTICLE_FULL,
            data=article,
            session_id=self.session_id,
            user_id=self.user_id
        )
        
        print("\n📄 Generated Response:")
        print("-"*40)
        print(result['response'])
        print("-"*40)
        
        print("\n📊 Quality Metrics:")
        metrics = result['quality_metrics']
        print(f"  • Quality Score: {metrics['quality_score']:.1f}/100")
        print(f"  • Readability: {metrics['readability_score']:.1f}")
        print(f"  • Word Count: {metrics['length_words']}")
        print(f"  • Technical Level: {metrics['technical_level'].value}")
        
        if metrics['suggestions']:
            print("\n💡 Improvement Suggestions:")
            for suggestion in metrics['suggestions']:
                print(f"  • {suggestion}")
    
    def demo_step_by_step_solution(self):
        """Demo step-by-step solution presentation."""
        print("\n" + "="*60)
        print("DEMO: Step-by-Step Solution")
        print("="*60)
        
        article = self.sample_articles[1]  # Printer troubleshooting
        
        print("\n🔧 Starting step-by-step solution for:", article.title)
        print(f"Total steps: {len(article.solution_steps)}")
        
        # Start solution
        response = self.system.step_manager.start_solution(
            session_id=self.session_id,
            article=article,
            mode="progressive"
        )
        
        print("\n📝 Step 1:")
        print("-"*40)
        print(response)
        
        # Simulate user completing step 1
        print("\n✅ User confirms: Step 1 completed successfully")
        response = self.system.step_manager.confirm_step_completion(
            session_id=self.session_id,
            success=True,
            user_feedback="Cable was loose, reconnected it"
        )
        
        print("\n📝 Step 2:")
        print("-"*40)
        print(response)
        
        # Simulate step 2 failure
        print("\n❌ User reports: Step 2 didn't work")
        response = self.system.step_manager.confirm_step_completion(
            session_id=self.session_id,
            success=False,
            user_feedback="Printer still not responding after power cycle"
        )
        
        print("\n🔄 Alternative approach:")
        print("-"*40)
        print(response)
    
    def demo_diagnostic_questions(self):
        """Demo diagnostic question flow."""
        print("\n" + "="*60)
        print("DEMO: Diagnostic Questions")
        print("="*60)
        
        print("\n🔍 Starting diagnostic session...")
        
        # Start diagnostic
        response = self.system.question_handler.start_diagnostic(
            session_id=f"{self.session_id}_diag",
            questions=self.sample_questions[:3],
            category="connectivity"
        )
        
        print("\n❓ Question 1:")
        print("-"*40)
        print(response)
        
        # Simulate user answer
        user_answer = "yes"
        print(f"\n👤 User answers: {user_answer}")
        
        response, route = self.system.question_handler.process_answer(
            f"{self.session_id}_diag",
            user_answer
        )
        
        print("\n❓ Question 2:")
        print("-"*40)
        print(response)
        
        # Simulate multiple choice answer
        user_answer = 2  # "Access denied"
        print(f"\n👤 User selects option: {user_answer}")
        
        response, route = self.system.question_handler.process_answer(
            f"{self.session_id}_diag",
            user_answer
        )
        
        print("\n❓ Question 3:")
        print("-"*40)
        print(response)
        
        # Complete diagnostic
        user_answer = 1  # "Today"
        print(f"\n👤 User selects option: {user_answer}")
        
        response, route = self.system.question_handler.process_answer(
            f"{self.session_id}_diag",
            user_answer
        )
        
        print("\n📋 Diagnostic Results:")
        print("-"*40)
        print(response)
    
    def demo_no_results_response(self):
        """Demo no results response with suggestions."""
        print("\n" + "="*60)
        print("DEMO: No Results Response")
        print("="*60)
        
        query = "quantum computer maintenance procedures"
        suggestions = [
            "Computer maintenance guide",
            "Hardware troubleshooting",
            "System optimization tips"
        ]
        
        print(f"\n🔍 User searched for: '{query}'")
        
        result = self.system.generate_response(
            response_type=ResponseType.NO_RESULTS,
            data={'query': query, 'suggestions': suggestions},
            session_id=self.session_id
        )
        
        print("\n📭 No Results Response:")
        print("-"*40)
        print(result['response'])
    
    def demo_escalation_response(self):
        """Demo escalation to human support."""
        print("\n" + "="*60)
        print("DEMO: Escalation Response")
        print("="*60)
        
        # Simulate a frustrated user scenario
        session = self.system.context_manager.start_session(
            f"{self.session_id}_escalate",
            self.user_id
        )
        
        session.context.current_emotion = "frustrated"
        session.context.response_count = 5
        session.failed_solution_attempts = 3
        session.context.preferences['issue_summary'] = "Printer won't work after trying everything"
        
        print("\n😤 User is frustrated after multiple failed attempts")
        
        # Check if escalation is needed
        should_escalate, reason = self.system.context_manager.should_escalate(
            f"{self.session_id}_escalate"
        )
        
        print(f"Should escalate: {should_escalate}")
        print(f"Reason: {reason}")
        
        if should_escalate:
            result = self.system.generate_response(
                response_type=ResponseType.ESCALATION,
                data={
                    'reason': reason,
                    'ticket_number': f"HELP-{random.randint(10000, 99999)}",
                    'wait_time': random.randint(2, 10)
                },
                session_id=f"{self.session_id}_escalate"
            )
            
            print("\n🎧 Escalation Response:")
            print("-"*40)
            print(result['response'])
    
    def demo_conversation_context(self):
        """Demo conversation context management."""
        print("\n" + "="*60)
        print("DEMO: Conversation Context Management")
        print("="*60)
        
        conv_session_id = f"{self.session_id}_context"
        
        # Start a conversation
        session = self.system.context_manager.start_session(
            conv_session_id,
            self.user_id
        )
        
        print("\n💬 Simulating conversation flow...")
        
        # User message 1 - Beginner level
        self.system.context_manager.add_turn(
            conv_session_id,
            "user",
            "Hi, I can't find the button to save my document. Where do I click?"
        )
        
        context = self.system.context_manager.get_context(conv_session_id)
        print(f"\n📊 After message 1 - Technical level: {context.technical_level.value}")
        
        # User message 2 - Shows frustration
        self.system.context_manager.add_turn(
            conv_session_id,
            "user",
            "This is so frustrating! I've been trying for an hour!"
        )
        
        context = self.system.context_manager.get_context(conv_session_id)
        print(f"📊 After message 2 - Emotion: {context.current_emotion}")
        
        # User message 3 - Expert level
        self.system.context_manager.add_turn(
            conv_session_id,
            "user",
            "Actually, I need to configure the registry settings for auto-save functionality"
        )
        
        context = self.system.context_manager.get_context(conv_session_id)
        print(f"📊 After message 3 - Technical level: {context.technical_level.value}")
        
        # Show conversation history
        history = self.system.context_manager.get_history(conv_session_id)
        print(f"\n📜 Conversation history: {len(history)} turns")
        for i, turn in enumerate(history, 1):
            print(f"  {i}. [{turn.speaker}]: {turn.message[:50]}...")
    
    def demo_response_quality_analysis(self):
        """Demo response quality analysis and optimization."""
        print("\n" + "="*60)
        print("DEMO: Response Quality Analysis")
        print("="*60)
        
        # Test different quality responses
        responses = [
            ("Poor", "Fix it."),
            ("Average", "To resolve this issue, please restart your computer and check if the problem persists."),
            ("Good", """**Solution for Your Issue:**

I understand you're experiencing difficulties. Let me help you resolve this step by step:

1. **First Step**: Check your system settings
   - Navigate to Control Panel
   - Open System Settings
   
2. **Second Step**: Verify the configuration
   - Ensure all options are correctly set
   - Save any changes made

This should resolve your problem. The process typically takes 5-10 minutes.

Let me know if you need any clarification or further assistance!""")
        ]
        
        analyzer = self.system.quality_analyzer
        
        for quality_type, response in responses:
            print(f"\n📝 {quality_type} Quality Response:")
            print("-"*40)
            print(response[:100] + "..." if len(response) > 100 else response)
            
            metrics = analyzer.analyze_response(response)
            print(f"\n📊 Analysis:")
            print(f"  • Quality Score: {metrics['quality_score']:.1f}/100")
            print(f"  • Readability: {metrics['readability_score']:.1f}")
            print(f"  • Word Count: {metrics['length_words']}")
            
            if metrics['suggestions']:
                print("  • Suggestions:")
                for suggestion in metrics['suggestions'][:2]:
                    print(f"    - {suggestion}")
        
        # Demo optimization
        print("\n🔧 Response Optimization Demo:")
        technical_response = "Execute the configuration protocol to initialize the network interface parameters."
        
        print(f"\nOriginal (Expert): {technical_response}")
        
        optimized = analyzer.optimize_response(
            technical_response,
            TechnicalLevel.BEGINNER,
            "friendly"
        )
        
        print(f"Optimized (Beginner): {optimized}")
    
    def demo_template_system(self):
        """Demo template system with variable substitution."""
        print("\n" + "="*60)
        print("DEMO: Template System")
        print("="*60)
        
        context = ResponseContext(
            user_name="Alice Johnson",
            software_version="Gmail",
            operating_system="Windows 11"
        )
        
        variables = {
            'solution_content': """
1. Go to Gmail settings (gear icon → Settings)
2. Click on 'Accounts and Import' tab
3. Find 'Change password' section
4. Follow the on-screen instructions""",
            'time_estimate': '5-7',
            'additional_notes': 'Remember to use a strong, unique password',
            'acknowledgment': "I see you're having trouble accessing your email account"
        }
        
        print("\n📄 Using Email Password Reset Template:")
        print("-"*40)
        
        rendered = self.system.template_engine.render_template(
            category='email',
            template_type='password_reset',
            variables=variables,
            context=context
        )
        
        print(rendered)
        
        # Demo conditional content
        print("\n🔀 Conditional Content Demo:")
        print("-"*40)
        
        base = "Here's how to reset your password."
        conditions = {
            'has_2fa': True,
            'is_admin': False,
            'first_time': True
        }
        conditional = {
            'has_2fa': "📱 Note: You'll need your 2FA device ready.",
            'is_admin': "⚠️ Admin privileges required for this action.",
            'first_time': "💡 Tip: Write down your new password in a secure location."
        }
        
        result = self.system.template_engine.add_conditional_content(
            base, conditions, conditional
        )
        
        print(result)
    
    def run_all_demos(self):
        """Run all demonstration scenarios."""
        demos = [
            ("Article Response", self.demo_article_response),
            ("Step-by-Step Solution", self.demo_step_by_step_solution),
            ("Diagnostic Questions", self.demo_diagnostic_questions),
            ("No Results Response", self.demo_no_results_response),
            ("Escalation Response", self.demo_escalation_response),
            ("Conversation Context", self.demo_conversation_context),
            ("Response Quality Analysis", self.demo_response_quality_analysis),
            ("Template System", self.demo_template_system)
        ]
        
        print("\n" + "="*80)
        print("RUNNING ALL DEMONSTRATIONS")
        print("="*80)
        
        for i, (name, demo_func) in enumerate(demos, 1):
            print(f"\n[{i}/{len(demos)}] {name}")
            try:
                demo_func()
                print("\n✅ Demo completed successfully")
            except Exception as e:
                print(f"\n❌ Demo failed: {str(e)}")
        
        print("\n" + "="*80)
        print("ALL DEMONSTRATIONS COMPLETE")
        print("="*80)
        
        # Print session summary
        print("\n📊 Session Summary:")
        print(f"  • Session ID: {self.session_id}")
        print(f"  • User ID: {self.user_id}")
        print(f"  • Active sessions: {len(self.system.context_manager.sessions)}")
        print(f"  • Active solutions: {len(self.system.step_manager.active_solutions)}")
        print(f"  • Active diagnostics: {len(self.system.question_handler.active_diagnostics)}")


def main():
    """Main function to run the demo."""
    print("\n🤖 Welcome to the Response Generation System Demo!\n")
    
    demo = ResponseGenerationDemo()
    
    while True:
        print("\n" + "="*60)
        print("SELECT DEMO OPTION:")
        print("="*60)
        print("1. Full Article Response")
        print("2. Step-by-Step Solution")
        print("3. Diagnostic Questions")
        print("4. No Results Response")
        print("5. Escalation Response")
        print("6. Conversation Context")
        print("7. Response Quality Analysis")
        print("8. Template System")
        print("9. Run All Demos")
        print("0. Exit")
        print("-"*60)
        
        choice = input("\nEnter your choice (0-9): ").strip()
        
        if choice == "0":
            print("\n👋 Thank you for using the Response Generation System Demo!")
            break
        elif choice == "1":
            demo.demo_article_response()
        elif choice == "2":
            demo.demo_step_by_step_solution()
        elif choice == "3":
            demo.demo_diagnostic_questions()
        elif choice == "4":
            demo.demo_no_results_response()
        elif choice == "5":
            demo.demo_escalation_response()
        elif choice == "6":
            demo.demo_conversation_context()
        elif choice == "7":
            demo.demo_response_quality_analysis()
        elif choice == "8":
            demo.demo_template_system()
        elif choice == "9":
            demo.run_all_demos()
        else:
            print("\n❌ Invalid choice. Please enter a number between 0 and 9.")
        
        if choice != "0":
            input("\n\nPress Enter to continue...")


if __name__ == "__main__":
    main()