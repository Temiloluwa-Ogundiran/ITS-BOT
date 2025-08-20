#!/usr/bin/env python3
"""
CSV Importer for Knowledge Base Content
"""

import csv
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from models import KnowledgeArticle, SolutionStep, DiagnosticQuestion, DifficultyLevel
from utils import DataValidator, DataConverter


@dataclass
class ImportResult:
    """Result of an import operation."""
    success: bool
    total_records: int
    successful_imports: int
    failed_imports: int
    errors: List[Dict[str, Any]]
    warnings: List[str]
    processing_time: float


class CSVImporter:
    """CSV file importer for knowledge base content."""
    
    def __init__(self, es_manager=None):
        """Initialize the CSV importer."""
        self.es_manager = es_manager
        self.validator = DataValidator()
        self.converter = DataConverter()
        
        self.required_columns = [
            'title', 'category', 'subcategory', 'content', 
            'keywords', 'symptoms', 'difficulty', 'estimated_time'
        ]
        
        self.import_stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'errors': [],
            'warnings': []
        }
    
    def import_from_csv(self, file_path: str, preview_mode: bool = False) -> ImportResult:
        """Import content from a CSV file."""
        start_time = datetime.now()
        self._reset_stats()
        
        try:
            if not self._file_exists(file_path):
                raise FileNotFoundError(f"CSV file not found: {file_path}")
            
            logger.info(f"Starting CSV import from: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Validate headers
                if not self._validate_headers(reader.fieldnames):
                    raise ValueError("Invalid CSV headers")
                
                # Process rows
                articles = []
                for row_num, row in enumerate(reader, start=2):
                    try:
                        article_data = self._process_row(row, row_num)
                        if article_data:
                            articles.append(article_data)
                            self.import_stats['total_processed'] += 1
                    except Exception as e:
                        self._record_error(row_num, "row_processing", str(e))
                        self.import_stats['failed'] += 1
                
                # Validate and convert articles
                valid_articles = self._validate_articles(articles)
                
                # Import to Elasticsearch if not in preview mode
                if not preview_mode and self.es_manager and valid_articles:
                    self._bulk_import(valid_articles)
                
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
            logger.error(f"CSV import failed: {e}")
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
        import os
        return os.path.exists(file_path)
    
    def _validate_headers(self, fieldnames: List[str]) -> bool:
        """Validate CSV headers against required columns."""
        if not fieldnames:
            return False
        
        missing_required = [col for col in self.required_columns if col not in fieldnames]
        return len(missing_required) == 0
    
    def _process_row(self, row: Dict[str, str], row_num: int) -> Optional[Dict[str, Any]]:
        """Process a single CSV row into article data."""
        try:
            article_data = {
                'title': row.get('title', '').strip(),
                'category': row.get('category', '').strip(),
                'subcategory': row.get('subcategory', '').strip(),
                'content': row.get('content', '').strip(),
                'keywords': self._parse_keywords(row.get('keywords', '')),
                'symptoms': self._parse_symptoms(row.get('symptoms', '')),
                'difficulty_level': row.get('difficulty', 'medium').strip().lower(),
                'estimated_time_minutes': self._parse_int(row.get('estimated_time', '0')),
                'success_rate': self._parse_float(row.get('success_rate', '0.8')),
                'solution_steps': self._parse_solution_steps(row.get('solution_steps', '')),
                'diagnostic_questions': self._parse_diagnostic_questions(row.get('diagnostic_questions', '')),
                'is_active': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                '_row_number': row_num
            }
            
            # Validate required fields
            if not article_data['title'] or not article_data['content']:
                raise ValueError("Title and content are required")
            
            return article_data
            
        except Exception as e:
            self._record_error(row_num, "row_processing", str(e))
            return None
    
    def _parse_keywords(self, keywords_str: str) -> List[str]:
        """Parse keywords from comma-separated string."""
        if not keywords_str:
            return []
        return [kw.strip() for kw in keywords_str.split(',') if kw.strip()]
    
    def _parse_symptoms(self, symptoms_str: str) -> List[str]:
        """Parse symptoms from comma-separated string."""
        if not symptoms_str:
            return []
        return [symptom.strip() for symptom in symptoms_str.split(',') if symptom.strip()]
    
    def _parse_solution_steps(self, steps_str: str) -> List[Dict[str, Any]]:
        """Parse solution steps from string or JSON."""
        if not steps_str:
            return []
        
        try:
            # Try to parse as JSON first
            if steps_str.strip().startswith('['):
                steps_data = json.loads(steps_str)
                if isinstance(steps_data, list):
                    return steps_data
        except json.JSONDecodeError:
            pass
        
        # Parse as numbered list
        steps = []
        lines = steps_str.strip().split('\n')
        step_num = 1
        
        for line in lines:
            line = line.strip()
            if line:
                # Remove numbering if present
                if line[0].isdigit() and '.' in line[:3]:
                    line = line.split('.', 1)[1].strip()
                
                if line:
                    steps.append({
                        'order': step_num,
                        'title': f"Step {step_num}",
                        'content': line,
                        'step_type': 'instruction'
                    })
                    step_num += 1
        
        return steps
    
    def _parse_diagnostic_questions(self, questions_str: str) -> List[Dict[str, Any]]:
        """Parse diagnostic questions from string or JSON."""
        if not questions_str:
            return []
        
        try:
            # Try to parse as JSON first
            if questions_str.strip().startswith('['):
                questions_data = json.loads(questions_str)
                if isinstance(questions_data, list):
                    return questions_data
        except json.JSONDecodeError:
            pass
        
        # Parse as simple questions
        questions = []
        lines = questions_str.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line:
                questions.append({
                    'question': line,
                    'question_type': 'text',
                    'required': False
                })
        
        return questions
    
    def _parse_int(self, value: str, default: int = 0) -> int:
        """Parse integer value with default."""
        try:
            return int(value.strip())
        except (ValueError, AttributeError):
            return default
    
    def _parse_float(self, value: str, default: float = 0.0) -> float:
        """Parse float value with default."""
        try:
            return float(value.strip())
        except (ValueError, AttributeError):
            return default
    
    def _validate_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate articles and return valid ones."""
        valid_articles = []
        
        for article_data in articles:
            try:
                # Validate article data
                is_valid, errors = self.validator.validate_article_data(article_data)
                if is_valid:
                    # Convert to Elasticsearch format
                    es_doc = self.converter.article_to_elasticsearch(article_data)
                    valid_articles.append(es_doc)
                    self.import_stats['successful'] += 1
                else:
                    for error in errors:
                        self._record_error(
                            article_data.get('_row_number'), "validation", error
                        )
                    self.import_stats['failed'] += 1
            except Exception as e:
                self._record_error(
                    article_data.get('_row_number'), "conversion", str(e)
                )
                self.import_stats['failed'] += 1
        
        return valid_articles
    
    def _bulk_import(self, articles: List[Dict[str, Any]]):
        """Perform bulk import to Elasticsearch."""
        try:
            bulk_result = self.es_manager.bulk_index_articles(articles)
            logger.info(f"Bulk import result: {bulk_result}")
        except Exception as e:
            logger.error(f"Bulk import failed: {e}")
            self._record_error(None, "bulk_import", str(e))
    
    def _record_error(self, row_number: Optional[int], error_type: str, message: str):
        """Record an error."""
        error_record = {
            'type': error_type,
            'message': message,
            'row_number': row_number
        }
        self.import_stats['errors'].append(error_record)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
