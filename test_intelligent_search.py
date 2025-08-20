#!/usr/bin/env python3
"""
Comprehensive Tests for Intelligent Search System
Tests query preprocessing, Elasticsearch query building, result processing, and analytics.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime, timedelta

from intelligent_search import (
    QueryPreprocessor, ElasticsearchQueryBuilder, SearchResultProcessor,
    SearchAnalytics, IntelligentSearchSystem, SearchQuery, SearchResult
)
from models import DifficultyLevel


class TestQueryPreprocessor(unittest.TestCase):
    """Test the QueryPreprocessor class."""
    
    def setUp(self):
        self.preprocessor = QueryPreprocessor()
        
    def test_intent_detection_problem(self):
        """Test intent detection for problem-related queries."""
        query = "How to fix printer error"
        search_query = self.preprocessor.preprocess_query(query)
        self.assertEqual(search_query.intent, "problem")
        self.assertGreater(search_query.confidence, 0.6)
        
    def test_intent_detection_question(self):
        """Test intent detection for question-related queries."""
        query = "What is the difference between RAM and ROM?"
        search_query = self.preprocessor.preprocess_query(query)
        self.assertEqual(search_query.intent, "question")
        self.assertGreater(search_query.confidence, 0.6)
        
    def test_entity_extraction_software(self):
        """Test entity extraction for software names."""
        query = "How to install Windows 10 and Office 365"
        search_query = self.preprocessor.preprocess_query(query)
        
        software_entities = [e for e in search_query.entities if e['type'] == 'software']
        self.assertGreater(len(software_entities), 0)
        
    def test_filter_processing_valid(self):
        """Test processing of valid filters."""
        filters = {
            'category': 'Email',
            'difficulty': 'easy',
            'max_time': 30,
            'min_success_rate': 0.8
        }
        
        search_query = self.preprocessor.preprocess_query("test query", filters)
        self.assertEqual(search_query.filters['category'], 'Email')
        self.assertEqual(search_query.filters['difficulty'], 'easy')


class TestElasticsearchQueryBuilder(unittest.TestCase):
    """Test the ElasticsearchQueryBuilder class."""
    
    def setUp(self):
        self.mock_es_client = Mock()
        self.query_builder = ElasticsearchQueryBuilder(self.mock_es_client)
        
    def test_field_boosting_configuration(self):
        """Test that field boosting is properly configured."""
        expected_boosts = {
            'title': 3.0,
            'keywords': 2.5,
            'symptoms': 2.0,
            'content': 1.0,
            'category': 1.5,
            'subcategory': 1.3
        }
        
        self.assertEqual(self.query_builder.field_boosts, expected_boosts)
        
    def test_build_search_query_structure(self):
        """Test that search query has proper structure."""
        search_query = SearchQuery(
            original_query="test query",
            cleaned_query="test query",
            intent="general",
            entities=[],
            expanded_terms=["test query"],
            filters={},
            confidence=0.5
        )
        
        es_query = self.query_builder.build_search_query(search_query)
        self.assertIsNotNone(es_query)


class TestSearchResultProcessor(unittest.TestCase):
    """Test the SearchResultProcessor class."""
    
    def setUp(self):
        self.mock_es_client = Mock()
        self.processor = SearchResultProcessor(self.mock_es_client)
        
    def test_process_search_results_structure(self):
        """Test processing of search results structure."""
        mock_response = {
            'hits': {
                'total': {'value': 1},
                'hits': [
                    {
                        '_id': 'doc1',
                        '_score': 0.95,
                        '_source': {
                            'title': 'Test Article',
                            'content': 'This is test content',
                            'category': 'Test',
                            'subcategory': 'Unit',
                            'difficulty_level': 'easy',
                            'estimated_time_minutes': 15,
                            'success_rate': 0.9,
                            'view_count': 10
                        }
                    }
                ]
            },
            'aggregations': {},
            'took': 15
        }
        
        results, metadata = self.processor.process_search_results(mock_response, "test query")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(metadata['total_hits'], 1)
        self.assertEqual(metadata['processing_time'], 15)


class TestSearchAnalytics(unittest.TestCase):
    """Test the SearchAnalytics class."""
    
    def setUp(self):
        self.mock_es_client = Mock()
        self.analytics = SearchAnalytics(self.mock_es_client)
        
    def test_track_search(self):
        """Test tracking of search queries."""
        search_query = SearchQuery(
            original_query="test query",
            cleaned_query="test query",
            intent="general",
            entities=[],
            expanded_terms=["test query"],
            filters={},
            confidence=0.5
        )
        
        self.mock_es_client.index.return_value = {'_id': 'analytics1'}
        
        self.analytics.track_search(search_query, 5, 0.15, ['category'])
        
        self.mock_es_client.index.assert_called_once()


class TestIntelligentSearchSystem(unittest.TestCase):
    """Test the main IntelligentSearchSystem class."""
    
    def setUp(self):
        self.mock_es_client = Mock()
        self.search_system = IntelligentSearchSystem(self.mock_es_client)
        
    def test_system_initialization(self):
        """Test that all components are properly initialized."""
        self.assertIsNotNone(self.search_system.preprocessor)
        self.assertIsNotNone(self.search_system.query_builder)
        self.assertIsNotNone(self.search_system.result_processor)
        self.assertIsNotNone(self.search_system.analytics)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def setUp(self):
        self.mock_es_client = Mock()
        self.search_system = IntelligentSearchSystem(self.mock_es_client)
        
    def test_empty_query(self):
        """Test handling of empty queries."""
        search_query = self.search_system.preprocessor.preprocess_query("")
        
        self.assertEqual(search_query.intent, "general")
        self.assertEqual(search_query.confidence, 0.5)
        self.assertEqual(len(search_query.entities), 0)
        
    def test_special_characters_query(self):
        """Test handling of queries with special characters."""
        special_query = "How to fix C:\\Windows\\System32 error?"
        
        search_query = self.search_system.preprocessor.preprocess_query(special_query)
        
        self.assertIsNotNone(search_query.intent)
        self.assertGreater(search_query.confidence, 0.0)


def main():
    """Run all tests."""
    print("🧪 Intelligent Search System - Comprehensive Testing")
    print("=" * 70)
    
    # Run unit tests
    unittest.main(verbosity=2, exit=False)
    
    print("\n🎉 All tests completed!")


if __name__ == "__main__":
    main()
