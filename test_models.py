#!/usr/bin/env python3
"""
Test file to demonstrate the usage of models and utilities.
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


def test_models():
    """Test the Pydantic models."""
    print("🧪 Testing Pydantic Models")
    print("=" * 40)
    
    # Test SolutionStep
    print("\n1. Testing SolutionStep model:")
    try:
        step = SolutionStep(
            order=1,
            title="Check Physical Connections",
            content="Ensure the printer is powered on and properly connected",
            step_type=SolutionStepType.INSTRUCTION,
            estimated_time_minutes=2
        )
        print(f"✅ SolutionStep created: {step.title}")
        print(f"   Type: {step.step_type.value}")
        print(f"   Time: {step.estimated_time_minutes} minutes")
    except Exception as e:
        print(f"❌ SolutionStep creation failed: {e}")
    
    # Test DiagnosticQuestion
    print("\n2. Testing DiagnosticQuestion model:")
    try:
        question = DiagnosticQuestion(
            question="Do you have access to your recovery email?",
            question_type=QuestionType.YES_NO,
            required=True,
            help_text="You'll need access to at least one recovery method"
        )
        print(f"✅ DiagnosticQuestion created: {question.question}")
        print(f"   Type: {question.question_type.value}")
        print(f"   Required: {question.required}")
    except Exception as e:
        print(f"❌ DiagnosticQuestion creation failed: {e}")
    
    # Test KnowledgeArticle
    print("\n3. Testing KnowledgeArticle model:")
    try:
        article = KnowledgeArticle(
            title="How to Reset Your Email Password",
            content="If you've forgotten your email password, follow these steps...",
            category="Email",
            subcategory="Password Management",
            difficulty_level=DifficultyLevel.EASY,
            keywords=["password reset", "email password"],
            symptoms=["Cannot log into email account"],
            solution_steps=[step],
            diagnostic_questions=[question],
            estimated_time_minutes=10,
            success_rate=0.95
        )
        print(f"✅ KnowledgeArticle created: {article.title}")
        print(f"   Category: {article.category}")
        print(f"   Difficulty: {article.difficulty_level.value}")
        print(f"   Time: {article.estimated_time_minutes} minutes")
        print(f"   Success Rate: {article.success_rate:.1%}")
        
        # Test methods
        slug = article.generate_slug()
        print(f"   Slug: {slug}")
        
        summary = article.get_summary(max_length=50)
        print(f"   Summary: {summary}")
        
    except Exception as e:
        print(f"❌ KnowledgeArticle creation failed: {e}")


def test_utilities():
    """Test the utility functions."""
    print("\n🔧 Testing Utility Functions")
    print("=" * 40)
    
    # Test TextProcessor
    print("\n1. Testing TextProcessor:")
    sample_text = "The printer is NOT working and I can't print anything!"
    
    cleaned = TextProcessor.clean_text(sample_text)
    print(f"   Original: {sample_text}")
    print(f"   Cleaned: {cleaned}")
    
    keywords = TextProcessor.extract_keywords(sample_text, max_keywords=5)
    print(f"   Keywords: {keywords}")
    
    symptoms = TextProcessor.extract_symptoms(sample_text)
    print(f"   Symptoms: {symptoms}")
    
    slug = TextProcessor.generate_slug(sample_text, max_length=30)
    print(f"   Slug: {slug}")
    
    # Test DataValidator
    print("\n2. Testing DataValidator:")
    test_data = {
        "title": "Test Article",
        "content": "This is a test article with sufficient content.",
        "category": "Test",
        "difficulty_level": "easy",
        "estimated_time_minutes": 15
    }
    
    is_valid, errors = DataValidator.validate_article_data(test_data)
    if is_valid:
        print("   ✅ Article data is valid")
    else:
        print("   ❌ Article data validation failed:")
        for error in errors:
            print(f"      - {error}")
    
    # Test DataConverter
    print("\n3. Testing DataConverter:")
    raw_data = {
        "title": "Test Article",
        "content": "Test content",
        "category": "Test",
        "difficulty_level": "medium",
        "keywords": "test, article, example",
        "is_active": "true",
        "estimated_time_minutes": "20"
    }
    
    converted = DataConverter.dict_to_article(raw_data)
    print(f"   Converted keywords: {converted['keywords']}")
    print(f"   Converted is_active: {converted['is_active']}")
    print(f"   Converted time: {converted['estimated_time_minutes']}")
    
    # Test IDGenerator
    print("\n4. Testing IDGenerator:")
    article_id = IDGenerator.generate_article_id()
    uuid_str = IDGenerator.generate_uuid()
    session_id = IDGenerator.generate_session_id()
    
    print(f"   Article ID: {article_id}")
    print(f"   UUID: {uuid_str}")
    print(f"   Session ID: {session_id}")
    
    # Test QueryParser
    print("\n5. Testing QueryParser:")
    test_query = "I can't log into my email account, it says password is wrong"
    
    intent, confidence = QueryParser.extract_intent(test_query)
    print(f"   Query: {test_query}")
    print(f"   Intent: {intent}")
    print(f"   Confidence: {confidence:.2f}")
    
    entities = QueryParser.extract_entities(test_query)
    print(f"   Categories: {entities['categories']}")
    print(f"   Symptoms: {entities['symptoms']}")
    print(f"   Keywords: {entities['keywords']}")


def test_configuration():
    """Test the configuration management."""
    print("\n⚙️ Testing Configuration Management")
    print("=" * 40)
    
    # Test development environment
    print("\n1. Testing Development Environment:")
    dev_config = ConfigManager(Environment.DEVELOPMENT)
    
    es_config = dev_config.get_elasticsearch_config()
    print(f"   Elasticsearch Host: {es_config['hosts'][0]['host']}")
    print(f"   Elasticsearch Port: {es_config['hosts'][0]['port']}")
    print(f"   Use SSL: {es_config['use_ssl']}")
    
    index_config = dev_config.get_index_config()
    print(f"   Index Name: {index_config['name']}")
    print(f"   Shards: {index_config['number_of_shards']}")
    print(f"   Replicas: {index_config['number_of_replicas']}")
    
    # Test production environment
    print("\n2. Testing Production Environment:")
    prod_config = ConfigManager(Environment.PRODUCTION)
    
    prod_es_config = prod_config.get_elasticsearch_config()
    print(f"   Elasticsearch Timeout: {prod_es_config['timeout']}")
    print(f"   Max Retries: {prod_es_config['max_retries']}")
    
    prod_index_config = prod_config.get_index_config()
    print(f"   Production Shards: {prod_index_config['number_of_shards']}")
    print(f"   Production Replicas: {prod_index_config['number_of_replicas']}")


def test_integration():
    """Test integration between components."""
    print("\n🔗 Testing Integration")
    print("=" * 40)
    
    # Create a complete article using all components
    print("\n1. Creating a complete article:")
    
    try:
        # Create solution steps
        steps = [
            SolutionStep(
                order=1,
                title="Check Physical Connections",
                content="Ensure the printer is powered on and connected",
                step_type=SolutionStepType.INSTRUCTION,
                estimated_time_minutes=2
            ),
            SolutionStep(
                order=2,
                title="Verify Network Connection",
                content="Check if printer is on the same network",
                step_type=SolutionStepType.VERIFICATION,
                estimated_time_minutes=3
            )
        ]
        
        # Create diagnostic questions
        questions = [
            DiagnosticQuestion(
                question="Is the printer powered on?",
                question_type=QuestionType.YES_NO,
                required=True
            ),
            DiagnosticQuestion(
                question="Is this a network printer?",
                question_type=QuestionType.YES_NO,
                required=True
            )
        ]
        
        # Create the article
        article = KnowledgeArticle(
            title="Fixing Printer Connection Issues",
            content="Step-by-step guide to resolve printer connectivity problems...",
            category="Hardware",
            subcategory="Printers",
            difficulty_level=DifficultyLevel.MEDIUM,
            keywords=["printer", "connection", "network", "troubleshooting"],
            symptoms=["Printer shows as offline", "Cannot print from computer"],
            solution_steps=steps,
            diagnostic_questions=questions,
            estimated_time_minutes=20,
            success_rate=0.85
        )
        
        print(f"✅ Complete article created: {article.title}")
        print(f"   Steps: {len(article.solution_steps)}")
        print(f"   Questions: {len(article.diagnostic_questions)}")
        print(f"   Keywords: {article.keywords}")
        
        # Test data conversion
        print("\n2. Testing data conversion:")
        
        # Convert to Elasticsearch format
        es_doc = DataConverter.article_to_elasticsearch(article.dict())
        print(f"   ✅ Converted to Elasticsearch format")
        print(f"   ES document keys: {list(es_doc.keys())}")
        
        # Test validation
        is_valid, errors = DataValidator.validate_article_data(article.dict())
        if is_valid:
            print(f"   ✅ Article validation passed")
        else:
            print(f"   ❌ Article validation failed: {errors}")
        
        # Test text processing
        print("\n3. Testing text processing:")
        
        # Extract keywords from content
        content_keywords = TextProcessor.extract_keywords(article.content, max_keywords=5)
        print(f"   Content keywords: {content_keywords}")
        
        # Generate slug
        slug = article.generate_slug()
        print(f"   Generated slug: {slug}")
        
        # Test query parsing
        print("\n4. Testing query parsing:")
        
        test_queries = [
            "My printer is not working",
            "I can't log into my email",
            "The internet is very slow"
        ]
        
        for query in test_queries:
            intent, confidence = QueryParser.extract_intent(query)
            print(f"   Query: '{query}' -> Intent: {intent} (confidence: {confidence:.2f})")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")


def main():
    """Run all tests."""
    print("🚀 Helpdesk Knowledge Base System - Model and Utility Tests")
    print("=" * 70)
    
    try:
        test_models()
        test_utilities()
        test_configuration()
        test_integration()
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
