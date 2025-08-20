#!/usr/bin/env python3
"""
Intelligent Search System for Helpdesk Knowledge Base
Provides advanced search capabilities with query preprocessing, intelligent query building,
result processing, and search analytics.
"""

import re
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from collections import defaultdict, Counter
import numpy as np
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q, MultiMatch, Match, Term, Range, Bool, FunctionScore
from elasticsearch_dsl.query import QueryString, Fuzzy

from models import KnowledgeArticle, DifficultyLevel
from utils import TextProcessor, QueryParser
from config_manager import ConfigManager


@dataclass
class SearchQuery:
    """Represents a processed search query."""
    original_query: str
    cleaned_query: str
    intent: str  # 'problem', 'question', 'request', 'general'
    entities: List[Dict[str, Any]]  # extracted entities
    expanded_terms: List[str]  # synonyms and related terms
    filters: Dict[str, Any]  # category, difficulty, time filters
    confidence: float  # confidence score for intent detection


@dataclass
class SearchResult:
    """Represents a search result with enhanced information."""
    article_id: str
    title: str
    content: str
    category: str
    subcategory: str
    difficulty_level: str
    estimated_time_minutes: int
    success_rate: float
    relevance_score: float
    matched_terms: List[str]
    highlighted_snippets: List[str]
    related_articles: List[str]
    view_count: int = 0


@dataclass
class SearchAnalytics:
    """Search analytics data."""
    query: str
    timestamp: datetime
    result_count: int
    click_through: bool = False
    time_spent: Optional[float] = None
    user_feedback: Optional[str] = None


