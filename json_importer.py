#!/usr/bin/env python3
"""
JSON Importer for Knowledge Base Content
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from models import KnowledgeArticle, SolutionStep, DiagnosticQuestion
from utils import DataValidator, DataConverter
from csv_importer import ImportResult


class JSONImporter:
    """JSON file importer for knowledge base content."""
    
    def __init__(self, es_manager=None):
        """Initialize the JSON importer."""
        self.es_manager = es_manager
        self.validator = DataValidator()
        self.converter = DataConverter()
        
        self.import_stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'errors': [],
            'warnings': []
        }
    
    def import_from_json(self, file_path: str, preview_mode: bool = False, 
                        update_existing: bool = False) -> ImportResult:
        """Import content from a JSON file."""
        start_time = datetime.now()
        self._reset_stats()
        
        try:
            if not self._file_exists(file_path):
                raise FileNotFoundError(f"JSON file not found: {file_path}")
            
            logging.info(f"Starting JSON import from: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Handle different JSON formats
            articles_data = self._extract_articles(data)
            
            # Process articles
            valid_articles = self._process_articles(articles_data)
            
            # Import to Elasticsearch if not in preview mode
            if not preview_mode and self.es_manager and valid_articles:
                self._import_articles(valid_articles, update_existing)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return ImportResult(
                success=self.import_stats['failed'] == 0,
                total_records=self.import_stats['total_processed'],
                successful_imports=self.import_stats['successful'],
                failed_imports=self.import_stats['failed'],
                errors=self.import_stats['errors'],
                warnings=self.import_stats['warnings'],
                processing_time=processing_time
            )
            
        except Exception as e:
            logging.error(f"JSON import failed: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            return ImportResult(
                success=False,
                total_records=0,
                successful_imports=0,
                failed_imports=1,
                errors=[{"type": "import_error", "message": str(e)}],
                warnings=[],
                processing_time=processing_time
            )
    
    def _reset_stats(self):
        """Reset import statistics."""
        self.import_stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'errors': [],
            'warnings': []
        }
    
    def _file_exists(self, file_path: str) -> bool:
        """Check if file exists."""
        return Path(file_path).exists()
    
    def _extract_articles(self, data: Any) -> List[Dict[str, Any]]:
        """Extract articles from various JSON formats."""
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            if 'articles' in data:
                return data['articles']
            elif 'data' in data:
                return data['data']
            elif 'content' in data:
                return data['content']
            else:
                # Single article
                return [data]
        else:
            raise ValueError("Invalid JSON format: expected array of articles or object with articles key")
    
    def _process_articles(self, articles_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and validate articles."""
        valid_articles = []
        
        for i, article_data in enumerate(articles_data):
            try:
                self.import_stats['total_processed'] += 1
                
                # Add metadata
                if '_row_number' not in article_data:
                    article_data['_row_number'] = i + 1
                
                # Validate article data
                is_valid, errors = self.validator.validate_article_data(article_data)
                if is_valid:
                    # Convert to Elasticsearch format
                    es_doc = self.converter.article_to_elasticsearch(article_data)
                    valid_articles.append(es_doc)
                    self.import_stats['successful'] += 1
                else:
                    for error in errors:
                        self._record_error(i + 1, "validation", error)
                    self.import_stats['failed'] += 1
                    
            except Exception as e:
                self._record_error(i + 1, "processing", str(e))
                self.import_stats['failed'] += 1
        
        return valid_articles
    
    def _import_articles(self, articles: List[Dict[str, Any]], update_existing: bool):
        """Import articles to Elasticsearch."""
        try:
            if update_existing:
                # Handle updates
                for article in articles:
                    if 'article_id' in article:
                        self.es_manager.update_article(article['article_id'], article)
                    else:
                        self.es_manager.index_article(article)
            else:
                # Bulk import
                bulk_result = self.es_manager.bulk_index_articles(articles)
                logging.info(f"Bulk import result: {bulk_result}")
                
        except Exception as e:
            logging.error(f"Import failed: {e}")
            self._record_error(None, "import", str(e))
    
    def _record_error(self, index: Optional[int], error_type: str, message: str):
        """Record an error."""
        error_record = {
            'type': error_type,
            'message': message,
            'index': index
        }
        self.import_stats['errors'].append(error_record)


# Configure logging
logging.basicConfig(level=logging.INFO)
