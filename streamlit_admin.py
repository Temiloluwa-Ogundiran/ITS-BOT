#!/usr/bin/env python3
"""
Streamlit Admin Interface for Knowledge Base Management
Provides a web-based interface for managing helpdesk knowledge base articles.
"""

import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Import our existing modules
from models import (
    KnowledgeArticle, SolutionStep, DiagnosticQuestion,
    DifficultyLevel, QuestionType, SolutionStepType
)
from utils import TextProcessor, DataValidator, DataConverter, IDGenerator
from helpdesk_elasticsearch import HelpdeskElasticsearchManager
from csv_importer import CSVImporter
from json_importer import JSONImporter
from excel_importer import ExcelImporter
from content_validator import ContentValidator


class StreamlitAdmin:
    """Main Streamlit admin interface for knowledge base management."""
    
    def __init__(self):
        self.setup_page_config()
        self.initialize_session_state()
        self.es_manager = None
        self.validator = ContentValidator()
        self.text_processor = TextProcessor()
        
    def setup_page_config(self):
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title="Knowledge Base Admin",
            page_icon="📚",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
    def initialize_session_state(self):
        """Initialize session state variables."""
        if 'current_article' not in st.session_state:
            st.session_state.current_article = None
        if 'edit_mode' not in st.session_state:
            st.session_state.edit_mode = False
        if 'import_results' not in st.session_state:
            st.session_state.import_results = None
        if 'search_query' not in st.session_state:
            st.session_state.search_query = ""
        if 'selected_category' not in st.session_state:
            st.session_state.selected_category = "All"
            
    def connect_elasticsearch(self):
        """Connect to Elasticsearch."""
        try:
            if self.es_manager is None:
                self.es_manager = HelpdeskElasticsearchManager()
                self.es_manager.connect()
            return True
        except Exception as e:
            st.error(f"Failed to connect to Elasticsearch: {e}")
            return False
            
    def run(self):
        """Run the main Streamlit application."""
        st.title("📚 Knowledge Base Admin Interface")
        st.markdown("---")
        
        # Sidebar for navigation and settings
        with st.sidebar:
            st.header("Navigation")
            page = st.selectbox(
                "Select Page",
                ["Add Article", "Browse/Edit", "Import", "Analytics"]
            )
            
            st.markdown("---")
            st.header("Elasticsearch Status")
            if st.button("Connect to ES"):
                if self.connect_elasticsearch():
                    st.success("Connected to Elasticsearch!")
                else:
                    st.error("Connection failed")
                    
            if self.es_manager:
                st.success("✅ Connected")
            else:
                st.warning("❌ Not Connected")
                
        # Main content area
        if page == "Add Article":
            self.show_add_article_page()
        elif page == "Browse/Edit":
            self.show_browse_edit_page()
        elif page == "Import":
            self.show_import_page()
        elif page == "Analytics":
            self.show_analytics_page()
            
    def show_add_article_page(self):
        """Display the Add Article form."""
        st.header("➕ Add New Article")
        
        if not self.connect_elasticsearch():
            st.error("Please connect to Elasticsearch first.")
            return
            
        with st.form("add_article_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input("Title *", key="title_input")
                category = st.selectbox(
                    "Category *",
                    ["Email", "Hardware", "Software", "Network", "Data Management", "Security"]
                )
                subcategory = st.text_input("Subcategory *", key="subcategory_input")
                difficulty = st.selectbox(
                    "Difficulty Level *",
                    [level.value for level in DifficultyLevel]
                )
                estimated_time = st.number_input(
                    "Estimated Time (minutes) *",
                    min_value=1,
                    max_value=480,
                    value=30,
                    key="time_input"
                )
                success_rate = st.slider(
                    "Success Rate *",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.85,
                    step=0.05,
                    key="success_input"
                )
                
            with col2:
                keywords = st.text_area(
                    "Keywords (comma-separated)",
                    placeholder="Enter keywords separated by commas",
                    key="keywords_input"
                )
                symptoms = st.text_area(
                    "Symptoms (comma-separated)",
                    placeholder="Enter symptoms separated by commas",
                    key="symptoms_input"
                )
                is_active = st.checkbox("Active", value=True, key="active_input")
                
            content = st.text_area(
                "Content *",
                height=200,
                placeholder="Enter the main article content...",
                key="content_input"
            )
            
            # Solution Steps
            st.subheader("Solution Steps")
            solution_steps = []
            
            for i in range(5):  # Allow up to 5 steps
                with st.expander(f"Step {i+1}", expanded=i==0):
                    step_title = st.text_input(f"Step {i+1} Title", key=f"step_title_{i}")
                    step_content = st.text_area(f"Step {i+1} Content", key=f"step_content_{i}")
                    step_type = st.selectbox(
                        f"Step {i+1} Type",
                        [step_type.value for step_type in SolutionStepType],
                        key=f"step_type_{i}"
                    )
                    step_time = st.number_input(
                        f"Step {i+1} Time (minutes)",
                        min_value=1,
                        max_value=60,
                        value=5,
                        key=f"step_time_{i}"
                    )
                    
                    if step_title and step_content:
                        solution_steps.append({
                            "order": i + 1,
                            "title": step_title,
                            "content": step_content,
                            "step_type": step_type,
                            "estimated_time_minutes": step_time
                        })
            
            # Diagnostic Questions
            st.subheader("Diagnostic Questions")
            diagnostic_questions = []
            
            for i in range(3):  # Allow up to 3 questions
                with st.expander(f"Question {i+1}", expanded=i==0):
                    question_text = st.text_input(f"Question {i+1}", key=f"question_{i}")
                    question_type = st.selectbox(
                        f"Question {i+1} Type",
                        [qtype.value for qtype in QuestionType],
                        key=f"qtype_{i}"
                    )
                    required = st.checkbox(f"Required", value=True, key=f"required_{i}")
                    
                    options = []
                    if question_type == "multiple_choice":
                        options_input = st.text_area(
                            f"Options (one per line)",
                            key=f"options_{i}"
                        )
                        if options_input:
                            options = [opt.strip() for opt in options_input.split('\n') if opt.strip()]
                    
                    if question_text:
                        diagnostic_questions.append({
                            "question": question_text,
                            "question_type": question_type,
                            "required": required,
                            "options": options if options else []
                        })
            
            # Preview and Submit
            if st.form_submit_button("Preview Article"):
                self.preview_article(
                    title, category, subcategory, content, keywords, symptoms,
                    difficulty, estimated_time, success_rate, is_active,
                    solution_steps, diagnostic_questions
                )
                
            if st.form_submit_button("Save Article"):
                self.save_article(
                    title, category, subcategory, content, keywords, symptoms,
                    difficulty, estimated_time, success_rate, is_active,
                    solution_steps, diagnostic_questions
                )
                
    def preview_article(self, title, category, subcategory, content, keywords,
                       symptoms, difficulty, estimated_time, success_rate, is_active,
                       solution_steps, diagnostic_questions):
        """Preview the article before saving."""
        st.subheader("📋 Article Preview")
        
        # Validate required fields
        if not all([title, category, subcategory, content]):
            st.error("Please fill in all required fields.")
            return
            
        # Create preview
        preview_data = {
            "title": title,
            "category": category,
            "subcategory": subcategory,
            "content": content,
            "keywords": [k.strip() for k in keywords.split(',') if k.strip()] if keywords else [],
            "symptoms": [s.strip() for s in symptoms.split(',') if s.strip()] if symptoms else [],
            "difficulty_level": difficulty,
            "estimated_time_minutes": estimated_time,
            "success_rate": success_rate,
            "is_active": is_active,
            "solution_steps": solution_steps,
            "diagnostic_questions": diagnostic_questions
        }
        
        # Display preview
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**Title:** {title}")
            st.markdown(f"**Category:** {category} > {subcategory}")
            st.markdown(f"**Difficulty:** {difficulty}")
            st.markdown(f"**Time:** {estimated_time} minutes")
            st.markdown(f"**Success Rate:** {success_rate:.0%}")
            st.markdown(f"**Status:** {'Active' if is_active else 'Inactive'}")
            
        with col2:
            if keywords:
                st.markdown("**Keywords:**")
                for keyword in preview_data["keywords"]:
                    st.markdown(f"- {keyword}")
                    
            if symptoms:
                st.markdown("**Symptoms:**")
                for symptom in preview_data["symptoms"]:
                    st.markdown(f"- {symptom}")
                    
        st.markdown("**Content:**")
        st.markdown(content)
        
        if solution_steps:
            st.markdown("**Solution Steps:**")
            for step in solution_steps:
                st.markdown(f"{step['order']}. **{step['title']}** ({step['step_type']})")
                st.markdown(f"   {step['content']} ({step['estimated_time_minutes']} min)")
                
        if diagnostic_questions:
            st.markdown("**Diagnostic Questions:**")
            for q in diagnostic_questions:
                required_text = " (Required)" if q['required'] else ""
                st.markdown(f"- **{q['question']}** [{q['question_type']}]{required_text}")
                if q['options']:
                    for option in q['options']:
                        st.markdown(f"  - {option}")
                        
    def save_article(self, title, category, subcategory, content, keywords,
                    symptoms, difficulty, estimated_time, success_rate, is_active,
                    solution_steps, diagnostic_questions):
        """Save the article to Elasticsearch."""
        try:
            # Validate required fields
            if not all([title, category, subcategory, content]):
                st.error("Please fill in all required fields.")
                return
                
            # Create article data
            article_data = {
                "title": title,
                "category": category,
                "subcategory": subcategory,
                "content": content,
                "keywords": [k.strip() for k in keywords.split(',') if k.strip()] if keywords else [],
                "symptoms": [s.strip() for s in symptoms.split(',') if s.strip()] if symptoms else [],
                "difficulty_level": difficulty,
                "estimated_time_minutes": estimated_time,
                "success_rate": success_rate,
                "is_active": is_active,
                "solution_steps": solution_steps,
                "diagnostic_questions": diagnostic_questions,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Validate article
            validation_result = self.validator.validate_article(article_data)
            if not validation_result.is_valid:
                st.error("Article validation failed:")
                for error in validation_result.errors:
                    st.error(f"- {error.field_name}: {error.error_message}")
                return
                
            # Save to Elasticsearch
            article_id = self.es_manager.index_article(article_data)
            
            if article_id:
                st.success(f"Article saved successfully with ID: {article_id}")
                # Clear form
                st.session_state.current_article = None
                st.rerun()
            else:
                st.error("Failed to save article.")
                
        except Exception as e:
            st.error(f"Error saving article: {e}")
            
    def show_browse_edit_page(self):
        """Display the Browse/Edit interface."""
        st.header("🔍 Browse and Edit Articles")
        
        if not self.connect_elasticsearch():
            st.error("Please connect to Elasticsearch first.")
            return
            
        # Search and filters
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            search_query = st.text_input(
                "Search Articles",
                placeholder="Search by title, content, keywords...",
                value=st.session_state.search_query
            )
            
        with col2:
            categories = ["All"] + ["Email", "Hardware", "Software", "Network", "Data Management", "Security"]
            selected_category = st.selectbox(
                "Filter by Category",
                categories,
                index=categories.index(st.session_state.selected_category)
            )
            
        with col3:
            if st.button("Search"):
                st.session_state.search_query = search_query
                st.session_state.selected_category = selected_category
                st.rerun()
                
        # Get articles
        try:
            articles = self.es_manager.search_articles(
                query=st.session_state.search_query if st.session_state.search_query else None,
                category=st.session_state.selected_category if st.session_state.selected_category != "All" else None
            )
            
            if not articles:
                st.info("No articles found matching your criteria.")
                return
                
            # Display articles
            for article in articles:
                self.display_article_card(article)
                
        except Exception as e:
            st.error(f"Error searching articles: {e}")
            
    def display_article_card(self, article):
        """Display an article card with edit options."""
        with st.expander(f"📄 {article.get('title', 'Untitled')}", expanded=False):
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.markdown(f"**Category:** {article.get('category', 'N/A')} > {article.get('subcategory', 'N/A')}")
                st.markdown(f"**Difficulty:** {article.get('difficulty_level', 'N/A')}")
                st.markdown(f"**Time:** {article.get('estimated_time_minutes', 'N/A')} min")
                st.markdown(f"**Success Rate:** {article.get('success_rate', 0):.0%}")
                
            with col2:
                status_color = "🟢" if article.get('is_active', False) else "🔴"
                st.markdown(f"**Status:** {status_color} {'Active' if article.get('is_active', False) else 'Inactive'}")
                st.markdown(f"**Created:** {article.get('created_at', 'N/A')[:10]}")
                st.markdown(f"**Updated:** {article.get('updated_at', 'N/A')[:10]}")
                
            with col3:
                if st.button("Edit", key=f"edit_{article.get('_id', 'unknown')}"):
                    st.session_state.current_article = article
                    st.session_state.edit_mode = True
                    st.rerun()
                    
                if st.button("Duplicate", key=f"dup_{article.get('_id', 'unknown')}"):
                    self.duplicate_article(article)
                    
                if st.button("Delete", key=f"del_{article.get('_id', 'unknown')}"):
                    if st.button("Confirm Delete", key=f"confirm_del_{article.get('_id', 'unknown')}"):
                        self.delete_article(article.get('_id'))
                        
            # Article content preview
            st.markdown("**Content Preview:**")
            content = article.get('content', '')
            if len(content) > 200:
                st.markdown(content[:200] + "...")
            else:
                st.markdown(content)
                
            # Keywords and symptoms
            if article.get('keywords'):
                st.markdown("**Keywords:** " + ", ".join(article['keywords']))
            if article.get('symptoms'):
                st.markdown("**Symptoms:** " + ", ".join(article['symptoms']))
                
    def duplicate_article(self, article):
        """Duplicate an existing article."""
        try:
            # Create a copy with modified title
            new_article = article.copy()
            new_article['title'] = f"{article['title']} (Copy)"
            new_article['created_at'] = datetime.now().isoformat()
            new_article['updated_at'] = datetime.now().isoformat()
            
            # Remove Elasticsearch metadata
            if '_id' in new_article:
                del new_article['_id']
            if '_index' in new_article:
                del new_article['_index']
            if '_score' in new_article:
                del new_article['_score']
                
            # Save the duplicate
            article_id = self.es_manager.index_article(new_article)
            if article_id:
                st.success(f"Article duplicated successfully with ID: {article_id}")
                st.rerun()
            else:
                st.error("Failed to duplicate article.")
                
        except Exception as e:
            st.error(f"Error duplicating article: {e}")
            
    def delete_article(self, article_id):
        """Delete an article."""
        try:
            if self.es_manager.delete_article(article_id):
                st.success("Article deleted successfully.")
                st.rerun()
            else:
                st.error("Failed to delete article.")
        except Exception as e:
            st.error(f"Error deleting article: {e}")
            
    def show_import_page(self):
        """Display the Import interface."""
        st.header("📥 Import Articles")
        
        if not self.connect_elasticsearch():
            st.error("Please connect to Elasticsearch first.")
            return
            
        # File upload
        st.subheader("Upload File")
        uploaded_file = st.file_uploader(
            "Choose a file to import",
            type=['csv', 'json', 'xlsx'],
            help="Supported formats: CSV, JSON, Excel"
        )
        
        if uploaded_file is not None:
            # File info
            file_details = {
                "Filename": uploaded_file.name,
                "File size": f"{uploaded_file.size / 1024:.1f} KB",
                "File type": uploaded_file.type
            }
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.json(file_details)
                
            with col2:
                preview_mode = st.checkbox("Preview Mode (validate without importing)")
                update_existing = st.checkbox("Update existing articles (JSON only)")
                
            # Import options
            if st.button("Start Import"):
                self.process_file_import(uploaded_file, preview_mode, update_existing)
                
        # Import results
        if st.session_state.import_results:
            self.display_import_results()
            
    def process_file_import(self, uploaded_file, preview_mode, update_existing):
        """Process file import based on file type."""
        try:
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            if file_extension == 'csv':
                self.import_csv_file(uploaded_file, preview_mode)
            elif file_extension == 'json':
                self.import_json_file(uploaded_file, preview_mode, update_existing)
            elif file_extension == 'xlsx':
                self.import_excel_file(uploaded_file, preview_mode)
            else:
                st.error(f"Unsupported file type: {file_extension}")
                
        except Exception as e:
            st.error(f"Error processing file: {e}")
            
    def import_csv_file(self, uploaded_file, preview_mode):
        """Import CSV file."""
        try:
            # Save uploaded file temporarily
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            # Import using CSV importer
            importer = CSVImporter(self.es_manager)
            result = importer.import_from_csv(temp_path, preview_mode=preview_mode)
            
            # Store results
            st.session_state.import_results = {
                "type": "CSV",
                "result": result,
                "filename": uploaded_file.name
            }
            
            # Clean up temp file
            import os
            os.remove(temp_path)
            
        except Exception as e:
            st.error(f"Error importing CSV: {e}")
            
    def import_json_file(self, uploaded_file, preview_mode, update_existing):
        """Import JSON file."""
        try:
            # Save uploaded file temporarily
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            # Import using JSON importer
            importer = JSONImporter(self.es_manager)
            result = importer.import_from_json(
                temp_path, 
                preview_mode=preview_mode,
                update_existing=update_existing
            )
            
            # Store results
            st.session_state.import_results = {
                "type": "JSON",
                "result": result,
                "filename": uploaded_file.name
            }
            
            # Clean up temp file
            import os
            os.remove(temp_path)
            
        except Exception as e:
            st.error(f"Error importing JSON: {e}")
            
    def import_excel_file(self, uploaded_file, preview_mode):
        """Import Excel file."""
        try:
            # Save uploaded file temporarily
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            # Import using Excel importer
            importer = ExcelImporter(self.es_manager)
            result = importer.import_from_excel(temp_path, preview_mode=preview_mode)
            
            # Store results
            st.session_state.import_results = {
                "type": "Excel",
                "result": result,
                "filename": uploaded_file.name
            }
            
            # Clean up temp file
            import os
            os.remove(temp_path)
            
        except Exception as e:
            st.error(f"Error importing Excel: {e}")
            
    def display_import_results(self):
        """Display import results."""
        st.subheader("📊 Import Results")
        
        results = st.session_state.import_results
        result = results["result"]
        
        # Summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Records", result.total_records)
        with col2:
            st.metric("Successful", result.successful_imports)
        with col3:
            st.metric("Failed", result.failed_imports)
        with col4:
            st.metric("Processing Time", f"{result.processing_time:.2f}s")
            
        # Success rate
        if result.total_records > 0:
            success_rate = result.successful_imports / result.total_records
            st.progress(success_rate)
            st.markdown(f"Success Rate: {success_rate:.1%}")
            
        # Errors
        if result.errors:
            st.subheader("❌ Import Errors")
            for error in result.errors:
                st.error(f"Row {error.get('row_number', 'N/A')}: {error.get('message', 'Unknown error')}")
                
        # Warnings
        if result.warnings:
            st.subheader("⚠️ Warnings")
            for warning in result.warnings:
                st.warning(warning)
                
        # Download failed records
        if result.failed_imports > 0:
            st.subheader("📥 Download Failed Records")
            # This would require implementing export functionality
            st.info("Export functionality for failed records not yet implemented.")
            
    def show_analytics_page(self):
        """Display the Analytics dashboard."""
        st.header("📊 Analytics Dashboard")
        
        if not self.connect_elasticsearch():
            st.error("Please connect to Elasticsearch first.")
            return
            
        try:
            # Get basic stats
            stats = self.es_manager.get_index_stats()
            
            # Total articles
            total_articles = stats.get('count', 0)
            st.metric("Total Articles", total_articles)
            
            if total_articles == 0:
                st.info("No articles found. Add some articles to see analytics.")
                return
                
            # Articles by category
            st.subheader("📈 Articles by Category")
            category_stats = self.get_category_stats()
            
            if category_stats:
                fig = px.pie(
                    values=list(category_stats.values()),
                    names=list(category_stats.keys()),
                    title="Articles by Category"
                )
                st.plotly_chart(fig, use_container_width=True)
                
            # Difficulty distribution
            st.subheader("🎯 Difficulty Distribution")
            difficulty_stats = self.get_difficulty_stats()
            
            if difficulty_stats:
                fig = px.bar(
                    x=list(difficulty_stats.keys()),
                    y=list(difficulty_stats.values()),
                    title="Articles by Difficulty Level"
                )
                st.plotly_chart(fig, use_container_width=True)
                
            # Success rate analysis
            st.subheader("📊 Success Rate Analysis")
            success_stats = self.get_success_rate_stats()
            
            if success_stats:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Average Success Rate", f"{success_stats['average']:.1%}")
                    st.metric("Highest Success Rate", f"{success_stats['highest']:.1%}")
                with col2:
                    st.metric("Lowest Success Rate", f"{success_stats['lowest']:.1%}")
                    st.metric("Total Success Rate", f"{success_stats['total']:.1%}")
                    
            # Recent activity
            st.subheader("🕒 Recent Activity")
            recent_articles = self.get_recent_articles()
            
            if recent_articles:
                for article in recent_articles[:5]:  # Show last 5
                    st.markdown(f"**{article['title']}** - {article['created_at'][:10]}")
                    
        except Exception as e:
            st.error(f"Error loading analytics: {e}")
            
    def get_category_stats(self):
        """Get article count by category."""
        try:
            # This would require implementing aggregation queries
            # For now, return sample data
            return {
                "Email": 15,
                "Hardware": 12,
                "Software": 18,
                "Network": 8,
                "Data Management": 6
            }
        except Exception as e:
            st.error(f"Error getting category stats: {e}")
            return {}
            
    def get_difficulty_stats(self):
        """Get article count by difficulty level."""
        try:
            # This would require implementing aggregation queries
            # For now, return sample data
            return {
                "Easy": 25,
                "Medium": 20,
                "Hard": 15
            }
        except Exception as e:
            st.error(f"Error getting difficulty stats: {e}")
            return {}
            
    def get_success_rate_stats(self):
        """Get success rate statistics."""
        try:
            # This would require implementing aggregation queries
            # For now, return sample data
            return {
                "average": 0.85,
                "highest": 0.98,
                "lowest": 0.65,
                "total": 0.85
            }
        except Exception as e:
            st.error(f"Error getting success rate stats: {e}")
            return {}
            
    def get_recent_articles(self):
        """Get recently created articles."""
        try:
            # This would require implementing date-based queries
            # For now, return sample data
            return [
                {"title": "Sample Article 1", "created_at": "2024-01-15T10:00:00Z"},
                {"title": "Sample Article 2", "created_at": "2024-01-14T15:30:00Z"},
                {"title": "Sample Article 3", "created_at": "2024-01-13T09:15:00Z"}
            ]
        except Exception as e:
            st.error(f"Error getting recent articles: {e}")
            return []


def main():
    """Main entry point for the Streamlit app."""
    app = StreamlitAdmin()
    app.run()


if __name__ == "__main__":
    main()