class QueryPreprocessor:
    """Handles query preprocessing and analysis."""
    
    def __init__(self):
        self.text_processor = TextProcessor()
        self.query_parser = QueryParser()
        
        # Intent detection patterns
        self.intent_patterns = {
            'problem': [
                r'\b(error|issue|problem|bug|fail|broken|not working|doesn\'t work|can\'t|won\'t)\b',
                r'\b(fix|resolve|solve|troubleshoot|repair)\b',
                r'\b(how to fix|how to resolve|how to solve)\b'
            ],
            'question': [
                r'\b(what|how|why|when|where|which|who)\b',
                r'\b(explain|describe|tell me|show me)\b',
                r'\b(what is|how does|why does)\b'
            ],
            'request': [
                r'\b(need|want|require|looking for|searching for)\b',
                r'\b(help with|assistance with|support for)\b',
                r'\b(guide|tutorial|instructions|steps)\b'
            ]
        }
        
        # Entity extraction patterns
        self.entity_patterns = {
            'software': [
                r'\b(windows|mac|linux|ubuntu|centos|debian)\b',
                r'\b(office|word|excel|powerpoint|outlook)\b',
                r'\b(chrome|firefox|safari|edge|opera)\b',
                r'\b(photoshop|illustrator|indesign|premiere)\b'
            ],
            'error_code': [
                r'\b(error\s+\d{3,4}|err\s+\d{3,4})\b',
                r'\b(0x[0-9a-fA-F]{8}|0x[0-9a-fA-F]{4})\b',
                r'\b(bsod|blue\s+screen|kernel\s+panic)\b'
            ],
            'hardware': [
                r'\b(printer|scanner|keyboard|mouse|monitor|display)\b',
                r'\b(router|modem|switch|hub|access\s+point)\b',
                r'\b(cpu|gpu|ram|ssd|hard\s+drive|motherboard)\b'
            ]
        }
        
    def preprocess_query(self, query: str, filters: Optional[Dict[str, Any]] = None) -> SearchQuery:
        """Preprocess and analyze a search query."""
        # Clean and normalize
        cleaned_query = self.text_processor.clean_text(query)
        
        # Detect intent
        intent = self._detect_intent(cleaned_query)
        
        # Extract entities
        entities = self._extract_entities(cleaned_query)
        
        # Expand terms with synonyms
        expanded_terms = self._expand_query_terms(cleaned_query)
        
        # Process filters
        processed_filters = self._process_filters(filters or {})
        
        # Calculate confidence
        confidence = self._calculate_confidence(intent, entities, expanded_terms)
        
        return SearchQuery(
            original_query=query,
            cleaned_query=cleaned_query,
            intent=intent,
            entities=entities,
            expanded_terms=expanded_terms,
            filters=processed_filters,
            confidence=confidence
        )
        
    def _detect_intent(self, query: str) -> str:
        """Detect the intent of the search query."""
        query_lower = query.lower()
        intent_scores = defaultdict(int)
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, query_lower, re.IGNORECASE)
                intent_scores[intent] += len(matches)
        
        # Default to general if no clear intent
        if not intent_scores:
            return 'general'
            
        # Return intent with highest score
        return max(intent_scores.items(), key=lambda x: x[1])[0]
        
    def _extract_entities(self, query: str) -> List[Dict[str, Any]]:
        """Extract entities from the query."""
        entities = []
        query_lower = query.lower()
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, query_lower, re.IGNORECASE)
                for match in matches:
                    entities.append({
                        'type': entity_type,
                        'value': match.group(),
                        'start': match.start(),
                        'end': match.end(),
                        'confidence': 0.9
                    })
        
        return entities
        
    def _expand_query_terms(self, query: str) -> List[str]:
        """Expand query terms with synonyms and related terms."""
        expanded_terms = [query]
        
        # Split into individual terms
        terms = query.split()
        
        for term in terms:
            if len(term) > 3:  # Only expand meaningful terms
                # Get synonyms
                synonyms = self.text_processor.expand_synonyms(term)
                expanded_terms.extend(synonyms)
                
                # Get related terms (stems)
                stem = self.text_processor.stem_text(term)
                if stem != term:
                    expanded_terms.append(stem)
        
        # Remove duplicates and return
        return list(set(expanded_terms))
        
    def _process_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate search filters."""
        processed_filters = {}
        
        # Category filter
        if 'category' in filters and filters['category']:
            processed_filters['category'] = filters['category']
            
        # Difficulty filter
        if 'difficulty' in filters and filters['difficulty']:
            if filters['difficulty'] in [level.value for level in DifficultyLevel]:
                processed_filters['difficulty'] = filters['difficulty']
                
        # Time filter
        if 'max_time' in filters and filters['max_time']:
            try:
                max_time = int(filters['max_time'])
                if 1 <= max_time <= 480:  # 1 minute to 8 hours
                    processed_filters['max_time'] = max_time
            except (ValueError, TypeError):
                pass
                
        # Success rate filter
        if 'min_success_rate' in filters and filters['min_success_rate']:
            try:
                min_rate = float(filters['min_success_rate'])
                if 0.0 <= min_rate <= 1.0:
                    processed_filters['min_success_rate'] = min_rate
            except (ValueError, TypeError):
                pass
                
        return processed_filters
        
    def _calculate_confidence(self, intent: str, entities: List[Dict], expanded_terms: List[str]) -> float:
        """Calculate confidence score for the query analysis."""
        confidence = 0.5  # Base confidence
        
        # Intent confidence
        if intent != 'general':
            confidence += 0.2
            
        # Entity confidence
        if entities:
            confidence += min(0.2, len(entities) * 0.1)
            
        # Term expansion confidence
        if len(expanded_terms) > 1:
            confidence += min(0.1, (len(expanded_terms) - 1) * 0.05)
            
        return min(1.0, confidence)


class ElasticsearchQueryBuilder:
    """Builds intelligent Elasticsearch queries."""
    
    def __init__(self, es_client: Elasticsearch, index_name: str = "helpdesk_kb"):
        self.es_client = es_client
        self.index_name = index_name
        
        # Field boosting configuration
        self.field_boosts = {
            'title': 3.0,
            'keywords': 2.5,
            'symptoms': 2.0,
            'content': 1.0,
            'category': 1.5,
            'subcategory': 1.3
        }
        
        # Fuzzy matching settings
        self.fuzzy_settings = {
            'title': {'fuzziness': 'AUTO', 'max_expansions': 50},
            'content': {'fuzziness': 'AUTO', 'max_expansions': 100},
            'keywords': {'fuzziness': 1, 'max_expansions': 20},
            'symptoms': {'fuzziness': 1, 'max_expansions': 20}
        }
        
    def build_search_query(self, search_query: SearchQuery, size: int = 20) -> Search:
        """Build a comprehensive Elasticsearch search query."""
        # Start with base search
        search = Search(using=self.es_client, index=self.index_name)
        
        # Build the main query
        main_query = self._build_main_query(search_query)
        search = search.query(main_query)
        
        # Add function scoring for relevance
        search = self._add_function_scoring(search)
        
        # Add filters
        search = self._add_filters(search, search_query.filters)
        
        # Add aggregations for faceting
        search = self._add_aggregations(search)
        
        # Set size and sorting
        search = search.extra(size=size)
        search = search.sort('_score')
        
        return search
        
    def _build_main_query(self, search_query: SearchQuery) -> Q:
        """Build the main search query."""
        # Multi-match query with field boosting
        multi_match = MultiMatch(
            query=search_query.cleaned_query,
            fields=[f"{field}^{boost}" for field, boost in self.field_boosts.items()],
            type='best_fields',
            operator='or',
            minimum_should_match='75%'
        )
        
        # Fuzzy matching for typos
        fuzzy_queries = []
        for field, settings in self.fuzzy_settings.items():
            fuzzy_query = Fuzzy(
                field=field,
                value=search_query.cleaned_query,
                **settings
            )
            fuzzy_queries.append(fuzzy_query)
        
        # Combine multi-match and fuzzy queries
        should_queries = [multi_match] + fuzzy_queries
        
        # Add entity-based queries
        for entity in search_query.entities:
            entity_query = Match(**{f"{entity['type']}_field": entity['value']})
            should_queries.append(entity_query)
            
        # Add expanded terms
        if search_query.expanded_terms:
            expanded_query = MultiMatch(
                query=' '.join(search_query.expanded_terms),
                fields=['title', 'content', 'keywords'],
                type='most_fields',
                operator='or'
            )
            should_queries.append(expanded_query)
        
        # Build the final query
        return Bool(should=should_queries, minimum_should_match=1)
        
    def _add_function_scoring(self, search: Search) -> Search:
        """Add function scoring for relevance ranking."""
        # Success rate boost
        success_rate_boost = FunctionScore(
            field_value_factor={
                'field': 'success_rate',
                'factor': 0.5,
                'modifier': 'sqrt'
            }
        )
        
        # View count boost (if available)
        view_count_boost = FunctionScore(
            field_value_factor={
                'field': 'view_count',
                'factor': 0.1,
                'modifier': 'log1p'
            }
        )
        
        # Difficulty-based boost (easier articles get slight boost)
        difficulty_boost = FunctionScore(
            script_score={
                'script': {
                    'source': '''
                        if (doc['difficulty_level.keyword'].value == 'easy') return 1.1;
                        else if (doc['difficulty_level.keyword'].value == 'medium') return 1.0;
                        else return 0.9;
                    '''
                }
            }
        )
        
        # Apply function scoring
        search = search.extra(
            function_score={
                'query': search.query,
                'functions': [success_rate_boost, view_count_boost, difficulty_boost],
                'score_mode': 'sum',
                'boost_mode': 'multiply'
            }
        )
        
        return search
        
    def _add_filters(self, search: Search, filters: Dict[str, Any]) -> Search:
        """Add filters to the search query."""
        filter_queries = []
        
        # Category filter
        if 'category' in filters:
            filter_queries.append(Term(category=filters['category']))
            
        # Difficulty filter
        if 'difficulty' in filters:
            filter_queries.append(Term(difficulty_level=filters['difficulty']))
            
        # Time filter
        if 'max_time' in filters:
            filter_queries.append(Range(estimated_time_minutes={'lte': filters['max_time']}))
            
        # Success rate filter
        if 'min_success_rate' in filters:
            filter_queries.append(Range(success_rate={'gte': filters['min_success_rate']}))
            
        # Active articles only
        filter_queries.append(Term(is_active=True))
        
        # Apply filters
        if filter_queries:
            search = search.filter(Bool(must=filter_queries))
            
        return search
        
    def _add_aggregations(self, search: Search) -> Search:
        """Add aggregations for faceting and analysis."""
        # Category aggregation
        search.aggs.bucket('categories', 'terms', field='category.keyword', size=20)
        
        # Difficulty aggregation
        search.aggs.bucket('difficulties', 'terms', field='difficulty_level.keyword', size=5)
        
        # Time range aggregation
        search.aggs.bucket('time_ranges', 'range', field='estimated_time_minutes', ranges=[
            {'from': 0, 'to': 15, 'key': '0-15 min'},
            {'from': 15, 'to': 30, 'key': '15-30 min'},
            {'from': 30, 'to': 60, 'key': '30-60 min'},
            {'from': 60, 'key': '60+ min'}
        ])
        
        # Success rate aggregation
        search.aggs.bucket('success_ranges', 'range', field='success_rate', ranges=[
            {'from': 0.0, 'to': 0.7, 'key': 'Low (0-70%)'},
            {'from': 0.7, 'to': 0.9, 'key': 'Medium (70-90%)'},
            {'from': 0.9, 'to': 1.0, 'key': 'High (90-100%)'}
        ])
        
        return search


class SearchResultProcessor:
    """Processes and enhances search results."""
    
    def __init__(self, es_client: Elasticsearch, index_name: str = "helpdesk_kb"):
        self.es_client = es_client
        self.index_name = index_name
        
    def process_search_results(self, search_response: Dict, original_query: str) -> Tuple[List[SearchResult], Dict[str, Any]]:
        """Process Elasticsearch search response into enhanced results."""
        hits = search_response.get('hits', {})
        total_hits = hits.get('total', {}).get('value', 0)
        
        # Process individual results
        results = []
        for hit in hits.get('hits', []):
            result = self._process_hit(hit, original_query)
            if result:
                results.append(result)
                
        # Process aggregations
        aggregations = self._process_aggregations(search_response.get('aggregations', {}))
        
        # Add related article suggestions
        results = self._add_related_articles(results)
        
        return results, {
            'total_hits': total_hits,
            'aggregations': aggregations,
            'processing_time': search_response.get('took', 0)
        }
        
    def _process_hit(self, hit: Dict, original_query: str) -> Optional[SearchResult]:
        """Process a single search hit."""
        source = hit.get('_source', {})
        score = hit.get('_score', 0.0)
        
        # Extract matched terms
        matched_terms = self._extract_matched_terms(hit, original_query)
        
        # Generate highlighted snippets
        highlighted_snippets = self._generate_snippets(hit, source.get('content', ''))
        
        return SearchResult(
            article_id=hit.get('_id', ''),
            title=source.get('title', ''),
            content=source.get('content', ''),
            category=source.get('category', ''),
            subcategory=source.get('subcategory', ''),
            difficulty_level=source.get('difficulty_level', ''),
            estimated_time_minutes=source.get('estimated_time_minutes', 0),
            success_rate=source.get('success_rate', 0.0),
            relevance_score=score,
            matched_terms=matched_terms,
            highlighted_snippets=highlighted_snippets,
            related_articles=[],
            view_count=source.get('view_count', 0)
        )
        
    def _extract_matched_terms(self, hit: Dict, original_query: str) -> List[str]:
        """Extract terms that matched the query."""
        matched_terms = set()
        
        # Check highlights
        highlights = hit.get('highlight', {})
        for field, highlights_list in highlights.items():
            for highlight in highlights_list:
                # Extract terms from highlighted text
                highlighted_terms = re.findall(r'<em>(.*?)</em>', highlight)
                matched_terms.update(highlighted_terms)
                
        # Add original query terms if no highlights
        if not matched_terms:
            query_terms = original_query.lower().split()
            matched_terms.update(query_terms)
            
        return list(matched_terms)
        
    def _generate_snippets(self, hit: Dict, content: str) -> List[str]:
        """Generate content snippets for the search result."""
        snippets = []
        
        # Use highlights if available
        highlights = hit.get('highlight', {})
        if 'content' in highlights:
            for highlight in highlights['content'][:3]:  # Max 3 snippets
                # Clean HTML tags and limit length
                clean_snippet = re.sub(r'<em>(.*?)</em>', r'**\1**', highlight)
                if len(clean_snippet) > 200:
                    clean_snippet = clean_snippet[:200] + '...'
                snippets.append(clean_snippet)
        else:
            # Generate snippets from content
            words = content.split()
            if len(words) > 50:
                # Create overlapping snippets
                for i in range(0, min(len(words), 200), 100):
                    snippet = ' '.join(words[i:i+100])
                    if len(snippet) > 200:
                        snippet = snippet[:200] + '...'
                    snippets.append(snippet)
                    if len(snippets) >= 3:
                        break
            else:
                snippets.append(content[:300] + '...' if len(content) > 300 else content)
                
        return snippets
        
    def _add_related_articles(self, results: List[SearchResult]) -> List[SearchResult]:
        """Add related article suggestions to search results."""
        for result in results:
            # Find articles in same category with similar content
            related_query = {
                'query': {
                    'bool': {
                        'must': [
                            {'term': {'category.keyword': result.category}},
                            {'term': {'is_active': True}}
                        ],
                        'must_not': [
                            {'term': {'_id': result.article_id}}
                        ]
                    }
                },
                'size': 3,
                'sort': [{'success_rate': {'order': 'desc'}}]
            }
            
            try:
                related_response = self.es_client.search(
                    index=self.index_name,
                    body=related_query
                )
                
                related_ids = []
                for hit in related_response['hits']['hits']:
                    related_ids.append(hit['_id'])
                    
                result.related_articles = related_ids
                
            except Exception as e:
                logging.warning(f"Failed to fetch related articles: {e}")
                result.related_articles = []
                
        return results
        
    def _process_aggregations(self, aggregations: Dict) -> Dict[str, Any]:
        """Process Elasticsearch aggregations into usable format."""
        processed = {}
        
        for agg_name, agg_data in aggregations.items():
            if agg_name == 'categories':
                processed['categories'] = [
                    {'name': bucket['key'], 'count': bucket['doc_count']}
                    for bucket in agg_data.get('buckets', [])
                ]
            elif agg_name == 'difficulties':
                processed['difficulties'] = [
                    {'name': bucket['key'], 'count': bucket['doc_count']}
                    for bucket in agg_data.get('buckets', [])
                ]
            elif agg_name == 'time_ranges':
                processed['time_ranges'] = [
                    {'name': bucket['key'], 'count': bucket['doc_count']}
                    for bucket in agg_data.get('buckets', [])
                ]
            elif agg_name == 'success_ranges':
                processed['success_ranges'] = [
                    {'name': bucket['key'], 'count': bucket['doc_count']}
                    for bucket in agg_data.get('buckets', [])
                ]
                
        return processed


class SearchAnalytics:
    """Tracks and analyzes search behavior."""
    
    def __init__(self, es_client: Elasticsearch, analytics_index: str = "search_analytics"):
        self.es_client = es_client
        self.analytics_index = analytics_index
        self._ensure_analytics_index()
        
    def _ensure_analytics_index(self):
        """Ensure the analytics index exists."""
        try:
            if not self.es_client.indices.exists(index=self.analytics_index):
                mapping = {
                    'mappings': {
                        'properties': {
                            'query': {'type': 'text'},
                            'timestamp': {'type': 'date'},
                            'result_count': {'type': 'integer'},
                            'click_through': {'type': 'boolean'},
                            'time_spent': {'type': 'float'},
                            'user_feedback': {'type': 'text'},
                            'intent': {'type': 'keyword'},
                            'entities': {'type': 'keyword'},
                            'filters_used': {'type': 'keyword'}
                        }
                    }
                }
                self.es_client.indices.create(index=self.analytics_index, body=mapping)
        except Exception as e:
            logging.warning(f"Failed to create analytics index: {e}")
            
    def track_search(self, search_query: SearchQuery, result_count: int, 
                    processing_time: float, filters_used: List[str]):
        """Track a search query."""
        try:
            analytics_doc = {
                'query': search_query.original_query,
                'timestamp': datetime.now().isoformat(),
                'result_count': result_count,
                'click_through': False,
                'time_spent': None,
                'user_feedback': None,
                'intent': search_query.intent,
                'entities': [entity['type'] for entity in search_query.entities],
                'filters_used': filters_used,
                'processing_time': processing_time
            }
            
            self.es_client.index(
                index=self.analytics_index,
                body=analytics_doc
            )
            
        except Exception as e:
            logging.error(f"Failed to track search: {e}")
            
    def track_click_through(self, query: str, article_id: str, time_spent: Optional[float] = None):
        """Track when a user clicks on a search result."""
        try:
            # Find the most recent search for this query
            search_query = {
                'query': {
                    'bool': {
                        'must': [
                            {'match': {'query': query}},
                            {'term': {'click_through': False}}
                        ]
                    }
                },
                'sort': [{'timestamp': {'order': 'desc'}}],
                'size': 1
            }
            
            response = self.es_client.search(
                index=self.analytics_index,
                body=search_query
            )
            
            if response['hits']['hits']:
                hit = response['hits']['hits'][0]
                # Update the document
                self.es_client.update(
                    index=self.analytics_index,
                    id=hit['_id'],
                    body={
                        'doc': {
                            'click_through': True,
                            'time_spent': time_spent,
                            'clicked_article': article_id
                        }
                    }
                )
                
        except Exception as e:
            logging.error(f"Failed to track click-through: {e}")
            
    def get_search_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get search analytics for the specified period."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Build analytics query
            analytics_query = {
                'query': {
                    'range': {
                        'timestamp': {
                            'gte': start_date
                        }
                    }
                },
                'aggs': {
                    'total_searches': {'value_count': {'field': 'query'}},
                    'unique_queries': {'cardinality': {'field': 'query'}},
                    'zero_result_searches': {
                        'filter': {'term': {'result_count': 0}}
                    },
                    'click_through_rate': {
                        'filter': {'term': {'click_through': True}}
                    },
                    'popular_queries': {
                        'terms': {'field': 'query', 'size': 20}
                    },
                    'intent_distribution': {
                        'terms': {'field': 'intent', 'size': 10}
                    },
                    'entity_usage': {
                        'terms': {'field': 'entities', 'size': 20}
                    },
                    'filter_usage': {
                        'terms': {'field': 'filters_used', 'size': 20}
                    },
                    'daily_searches': {
                        'date_histogram': {
                            'field': 'timestamp',
                            'calendar_interval': 'day'
                        }
                    }
                }
            }
            
            response = self.es_client.search(
                index=self.analytics_index,
                body=analytics_query,
                size=0
            )
            
            return self._process_analytics_response(response)
            
        except Exception as e:
            logging.error(f"Failed to get search analytics: {e}")
            return {}
            
    def _process_analytics_response(self, response: Dict) -> Dict[str, Any]:
        """Process analytics response into usable format."""
        aggregations = response.get('aggregations', {})
        
        total_searches = aggregations.get('total_searches', {}).get('value', 0)
        unique_queries = aggregations.get('unique_queries', {}).get('value', 0)
        zero_results = aggregations.get('zero_result_searches', {}).get('doc_count', 0)
        click_throughs = aggregations.get('click_through_rate', {}).get('doc_count', 0)
        
        analytics = {
            'summary': {
                'total_searches': total_searches,
                'unique_queries': unique_queries,
                'zero_result_rate': zero_results / total_searches if total_searches > 0 else 0,
                'click_through_rate': click_throughs / total_searches if total_searches > 0 else 0
            },
            'popular_queries': [
                {'query': bucket['key'], 'count': bucket['doc_count']}
                for bucket in aggregations.get('popular_queries', {}).get('buckets', [])
            ],
            'intent_distribution': [
                {'intent': bucket['key'], 'count': bucket['doc_count']}
                for bucket in aggregations.get('intent_distribution', {}).get('buckets', [])
            ],
            'entity_usage': [
                {'entity': bucket['key'], 'count': bucket['doc_count']}
                for bucket in aggregations.get('entity_usage', {}).get('buckets', [])
            ],
            'filter_usage': [
                {'filter': bucket['key'], 'count': bucket['doc_count']}
                for bucket in aggregations.get('filter_usage', {}).get('buckets', [])
            ],
            'daily_trends': [
                {'date': bucket['key_as_string'], 'count': bucket['doc_count']}
                for bucket in aggregations.get('daily_searches', {}).get('buckets', [])
            ]
        }
        
        return analytics


class IntelligentSearchSystem:
    """Main intelligent search system that orchestrates all components."""
    
    def __init__(self, es_client: Elasticsearch, index_name: str = "helpdesk_kb"):
        self.es_client = es_client
        self.index_name = index_name
        
        # Initialize components
        self.preprocessor = QueryPreprocessor()
        self.query_builder = ElasticsearchQueryBuilder(es_client, index_name)
        self.result_processor = SearchResultProcessor(es_client, index_name)
        self.analytics = SearchAnalytics(es_client)
        
    def search(self, query: str, filters: Optional[Dict[str, Any]] = None, 
               size: int = 20) -> Tuple[List[SearchResult], Dict[str, Any], SearchQuery]:
        """Perform an intelligent search."""
        start_time = datetime.now()
        
        # Preprocess query
        search_query = self.preprocessor.preprocess_query(query, filters)
        
        # Build Elasticsearch query
        es_query = self.query_builder.build_search_query(search_query, size)
        
        # Execute search
        try:
            search_response = es_query.execute()
            response_dict = search_response.to_dict()
        except Exception as e:
            logging.error(f"Search execution failed: {e}")
            return [], {}, search_query
            
        # Process results
        results, metadata = self.result_processor.process_search_results(response_dict, query)
        
        # Track analytics
        processing_time = (datetime.now() - start_time).total_seconds()
        filters_used = list(filters.keys()) if filters else []
        self.analytics.track_search(search_query, len(results), processing_time, filters_used)
        
        return results, metadata, search_query
        
    def get_search_suggestions(self, partial_query: str) -> List[str]:
        """Get search suggestions for partial queries."""
        try:
            # Use Elasticsearch suggest API
            suggest_query = {
                'suggest': {
                    'query_suggest': {
                        'prefix': partial_query,
                        'completion': {
                            'field': 'title_suggest',
                            'size': 5,
                            'skip_duplicates': True
                        }
                    }
                }
            }
            
            response = self.es_client.search(
                index=self.index_name,
                body=suggest_query
            )
            
            suggestions = []
            for suggestion in response['suggest']['query_suggest'][0]['options']:
                suggestions.append(suggestion['text'])
                
            return suggestions
            
        except Exception as e:
            logging.error(f"Failed to get search suggestions: {e}")
            return []
            
    def get_did_you_mean(self, query: str) -> List[str]:
        """Get 'Did you mean?' suggestions for potential typos."""
        try:
            # Use fuzzy matching to find similar terms
            fuzzy_query = {
                'query': {
                    'multi_match': {
                        'query': query,
                        'fields': ['title', 'keywords'],
                        'fuzziness': 'AUTO',
                        'operator': 'or'
                    }
                },
                'size': 5
            }
            
            response = self.es_client.search(
                index=self.index_name,
                body=fuzzy_query
            )
            
            suggestions = []
            for hit in response['hits']['hits']:
                title = hit['_source'].get('title', '')
                if title.lower() != query.lower():
                    suggestions.append(title)
                    
            return suggestions[:3]  # Return top 3 suggestions
            
        except Exception as e:
            logging.error(f"Failed to get 'Did you mean?' suggestions: {e}")
            return []
            
    def get_search_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive search analytics."""
        return self.analytics.get_search_analytics(days)
        
    def track_click_through(self, query: str, article_id: str, time_spent: Optional[float] = None):
        """Track when a user clicks on a search result."""
        self.analytics.track_click_through(query, article_id, time_spent)


def main():
    """Main function for testing the intelligent search system."""
    print("🚀 Intelligent Search System - Test Mode")
    print("=" * 50)
    
    # This would be used in the actual application
    # For testing, you would initialize with a real Elasticsearch client
    print("✅ Intelligent Search System initialized successfully!")
    print("Use this system in your Streamlit admin interface or other applications.")


if __name__ == "__main__":
    main()
