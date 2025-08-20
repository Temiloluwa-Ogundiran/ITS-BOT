#!/usr/bin/env python3
"""
Demo script for the Helpdesk Knowledge Base System.
This script demonstrates the core functionality of the system.
"""

import json
from datetime import datetime
from models import (
    KnowledgeArticle, SolutionStep, DiagnosticQuestion,
    DifficultyLevel, QuestionType, SolutionStepType
)
from utils import (
    TextProcessor, DataValidator, DataConverter,
    IDGenerator, QueryParser
)
from config_manager import ConfigManager, Environment


def create_sample_article():
    """Create a sample helpdesk article."""
    print("📝 Creating a sample helpdesk article...")
    
    # Create solution steps
    steps = [
        SolutionStep(
            order=1,
            title="Check Internet Connection",
            content="First, verify that your computer has a working internet connection. Try opening a website in your browser.",
            step_type=SolutionStepType.INSTRUCTION,
            estimated_time_minutes=2
        ),
        SolutionStep(
            order=2,
            title="Verify Email Server Status",
            content="Check if the email server is operational. You can usually find this information on the email provider's status page.",
            step_type=SolutionStepType.VERIFICATION,
            estimated_time_minutes=3
        ),
        SolutionStep(
            order=3,
            title="Check Email Settings",
            content="Verify that your email client settings match the recommended configuration for your email provider.",
            step_type=SolutionStepType.INSTRUCTION,
            estimated_time_minutes=5
        ),
        SolutionStep(
            order=4,
            title="Test with Web Interface",
            content="Try accessing your email through the web interface to isolate whether the issue is with the client or the server.",
            step_type=SolutionStepType.TROUBLESHOOTING,
            estimated_time_minutes=4
        )
    ]
    
    # Create diagnostic questions
    questions = [
        DiagnosticQuestion(
            question="Are you able to access other websites?",
            question_type=QuestionType.YES_NO,
            required=True,
            help_text="This helps determine if it's a general internet issue or specific to email."
        ),
        DiagnosticQuestion(
            question="What email client are you using?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=["Outlook", "Thunderbird", "Apple Mail", "Web Browser", "Mobile App"],
            required=True
        ),
        DiagnosticQuestion(
            question="When did this problem start?",
            question_type=QuestionType.TEXT,
            required=False,
            help_text="Approximate date and time when you first noticed the issue."
        )
    ]
    
    # Create the article
    article = KnowledgeArticle(
        title="Troubleshooting Email Connection Issues",
        content="This guide helps you resolve common email connection problems. Follow the steps in order and answer the diagnostic questions to identify the root cause of your issue.",
        category="Email",
        subcategory="Connection Issues",
        difficulty_level=DifficultyLevel.MEDIUM,
        keywords=["email", "connection", "troubleshooting", "internet", "server"],
        symptoms=[
            "Cannot connect to email server",
            "Email client shows connection error",
            "Unable to send or receive emails",
            "Connection timeout errors"
        ],
        solution_steps=steps,
        diagnostic_questions=questions,
        estimated_time_minutes=20,
        success_rate=0.88
    )
    
    print(f"✅ Article created: {article.title}")
    print(f"   Category: {article.category} > {article.subcategory}")
    print(f"   Difficulty: {article.difficulty_level.value}")
    print(f"   Estimated time: {article.estimated_time_minutes} minutes")
    print(f"   Success rate: {article.success_rate:.1%}")
    print(f"   Solution steps: {len(article.solution_steps)}")
    print(f"   Diagnostic questions: {len(article.diagnostic_questions)}")
    
    return article


def demonstrate_text_processing():
    """Demonstrate text processing capabilities."""
    print("\n🔤 Demonstrating Text Processing...")
    
    # Sample user query
    user_query = "I can't connect to my email and it's giving me a connection timeout error"
    
    print(f"User Query: '{user_query}'")
    
    # Clean the text
    cleaned_text = TextProcessor.clean_text(user_query)
    print(f"Cleaned Text: '{cleaned_text}'")
    
    # Extract keywords
    keywords = TextProcessor.extract_keywords(user_query, max_keywords=5)
    print(f"Extracted Keywords: {keywords}")
    
    # Extract symptoms
    symptoms = TextProcessor.extract_symptoms(user_query)
    print(f"Extracted Symptoms: {symptoms}")
    
    # Generate slug
    slug = TextProcessor.generate_slug(user_query, max_length=40)
    print(f"Generated Slug: {slug}")
    
    # Expand synonyms
    expanded_keywords = TextProcessor.expand_synonyms(keywords)
    print(f"Expanded Keywords: {expanded_keywords}")


