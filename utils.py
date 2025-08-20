"""
Utility functions for the Helpdesk Knowledge Base system.
Provides text processing, validation, conversion, and helper functions.
"""

import re
import json
import hashlib
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path
import logging
from urllib.parse import quote_plus, unquote_plus

# Configure logging
logger = logging.getLogger(__name__)


class TextProcessor:
    """Text processing utilities for helpdesk content."""
    
    # Common IT terms and their variations
    IT_TERMS = {
        'email': ['mail', 'e-mail', 'electronic mail'],
        'password': ['pwd', 'pass', 'passwd'],
        'username': ['user', 'login', 'userid'],
        'computer': ['pc', 'desktop', 'laptop'],
        'internet': ['web', 'online', 'network'],
        'printer': ['print', 'printing'],
        'software': ['program', 'application', 'app'],
        'hardware': ['device', 'equipment'],
        'error': ['issue', 'problem', 'bug', 'fault'],
        'solution': ['fix', 'resolve', 'repair'],
        'restart': ['reboot', 'reset'],
        'update': ['upgrade', 'patch'],
        'install': ['setup', 'configure'],
        'uninstall': ['remove', 'delete']
    }
    
    # Common stop words for IT content
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
    }
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Input text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep hyphens and apostrophes
        text = re.sub(r'[^\w\s\-']', ' ', text)
        
        # Clean up whitespace again
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract meaningful keywords from text.
        
        Args:
            text: Input text
            max_keywords: Maximum number of keywords to extract
            
        Returns:
            List of extracted keywords
        """
        if not text:
            return []
        
        # Clean the text
        cleaned_text = TextProcessor.clean_text(text)
        
        # Split into words
        words = cleaned_text.split()
        
        # Filter out stop words and short words
        keywords = []
        for word in words:
            if (len(word) > 2 and 
                word not in TextProcessor.STOP_WORDS and
                not word.isdigit()):
                keywords.append(word)
        
        # Count word frequency
        word_freq = {}
        for word in keywords:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_keywords[:max_keywords]]
    
    @staticmethod
    def expand_synonyms(terms: List[str]) -> List[str]:
        """
        Expand terms with their synonyms.
        
        Args:
            terms: List of terms to expand
            
        Returns:
            Expanded list with synonyms
        """
        expanded = set(terms)
        
        for term in terms:
            term_lower = term.lower()
            for main_term, synonyms in TextProcessor.IT_TERMS.items():
                if term_lower in synonyms or term_lower == main_term:
                    expanded.update([main_term] + synonyms)
        
        return list(expanded)
    
    @staticmethod
    def generate_slug(text: str, max_length: int = 50) -> str:
        """
        Generate a URL-friendly slug from text.
        
        Args:
            text: Input text
            max_length: Maximum slug length
            
        Returns:
            URL-friendly slug
        """
        if not text:
            return ""
        
        # Convert to lowercase and replace spaces with hyphens
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        
        # Truncate to max length
        if len(slug) > max_length:
            slug = slug[:max_length].rsplit('-', 1)[0]
        
        return slug.strip('-')
    
    @staticmethod
    def extract_symptoms(text: str) -> List[str]:
        """
        Extract potential symptoms from text.
        
        Args:
            text: Input text
            
        Returns:
            List of extracted symptoms
        """
        if not text:
            return []
        
        # Common symptom patterns
        symptom_patterns = [
            r'(?:cannot|cant|can\'t)\s+(?:log\s+in|access|connect|use|open)',
            r'(?:not\s+working|doesn\'t\s+work|isn\'t\s+working)',
            r'(?:error|failed|failure|broken|damaged)',
            r'(?:slow|sluggish|freezing|crashing)',
            r'(?:missing|lost|deleted|corrupted)',
            r'(?:password|login|access)\s+(?:problem|issue|trouble)'
        ]
        
        symptoms = []
        for pattern in symptom_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                symptom = text[match.start():match.end()].strip()
                if symptom and len(symptom) > 5:
                    symptoms.append(symptom)
        
        return list(set(symptoms))


class DataValidator:
    """Data validation utilities for helpdesk articles."""
    
    @staticmethod
    def validate_article_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate article data structure and content.
        
        Args:
            data: Article data dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        required_fields = ['title', 'content', 'category', 'difficulty_level']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate field types and values
        if 'title' in data:
            if not isinstance(data['title'], str):
                errors.append("Title must be a string")
            elif len(data['title']) > 200:
                errors.append("Title must be 200 characters or less")
        
        if 'content' in data:
            if not isinstance(data['content'], str):
                errors.append("Content must be a string")
            elif len(data['content']) < 10:
                errors.append("Content must be at least 10 characters")
            elif len(data['content']) > 10000:
                errors.append("Content must be 10,000 characters or less")
        
        if 'difficulty_level' in data:
            valid_levels = ['easy', 'medium', 'hard']
            if data['difficulty_level'] not in valid_levels:
                errors.append(f"Difficulty level must be one of: {valid_levels}")
        
        if 'estimated_time_minutes' in data:
            try:
                time_val = int(data['estimated_time_minutes'])
                if time_val < 1 or time_val > 480:
                    errors.append("Estimated time must be between 1 and 480 minutes")
            except (ValueError, TypeError):
                errors.append("Estimated time must be a valid integer")
        
        if 'success_rate' in data:
            try:
                rate_val = float(data['success_rate'])
                if rate_val < 0.0 or rate_val > 1.0:
                    errors.append("Success rate must be between 0.0 and 1.0")
            except (ValueError, TypeError):
                errors.append("Success rate must be a valid number")
        
        # Validate arrays
        array_fields = ['keywords', 'symptoms', 'solution_steps', 'diagnostic_questions']
        for field in array_fields:
            if field in data and data[field] is not None:
                if not isinstance(data[field], list):
                    errors.append(f"{field} must be a list")
                elif field == 'keywords' and len(data[field]) > 20:
                    errors.append("Keywords cannot exceed 20 items")
                elif field == 'symptoms' and len(data[field]) > 15:
                    errors.append("Symptoms cannot exceed 15 items")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_json_file(file_path: Union[str, Path]) -> Tuple[bool, List[str]]:
        """
        Validate JSON file structure and content.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            return False, ["File not found"]
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON format: {str(e)}"]
        except Exception as e:
            return False, [f"Error reading file: {str(e)}"]
        
        # Validate that it's a list
        if not isinstance(data, list):
            return False, ["Root element must be a list"]
        
        # Validate each article
        for i, article in enumerate(data):
            if not isinstance(article, dict):
                errors.append(f"Article {i} must be a dictionary")
                continue
            
            is_valid, article_errors = DataValidator.validate_article_data(article)
            if not is_valid:
                for error in article_errors:
                    errors.append(f"Article {i}: {error}")
        
        return len(errors) == 0, errors


