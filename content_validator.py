#!/usr/bin/env python3
"""
Content Validator for Knowledge Base System

Provides comprehensive validation for knowledge base content including
field validation, data type checking, and business rule validation.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime

from models import KnowledgeArticle, SolutionStep, DiagnosticQuestion, DifficultyLevel


@dataclass
class ValidationError:
    """Validation error details."""
    row_number: Optional[int]
    field_name: str
    error_message: str
    severity: str = "error"  # error, warning, info


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[str]
    total_checked: int
    passed: int
    failed: int


class ContentValidator:
    """Content validation and quality checking for knowledge base articles."""
    
    def __init__(self):
        """Initialize the content validator."""
        self.required_fields = {
            'title': str,
            'content': str,
            'category': str
        }
        
        self.optional_fields = {
            'subcategory': str,
            'keywords': list,
            'symptoms': list,
            'difficulty_level': str,
            'estimated_time_minutes': int,
            'success_rate': float,
            'solution_steps': list,
            'diagnostic_questions': list,
            'is_active': bool
        }
        
        self.field_constraints = {
            'title': {'min_length': 5, 'max_length': 200},
            'content': {'min_length': 20, 'max_length': 10000},
            'estimated_time_minutes': {'min': 1, 'max': 480},  # 1 min to 8 hours
            'success_rate': {'min': 0.0, 'max': 1.0}
        }
        
        self.valid_difficulties = ['easy', 'medium', 'hard']
        self.valid_question_types = ['text', 'yes_no', 'multiple_choice']
        self.valid_step_types = ['instruction', 'verification', 'troubleshooting']
    
    def validate_article(self, article_data: Dict[str, Any]) -> ValidationResult:
        """Validate a single article comprehensively."""
        errors = []
        warnings = []
        total_checked = 0
        passed = 0
        failed = 0
        
        # Check required fields
        required_result = self._validate_required_fields(article_data)
        errors.extend(required_result.errors)
        warnings.extend(required_result.warnings)
        total_checked += required_result.total_checked
        passed += required_result.passed
        failed += required_result.failed
        
        # Validate data types
        type_result = self._validate_data_types(article_data)
        errors.extend(type_result.errors)
        warnings.extend(type_result.warnings)
        total_checked += type_result.total_checked
        passed += type_result.passed
        failed += type_result.failed
        
        # Check field constraints
        constraint_result = self._validate_field_constraints(article_data)
        errors.extend(constraint_result.errors)
        warnings.extend(constraint_result.warnings)
        total_checked += constraint_result.total_checked
        passed += constraint_result.passed
        failed += constraint_result.failed
        
        # Validate nested objects
        nested_result = self._validate_nested_objects(article_data)
        errors.extend(nested_result.errors)
        warnings.extend(nested_result.warnings)
        total_checked += nested_result.total_checked
        passed += nested_result.passed
        failed += nested_result.failed
        
        # Business rule validation
        business_result = self._validate_business_rules(article_data)
        errors.extend(business_result.errors)
        warnings.extend(business_result.warnings)
        total_checked += business_result.total_checked
        passed += business_result.passed
        failed += business_result.failed
        
        is_valid = len([e for e in errors if e.severity == "error"]) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            total_checked=total_checked,
            passed=passed,
            failed=failed
        )
    
    def _validate_required_fields(self, article_data: Dict[str, Any]) -> ValidationResult:
        """Validate that all required fields are present."""
        errors = []
        warnings = []
        total_checked = len(self.required_fields)
        passed = 0
        failed = 0
        
        for field_name, expected_type in self.required_fields.items():
            if field_name not in article_data or article_data[field_name] is None:
                errors.append(ValidationError(
                    row_number=article_data.get('_row_number'),
                    field_name=field_name,
                    error_message=f"Required field '{field_name}' is missing",
                    severity="error"
                ))
                failed += 1
            elif article_data[field_name] == "":
                errors.append(ValidationError(
                    row_number=article_data.get('_row_number'),
                    field_name=field_name,
                    error_message=f"Required field '{field_name}' cannot be empty",
                    severity="error"
                ))
                failed += 1
            else:
                passed += 1
        
        return ValidationResult(
            is_valid=failed == 0,
            errors=errors,
            warnings=warnings,
            total_checked=total_checked,
            passed=passed,
            failed=failed
        )
    
    def _validate_data_types(self, article_data: Dict[str, Any]) -> ValidationResult:
        """Validate data types of fields."""
        errors = []
        warnings = []
        total_checked = 0
        passed = 0
        failed = 0
        
        # Check required fields
        for field_name, expected_type in self.required_fields.items():
            if field_name in article_data:
                total_checked += 1
                if self._check_type(article_data[field_name], expected_type):
                    passed += 1
                else:
                    errors.append(ValidationError(
                        row_number=article_data.get('_row_number'),
                        field_name=field_name,
                        error_message=f"Field '{field_name}' must be of type {expected_type.__name__}",
                        severity="error"
                    ))
                    failed += 1
        
        # Check optional fields
        for field_name, expected_type in self.optional_fields.items():
            if field_name in article_data and article_data[field_name] is not None:
                total_checked += 1
                if self._check_type(article_data[field_name], expected_type):
                    passed += 1
                else:
                    errors.append(ValidationError(
                        row_number=article_data.get('_row_number'),
                        field_name=field_name,
                        error_message=f"Field '{field_name}' must be of type {expected_type.__name__}",
                        severity="error"
                    ))
                    failed += 1
        
        return ValidationResult(
            is_valid=failed == 0,
            errors=errors,
            warnings=warnings,
            total_checked=total_checked,
            passed=passed,
            failed=failed
        )
    
    def _check_type(self, value: Any, expected_type: type) -> bool:
        """Check if a value matches the expected type."""
        if expected_type == list:
            return isinstance(value, list)
        elif expected_type == str:
            return isinstance(value, str)
        elif expected_type == int:
            return isinstance(value, int) and not isinstance(value, bool)
        elif expected_type == float:
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        elif expected_type == bool:
            return isinstance(value, bool)
        else:
            return isinstance(value, expected_type)
    
    def _validate_field_constraints(self, article_data: Dict[str, Any]) -> ValidationResult:
        """Validate field constraints like length and range limits."""
        errors = []
        warnings = []
        total_checked = 0
        passed = 0
        failed = 0
        
        for field_name, constraints in self.field_constraints.items():
            if field_name in article_data and article_data[field_name] is not None:
                total_checked += 1
                field_value = article_data[field_name]
                
                # Check length constraints
                if 'min_length' in constraints and isinstance(field_value, str):
                    if len(field_value) < constraints['min_length']:
                        errors.append(ValidationError(
                            row_number=article_data.get('_row_number'),
                            field_name=field_name,
                            error_message=f"Field '{field_name}' is too short (minimum {constraints['min_length']} characters)",
                            severity="error"
                        ))
                        failed += 1
                        continue
                
                if 'max_length' in constraints and isinstance(field_value, str):
                    if len(field_value) > constraints['max_length']:
                        warnings.append(f"Field '{field_name}' is very long ({len(field_value)} characters)")
                        # This is a warning, not an error
                
                # Check numeric constraints
                if 'min' in constraints and isinstance(field_value, (int, float)):
                    if field_value < constraints['min']:
                        errors.append(ValidationError(
                            row_number=article_data.get('_row_number'),
                            field_name=field_name,
                            error_message=f"Field '{field_name}' must be at least {constraints['min']}",
                            severity="error"
                        ))
                        failed += 1
                        continue
                
                if 'max' in constraints and isinstance(field_value, (int, float)):
                    if field_value > constraints['max']:
                        errors.append(ValidationError(
                            row_number=article_data.get('_row_number'),
                            field_name=field_name,
                            error_message=f"Field '{field_name}' must be at most {constraints['max']}",
                            severity="error"
                        ))
                        failed += 1
                        continue
                
                passed += 1
        
        return ValidationResult(
            is_valid=failed == 0,
            errors=errors,
            warnings=warnings,
            total_checked=total_checked,
            passed=passed,
            failed=failed
        )
    
    def _validate_nested_objects(self, article_data: Dict[str, Any]) -> ValidationResult:
        """Validate nested objects like solution steps and diagnostic questions."""
        errors = []
        warnings = []
        total_checked = 0
        passed = 0
        failed = 0
        
        # Validate solution steps
        if 'solution_steps' in article_data and isinstance(article_data['solution_steps'], list):
            total_checked += 1
            steps_result = self._validate_solution_steps(article_data['solution_steps'], article_data.get('_row_number'))
            errors.extend(steps_result.errors)
            warnings.extend(steps_result.warnings)
            if steps_result.is_valid:
                passed += 1
            else:
                failed += 1
        
        # Validate diagnostic questions
        if 'diagnostic_questions' in article_data and isinstance(article_data['diagnostic_questions'], list):
            total_checked += 1
            questions_result = self._validate_diagnostic_questions(article_data['diagnostic_questions'], article_data.get('_row_number'))
            errors.extend(questions_result.errors)
            warnings.extend(questions_result.warnings)
            if questions_result.is_valid:
                passed += 1
            else:
                failed += 1
        
        return ValidationResult(
            is_valid=failed == 0,
            errors=errors,
            warnings=warnings,
            total_checked=total_checked,
            passed=passed,
            failed=failed
        )
    
    def _validate_solution_steps(self, steps: List[Dict[str, Any]], row_number: Optional[int]) -> ValidationResult:
        """Validate solution steps."""
        errors = []
        warnings = []
        total_checked = len(steps)
        passed = 0
        failed = 0
        
        if not steps:
            warnings.append("No solution steps provided")
            return ValidationResult(
                is_valid=True,
                errors=errors,
                warnings=warnings,
                total_checked=total_checked,
                passed=passed,
                failed=failed
            )
        
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                errors.append(ValidationError(
                    row_number=row_number,
                    field_name=f'solution_steps[{i}]',
                    error_message="Solution step must be a dictionary",
                    severity="error"
                ))
                failed += 1
                continue
            
            # Check required step fields
            if 'order' not in step or 'content' not in step:
                errors.append(ValidationError(
                    row_number=row_number,
                    field_name=f'solution_steps[{i}]',
                    error_message="Solution step must have 'order' and 'content' fields",
                    severity="error"
                ))
                failed += 1
                continue
            
            # Validate step order
            if not isinstance(step['order'], int) or step['order'] < 1:
                errors.append(ValidationError(
                    row_number=row_number,
                    field_name=f'solution_steps[{i}].order',
                    error_message="Step order must be a positive integer",
                    severity="error"
                ))
                failed += 1
                continue
            
            # Validate step content
            if not isinstance(step['content'], str) or len(step['content'].strip()) < 5:
                errors.append(ValidationError(
                    row_number=row_number,
                    field_name=f'solution_steps[{i}].content',
                    error_message="Step content must be a non-empty string (minimum 5 characters)",
                    severity="error"
                ))
                failed += 1
                continue
            
            passed += 1
        
        return ValidationResult(
            is_valid=failed == 0,
            errors=errors,
            warnings=warnings,
            total_checked=total_checked,
            passed=passed,
            failed=failed
        )
    
    def _validate_diagnostic_questions(self, questions: List[Dict[str, Any]], row_number: Optional[int]) -> ValidationResult:
        """Validate diagnostic questions."""
        errors = []
        warnings = []
        total_checked = len(questions)
        passed = 0
        failed = 0
        
        for i, question in enumerate(questions):
            if not isinstance(question, dict):
                errors.append(ValidationError(
                    row_number=row_number,
                    field_name=f'diagnostic_questions[{i}]',
                    error_message="Diagnostic question must be a dictionary",
                    severity="error"
                ))
                failed += 1
                continue
            
            # Check required question fields
            if 'question' not in question:
                errors.append(ValidationError(
                    row_number=row_number,
                    field_name=f'diagnostic_questions[{i}]',
                    error_message="Diagnostic question must have 'question' field",
                    severity="error"
                ))
                failed += 1
                continue
            
            # Validate question text
            if not isinstance(question['question'], str) or len(question['question'].strip()) < 5:
                errors.append(ValidationError(
                    row_number=row_number,
                    field_name=f'diagnostic_questions[{i}].question',
                    error_message="Question text must be a non-empty string (minimum 5 characters)",
                    severity="error"
                ))
                failed += 1
                continue
            
            # Validate question type if present
            if 'question_type' in question:
                if question['question_type'] not in self.valid_question_types:
                    errors.append(ValidationError(
                        row_number=row_number,
                        field_name=f'diagnostic_questions[{i}].question_type',
                        error_message=f"Question type must be one of: {', '.join(self.valid_question_types)}",
                        severity="error"
                    ))
                    failed += 1
                    continue
            
            passed += 1
        
        return ValidationResult(
            is_valid=failed == 0,
            errors=errors,
            warnings=warnings,
            total_checked=total_checked,
            passed=passed,
            failed=failed
        )
    
    def _validate_business_rules(self, article_data: Dict[str, Any]) -> ValidationResult:
        """Validate business rules and consistency."""
        errors = []
        warnings = []
        total_checked = 0
        passed = 0
        failed = 0
        
        # Check difficulty level
        if 'difficulty_level' in article_data:
            total_checked += 1
            difficulty = article_data['difficulty_level'].lower()
            if difficulty not in self.valid_difficulties:
                errors.append(ValidationError(
                    row_number=article_data.get('_row_number'),
                    field_name='difficulty_level',
                    error_message=f"Difficulty must be one of: {', '.join(self.valid_difficulties)}",
                    severity="error"
                ))
                failed += 1
            else:
                passed += 1
        
        # Check for orphaned subcategories
        if 'subcategory' in article_data and article_data['subcategory'] and 'category' not in article_data:
            total_checked += 1
            warnings.append("Subcategory provided without parent category")
            # This is a warning, not an error
            passed += 1
        
        # Check content quality
        if 'content' in article_data and isinstance(article_data['content'], str):
            total_checked += 1
            content = article_data['content']
            
            # Check for very short content
            if len(content) < 50:
                warnings.append("Content is quite short - consider adding more detail")
            
            # Check for common issues
            if content.lower().count('password') > 5:
                warnings.append("Content contains many references to 'password' - consider security implications")
            
            passed += 1
        
        return ValidationResult(
            is_valid=failed == 0,
            errors=errors,
            warnings=warnings,
            total_checked=total_checked,
            passed=passed,
            failed=failed
        )
    
    def validate_bulk_articles(self, articles: List[Dict[str, Any]]) -> ValidationResult:
        """Validate multiple articles and check for consistency across the set."""
        errors = []
        warnings = []
        total_checked = len(articles)
        passed = 0
        failed = 0
        
        # Individual article validation
        for article in articles:
            result = self.validate_article(article)
            errors.extend(result.errors)
            warnings.extend(result.warnings)
            
            if result.is_valid:
                passed += 1
            else:
                failed += 1
        
        # Cross-article consistency checks
        consistency_result = self._check_cross_article_consistency(articles)
        warnings.extend(consistency_result)
        
        return ValidationResult(
            is_valid=failed == 0,
            errors=errors,
            warnings=warnings,
            total_checked=total_checked,
            passed=passed,
            failed=failed
        )
    
    def _check_cross_article_consistency(self, articles: List[Dict[str, Any]]) -> List[str]:
        """Check consistency across multiple articles."""
        warnings = []
        
        # Collect all categories and subcategories
        categories = set()
        subcategories = set()
        
        for article in articles:
            if 'category' in article and article['category']:
                categories.add(article['category'])
            if 'subcategory' in article and article['subcategory']:
                subcategories.add(article['subcategory'])
        
        # Check for orphaned subcategories
        orphaned_subcategories = []
        for article in articles:
            if 'subcategory' in article and article['subcategory']:
                if 'category' not in article or not article['category']:
                    orphaned_subcategories.append(article['subcategory'])
        
        if orphaned_subcategories:
            warnings.append(f"Found subcategories without parent categories: {orphaned_subcategories}")
        
        # Check for potential duplicates
        titles = [article.get('title', '').lower().strip() for article in articles if article.get('title')]
        duplicate_titles = [title for title in set(titles) if titles.count(title) > 1]
        
        if duplicate_titles:
            warnings.append(f"Potential duplicate titles found: {duplicate_titles}")
        
        return warnings


# Configure logging
logging.basicConfig(level=logging.INFO)