def demonstrate_query_parsing():
    """Demonstrate query parsing capabilities."""
    print("\n🔍 Demonstrating Query Parsing...")
    
    test_queries = [
        "My printer won't print anything",
        "I forgot my email password",
        "The internet is very slow today",
        "How do I install new software?",
        "My computer keeps freezing"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        
        # Extract intent
        intent, confidence = QueryParser.extract_intent(query)
        print(f"  Intent: {intent} (confidence: {confidence:.2f})")
        
        # Extract entities
        entities = QueryParser.extract_entities(query)
        print(f"  Categories: {entities['categories']}")
        print(f"  Symptoms: {entities['symptoms']}")
        print(f"  Keywords: {entities['keywords']}")


def demonstrate_data_validation():
    """Demonstrate data validation capabilities."""
    print("\n✅ Demonstrating Data Validation...")
    
    # Valid article data
    valid_data = {
        "title": "How to Reset Your Password",
        "content": "This guide explains how to reset your password if you've forgotten it.",
        "category": "Security",
        "subcategory": "Password Management",
        "difficulty_level": "easy",
        "keywords": ["password", "reset", "security"],
        "symptoms": ["Cannot log into account"],
        "estimated_time_minutes": 15,
        "success_rate": 0.95
    }
    
    print("Testing valid article data...")
    is_valid, errors = DataValidator.validate_article_data(valid_data)
    if is_valid:
        print("  ✅ Data is valid")
    else:
        print("  ❌ Validation failed:")
        for error in errors:
            print(f"    - {error}")
    
    # Invalid article data
    invalid_data = {
        "title": "",  # Empty title
        "content": "Short",  # Too short content
        "difficulty_level": "super_hard",  # Invalid difficulty
        "estimated_time_minutes": -5,  # Negative time
        "success_rate": 1.5  # Invalid success rate
    }
    
    print("\nTesting invalid article data...")
    is_valid, errors = DataValidator.validate_article_data(invalid_data)
    if is_valid:
        print("  ✅ Data is valid")
    else:
        print("  ❌ Validation failed:")
        for error in errors:
            print(f"    - {error}")


def demonstrate_data_conversion():
    """Demonstrate data conversion capabilities."""
    print("\n🔄 Demonstrating Data Conversion...")
    
    # Raw data (as might come from a form or API)
    raw_data = {
        "title": "Fix Internet Connection",
        "content": "Steps to resolve internet connectivity issues",
        "category": "Network",
        "difficulty_level": "medium",
        "keywords": "internet, connection, network, troubleshooting",
        "symptoms": "No internet access, slow connection",
        "is_active": "true",
        "estimated_time_minutes": "25",
        "success_rate": "0.82"
    }
    
    print("Raw data:")
    for key, value in raw_data.items():
        print(f"  {key}: {value} (type: {type(value).__name__})")
    
    # Convert to standardized format
    print("\nConverting to standardized format...")
    standardized = DataConverter.dict_to_article(raw_data)
    
    print("Standardized data:")
    for key, value in standardized.items():
        if key in raw_data:
            print(f"  {key}: {value} (type: {type(value).__name__})")
    
    # Convert to Elasticsearch format
    print("\nConverting to Elasticsearch format...")
    es_doc = DataConverter.article_to_elasticsearch(standardized)
    
    print("Elasticsearch document keys:")
    for key in es_doc.keys():
        print(f"  - {key}")


def demonstrate_configuration():
    """Demonstrate configuration management."""
    print("\n⚙️ Demonstrating Configuration Management...")
    
    # Development environment
    print("Development Environment:")
    dev_config = ConfigManager(Environment.DEVELOPMENT)
    
    es_config = dev_config.get_elasticsearch_config()
    print(f"  Elasticsearch: {es_config['hosts'][0]['host']}:{es_config['hosts'][0]['port']}")
    print(f"  SSL: {es_config['use_ssl']}")
    print(f"  Timeout: {es_config['timeout']}s")
    
    index_config = dev_config.get_index_config()
    print(f"  Index: {index_config['name']}")
    print(f"  Shards: {index_config['number_of_shards']}")
    print(f"  Replicas: {index_config['number_of_replicas']}")
    
    # Production environment
    print("\nProduction Environment:")
    prod_config = ConfigManager(Environment.PRODUCTION)
    
    prod_es_config = prod_config.get_elasticsearch_config()
    print(f"  Timeout: {prod_es_config['timeout']}s")
    print(f"  Max Retries: {prod_es_config['max_retries']}")
    
    prod_index_config = prod_config.get_index_config()
    print(f"  Shards: {prod_index_config['number_of_shards']}")
    print(f"  Replicas: {prod_index_config['number_of_replicas']}")


def demonstrate_id_generation():
    """Demonstrate ID generation capabilities."""
    print("\n🆔 Demonstrating ID Generation...")
    
    # Generate various types of IDs
    article_id = IDGenerator.generate_article_id()
    uuid_str = IDGenerator.generate_uuid()
    session_id = IDGenerator.generate_session_id()
    
    print(f"Article ID: {article_id}")
    print(f"UUID: {uuid_str}")
    print(f"Session ID: {session_id}")
    
    # Generate slugs from titles
    titles = [
        "How to Fix Printer Issues",
        "Email Password Reset Guide",
        "Internet Connection Troubleshooting"
    ]
    
    print("\nGenerating slugs from titles:")
    for title in titles:
        slug = IDGenerator.generate_slug_from_title(title)
        print(f"  '{title}' -> '{slug}'")


def main():
    """Run the main demonstration."""
    print("🚀 Helpdesk Knowledge Base System - Demonstration")
    print("=" * 60)
    
    try:
        # Create a sample article
        article = create_sample_article()
        
        # Demonstrate various capabilities
        demonstrate_text_processing()
        demonstrate_query_parsing()
        demonstrate_data_validation()
        demonstrate_data_conversion()
        demonstrate_configuration()
        demonstrate_id_generation()
        
        print("\n🎉 Demonstration completed successfully!")
        print("\nThe system is now ready to:")
        print("  • Create and manage helpdesk articles")
        print("  • Process and analyze user queries")
        print("  • Validate and convert data formats")
        print("  • Manage configuration for different environments")
        print("  • Generate unique identifiers and slugs")
        
    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