class DataConverter:
    """Data conversion utilities for different formats."""
    
    @staticmethod
    def dict_to_article(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert raw dictionary to standardized article format.
        
        Args:
            data: Raw article data
            
        Returns:
            Standardized article data
        """
        # Create a copy to avoid modifying original
        article = data.copy()
        
        # Ensure timestamps are in ISO format
        if 'created_at' in article and article['created_at']:
            if isinstance(article['created_at'], str):
                try:
                    datetime.fromisoformat(article['created_at'].replace('Z', '+00:00'))
                except ValueError:
                    article['created_at'] = datetime.utcnow().isoformat()
            else:
                article['created_at'] = datetime.utcnow().isoformat()
        
        if 'updated_at' in article and article['updated_at']:
            if isinstance(article['updated_at'], str):
                try:
                    datetime.fromisoformat(article['updated_at'].replace('Z', '+00:00'))
                except ValueError:
                    article['updated_at'] = datetime.utcnow().isoformat()
            else:
                article['updated_at'] = datetime.utcnow().isoformat()
        
        # Ensure boolean fields are proper booleans
        boolean_fields = ['is_active']
        for field in boolean_fields:
            if field in article:
                if isinstance(article[field], str):
                    article[field] = article[field].lower() in ('true', '1', 'yes', 'on')
                elif isinstance(article[field], int):
                    article[field] = bool(article[field])
        
        # Ensure numeric fields are proper numbers
        numeric_fields = ['estimated_time_minutes', 'success_rate']
        for field in numeric_fields:
            if field in article and article[field] is not None:
                try:
                    if field == 'estimated_time_minutes':
                        article[field] = int(article[field])
                    else:
                        article[field] = float(article[field])
                except (ValueError, TypeError):
                    if field == 'estimated_time_minutes':
                        article[field] = 15  # Default value
                    else:
                        article[field] = 0.8  # Default value
        
        # Clean and validate arrays
        array_fields = ['keywords', 'symptoms', 'tags']
        for field in array_fields:
            if field in article:
                if isinstance(article[field], str):
                    # Split comma-separated strings
                    article[field] = [item.strip() for item in article[field].split(',') if item.strip()]
                elif not isinstance(article[field], list):
                    article[field] = []
                
                # Clean array items
                article[field] = [str(item).strip() for item in article[field] if item]
        
        return article
    
    @staticmethod
    def article_to_elasticsearch(article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert article to Elasticsearch document format.
        
        Args:
            article: Article data
            
        Returns:
            Elasticsearch document
        """
        # Create a copy for Elasticsearch
        es_doc = article.copy()
        
        # Ensure required Elasticsearch fields
        if 'created_at' not in es_doc:
            es_doc['created_at'] = datetime.utcnow().isoformat()
        if 'updated_at' not in es_doc:
            es_doc['updated_at'] = datetime.utcnow().isoformat()
        
        # Convert datetime objects to ISO strings
        for field in ['created_at', 'updated_at', 'last_reviewed']:
            if field in es_doc and es_doc[field]:
                if isinstance(es_doc[field], datetime):
                    es_doc[field] = es_doc[field].isoformat()
        
        # Ensure arrays are properly formatted
        for field in ['keywords', 'symptoms', 'tags']:
            if field in es_doc and not isinstance(es_doc[field], list):
                es_doc[field] = []
        
        return es_doc
    
    @staticmethod
    def elasticsearch_to_article(es_doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Elasticsearch document to article format.
        
        Args:
            es_doc: Elasticsearch document
            
        Returns:
            Article data
        """
        # Create a copy
        article = es_doc.copy()
        
        # Remove Elasticsearch metadata
        article.pop('_id', None)
        article.pop('_index', None)
        article.pop('_score', None)
        article.pop('_type', None)
        
        # Convert ISO strings to datetime objects
        for field in ['created_at', 'updated_at', 'last_reviewed']:
            if field in article and article[field]:
                try:
                    article[field] = datetime.fromisoformat(article[field].replace('Z', '+00:00'))
                except ValueError:
                    # Keep as string if parsing fails
                    pass
        
        return article


class IDGenerator:
    """Utilities for generating unique identifiers."""
    
    @staticmethod
    def generate_article_id() -> int:
        """
        Generate a unique article ID.
        
        Returns:
            Unique article ID
        """
        # In a real system, this would come from a database sequence
        # For now, use timestamp-based ID
        return int(datetime.utcnow().timestamp() * 1000) % 1000000
    
    @staticmethod
    def generate_uuid() -> str:
        """
        Generate a UUID string.
        
        Returns:
            UUID string
        """
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_session_id() -> str:
        """
        Generate a session ID.
        
        Returns:
            Session ID string
        """
        return f"session_{uuid.uuid4().hex[:8]}"
    
    @staticmethod
    def generate_slug_from_title(title: str, existing_slugs: Optional[List[str]] = None) -> str:
        """
        Generate a unique slug from title.
        
        Args:
            title: Article title
            existing_slugs: List of existing slugs to avoid conflicts
            
        Returns:
            Unique slug
        """
        base_slug = TextProcessor.generate_slug(title)
        
        if not existing_slugs:
            return base_slug
        
        # If slug exists, append a number
        slug = base_slug
        counter = 1
        while slug in existing_slugs:
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug


class QueryParser:
    """Utilities for parsing and analyzing user queries."""
    
    @staticmethod
    def extract_intent(query: str) -> Tuple[str, float]:
        """
        Extract user intent from query.
        
        Args:
            query: User query text
            
        Returns:
            Tuple of (intent, confidence_score)
        """
        query_lower = query.lower()
        
        # Define intent patterns
        intent_patterns = {
            'password_reset': [
                r'password.*reset|reset.*password|forgot.*password|change.*password',
                r'can\'t.*log.*in|cannot.*log.*in|locked.*out'
            ],
            'printer_issue': [
                r'printer.*not.*working|printer.*offline|can\'t.*print',
                r'print.*error|printer.*problem'
            ],
            'internet_slow': [
                r'slow.*internet|internet.*slow|slow.*connection',
                r'web.*slow|loading.*slow'
            ],
            'software_update': [
                r'software.*update|update.*software|install.*update',
                r'new.*version|latest.*version'
            ],
            'file_recovery': [
                r'deleted.*file|lost.*file|recover.*file',
                r'file.*missing|restore.*file'
            ]
        }
        
        best_intent = 'general_help'
        best_score = 0.0
        
        for intent, patterns in intent_patterns.items():
            score = 0.0
            for pattern in patterns:
                matches = re.findall(pattern, query_lower)
                if matches:
                    score += len(matches) * 0.3
            
            if score > best_score:
                best_score = score
                best_intent = intent
        
        # Normalize confidence score
        confidence = min(best_score, 1.0)
        
        return best_intent, confidence
    
    @staticmethod
    def extract_entities(query: str) -> Dict[str, List[str]]:
        """
        Extract entities from user query.
        
        Args:
            query: User query text
            
        Returns:
            Dictionary of entity types and values
        """
        entities = {
            'categories': [],
            'symptoms': [],
            'keywords': [],
            'time_constraints': []
        }
        
        query_lower = query.lower()
        
        # Extract categories
        categories = ['email', 'hardware', 'software', 'network', 'security', 'data']
        for category in categories:
            if category in query_lower:
                entities['categories'].append(category)
        
        # Extract symptoms
        symptoms = TextProcessor.extract_symptoms(query)
        entities['symptoms'] = symptoms
        
        # Extract keywords
        keywords = TextProcessor.extract_keywords(query, max_keywords=5)
        entities['keywords'] = keywords
        
        # Extract time constraints
        time_patterns = [
            r'(\d+)\s*(?:min|minute|minutes)',
            r'(\d+)\s*(?:hour|hours)',
            r'quick|fast|urgent|emergency'
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, query_lower)
            entities['time_constraints'].extend(matches)
        
        return entities
    
    @staticmethod
    def format_response(articles: List[Dict[str, Any]], query: str) -> str:
        """
        Format search results as a user-friendly response.
        
        Args:
            articles: List of found articles
            query: Original user query
            
        Returns:
            Formatted response string
        """
        if not articles:
            return f"I couldn't find any articles matching '{query}'. Please try different keywords or contact support."
        
        response = f"I found {len(articles)} article(s) that might help with '{query}':\n\n"
        
        for i, article in enumerate(articles, 1):
            title = article.get('title', 'Untitled')
            difficulty = article.get('difficulty_level', 'unknown').title()
            time = article.get('estimated_time_minutes', 0)
            success = article.get('success_rate', 0.0)
            
            response += f"{i}. {title}\n"
            response += f"   Difficulty: {difficulty} | Time: {time} min | Success Rate: {success:.0%}\n\n"
        
        response += "Click on any article title to view the full solution."
        
        return response


# Convenience functions
def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    return TextProcessor.clean_text(text)


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract meaningful keywords from text."""
    return TextProcessor.extract_keywords(text, max_keywords)


def generate_slug(text: str, max_length: int = 50) -> str:
    """Generate a URL-friendly slug from text."""
    return TextProcessor.generate_slug(text, max_length)


def validate_article_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate article data structure and content."""
    return DataValidator.validate_article_data(data)


def validate_json_file(file_path: Union[str, Path]) -> Tuple[bool, List[str]]:
    """Validate JSON file structure and content."""
    return DataValidator.validate_json_file(file_path)


def generate_article_id() -> int:
    """Generate a unique article ID."""
    return IDGenerator.generate_article_id()


def extract_intent(query: str) -> Tuple[str, float]:
    """Extract user intent from query."""
    return QueryParser.extract_intent(query)
