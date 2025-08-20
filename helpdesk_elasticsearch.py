import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from elasticsearch import Elasticsearch, ConnectionError, NotFoundError
from elasticsearch.exceptions import RequestError
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HelpdeskElasticsearchManager:
    """
    Manages Elasticsearch operations for the helpdesk knowledge base system.
    Handles connection, index creation, and CRUD operations.
    """
    
    def __init__(self, 
                 host: str = "localhost", 
                 port: int = 9200, 
                 index_name: str = "helpdesk_kb",
                 use_ssl: bool = False,
                 username: Optional[str] = None,
                 password: Optional[str] = None):
        """
        Initialize the Elasticsearch manager.
        
        Args:
            host: Elasticsearch host
            port: Elasticsearch port
            index_name: Name of the index
            use_ssl: Whether to use SSL
            username: Elasticsearch username (if authentication is enabled)
            password: Elasticsearch password (if authentication is enabled)
        """
        self.host = host
        self.port = port
        self.index_name = index_name
        self.use_ssl = use_ssl
        
        # Build connection parameters
        connection_params = {
            'hosts': [{'host': host, 'port': port}],
            'use_ssl': use_ssl,
            'verify_certs': False if use_ssl else True
        }
        
        if username and password:
            connection_params['http_auth'] = (username, password)
        
        try:
            self.es = Elasticsearch(**connection_params)
            self._test_connection()
            logger.info(f"Successfully connected to Elasticsearch at {host}:{port}")
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            raise
    
    def _test_connection(self) -> bool:
        """Test the Elasticsearch connection."""
        try:
            if self.es.ping():
                logger.info("Elasticsearch connection test successful")
                return True
            else:
                raise ConnectionError("Elasticsearch ping failed")
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            raise
    
    def create_index(self, mapping_file: str = "elasticsearch_mapping.json") -> bool:
        """
        Create the helpdesk knowledge base index with the specified mapping.
        
        Args:
            mapping_file: Path to the JSON mapping file
            
        Returns:
            bool: True if index created successfully, False otherwise
        """
        try:
            # Check if index already exists
            if self.es.indices.exists(index=self.index_name):
                logger.info(f"Index '{self.index_name}' already exists")
                return True
            
            # Load mapping from file
            with open(mapping_file, 'r') as f:
                mapping = json.load(f)
            
            # Create index with mapping
            response = self.es.indices.create(
                index=self.index_name,
                body=mapping
            )
            
            if response.get('acknowledged'):
                logger.info(f"Index '{self.index_name}' created successfully")
                return True
            else:
                logger.error("Failed to create index")
                return False
                
        except FileNotFoundError:
            logger.error(f"Mapping file '{mapping_file}' not found")
            return False
        except Exception as e:
            logger.error(f"Error creating index: {e}")
            return False
    
    def delete_index(self) -> bool:
        """
        Delete the helpdesk knowledge base index.
        
        Returns:
            bool: True if index deleted successfully, False otherwise
        """
        try:
            if self.es.indices.exists(index=self.index_name):
                response = self.es.indices.delete(index=self.index_name)
                if response.get('acknowledged'):
                    logger.info(f"Index '{self.index_name}' deleted successfully")
                    return True
                else:
                    logger.error("Failed to delete index")
                    return False
            else:
                logger.info(f"Index '{self.index_name}' does not exist")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting index: {e}")
            return False
    
    def index_article(self, article_data: Dict[str, Any]) -> Optional[str]:
        """
        Index a helpdesk article.
        
        Args:
            article_data: Dictionary containing article data
            
        Returns:
            Optional[str]: Document ID if successful, None otherwise
        """
        try:
            # Add timestamps if not present
            if 'created_at' not in article_data:
                article_data['created_at'] = datetime.utcnow().isoformat()
            if 'updated_at' not in article_data:
                article_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Validate required fields
            required_fields = ['title', 'content', 'category', 'difficulty_level']
            for field in required_fields:
                if field not in article_data:
                    raise ValueError(f"Required field '{field}' is missing")
            
            # Index the document
            response = self.es.index(
                index=self.index_name,
                body=article_data,
                refresh=True
            )
            
            if response.get('result') in ['created', 'updated']:
                doc_id = response.get('_id')
                logger.info(f"Article indexed successfully with ID: {doc_id}")
                return doc_id
            else:
                logger.error("Failed to index article")
                return None
                
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error indexing article: {e}")
            return None
    
    def get_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a helpdesk article by ID.
        
        Args:
            article_id: Document ID
            
        Returns:
            Optional[Dict]: Article data if found, None otherwise
        """
        try:
            response = self.es.get(
                index=self.index_name,
                id=article_id
            )
            
            if response.get('found'):
                article_data = response.get('_source', {})
                article_data['_id'] = response.get('_id')
                return article_data
            else:
                logger.warning(f"Article with ID '{article_id}' not found")
                return None
                
        except NotFoundError:
            logger.warning(f"Article with ID '{article_id}' not found")
            return None
        except Exception as e:
            logger.error(f"Error retrieving article: {e}")
            return None
    
    def update_article(self, article_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update a helpdesk article.
        
        Args:
            article_id: Document ID
            update_data: Dictionary containing fields to update
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Add updated timestamp
            update_data['updated_at'] = datetime.utcnow().isoformat()
            
            response = self.es.update(
                index=self.index_name,
                id=article_id,
                body={'doc': update_data},
                refresh=True
            )
            
            if response.get('result') == 'updated':
                logger.info(f"Article '{article_id}' updated successfully")
                return True
            else:
                logger.error("Failed to update article")
                return False
                
        except NotFoundError:
            logger.error(f"Article with ID '{article_id}' not found")
            return False
        except Exception as e:
            logger.error(f"Error updating article: {e}")
            return False
    
    def delete_article(self, article_id: str) -> bool:
        """
        Delete a helpdesk article.
        
        Args:
            article_id: Document ID
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            response = self.es.delete(
                index=self.index_name,
                id=article_id,
                refresh=True
            )
            
            if response.get('result') == 'deleted':
                logger.info(f"Article '{article_id}' deleted successfully")
                return True
            else:
                logger.error("Failed to delete article")
                return False
                
        except NotFoundError:
            logger.error(f"Article with ID '{article_id}' not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting article: {e}")
            return False
    
    def search_articles(self, 
                       query: str = None,
                       category: str = None,
                       difficulty_level: str = None,
                       symptoms: List[str] = None,
                       keywords: List[str] = None,
                       size: int = 10,
                       from_: int = 0) -> Dict[str, Any]:
        """
        Search for helpdesk articles using various criteria.
        
        Args:
            query: Full-text search query
            category: Filter by category
            difficulty_level: Filter by difficulty level
            symptoms: Filter by symptoms
            keywords: Filter by keywords
            size: Number of results to return
            from_: Starting offset for pagination
            
        Returns:
            Dict: Search results with hits and total count
        """
        try:
            # Build search query
            search_body = {
                "from": from_,
                "size": size,
                "query": {
                    "bool": {
                        "must": [],
                        "filter": [],
                        "should": []
                    }
                },
                "sort": [
                    {"_score": {"order": "desc"}},
                    {"updated_at": {"order": "desc"}}
                ]
            }
            
            # Add full-text search
            if query:
                search_body["query"]["bool"]["must"].append({
                    "multi_match": {
                        "query": query,
                        "fields": ["title^2", "content", "symptoms", "keywords"],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                })
            
            # Add filters
            if category:
                search_body["query"]["bool"]["filter"].append({
                    "term": {"category": category}
                })
            
            if difficulty_level:
                search_body["query"]["bool"]["filter"].append({
                    "term": {"difficulty_level": difficulty_level}
                })
            
            if symptoms:
                for symptom in symptoms:
                    search_body["query"]["bool"]["should"].append({
                        "match": {"symptoms": symptom}
                    })
            
            if keywords:
                for keyword in keywords:
                    search_body["query"]["bool"]["should"].append({
                        "match": {"keywords": keyword}
                    })
            
            # Execute search
            response = self.es.search(
                index=self.index_name,
                body=search_body
            )
            
            # Process results
            hits = response.get('hits', {})
            total = hits.get('total', {}).get('value', 0)
            articles = []
            
            for hit in hits.get('hits', []):
                article = hit.get('_source', {})
                article['_id'] = hit.get('_id')
                article['_score'] = hit.get('_score')
                articles.append(article)
            
            return {
                'total': total,
                'articles': articles,
                'from': from_,
                'size': size
            }
            
        except Exception as e:
            logger.error(f"Error searching articles: {e}")
            return {'total': 0, 'articles': [], 'from': from_, 'size': size}
    
    def bulk_index_articles(self, articles: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Bulk index multiple articles for better performance.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            Dict: Count of successful and failed operations
        """
        try:
            bulk_data = []
            
            for article in articles:
                # Add timestamps if not present
                if 'created_at' not in article:
                    article['created_at'] = datetime.utcnow().isoformat()
                if 'updated_at' not in article:
                    article['updated_at'] = datetime.utcnow().isoformat()
                
                # Add index action
                bulk_data.append({
                    'index': {
                        '_index': self.index_name
                    }
                })
                bulk_data.append(article)
            
            if bulk_data:
                response = self.es.bulk(body=bulk_data, refresh=True)
                
                # Count results
                successful = 0
                failed = 0
                
                for item in response.get('items', []):
                    if 'index' in item and item['index'].get('status') in [200, 201]:
                        successful += 1
                    else:
                        failed += 1
                
                logger.info(f"Bulk indexing completed: {successful} successful, {failed} failed")
                return {'successful': successful, 'failed': failed}
            else:
                logger.warning("No articles provided for bulk indexing")
                return {'successful': 0, 'failed': 0}
                
        except Exception as e:
            logger.error(f"Error in bulk indexing: {e}")
            return {'successful': 0, 'failed': len(articles)}
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the helpdesk knowledge base index.
        
        Returns:
            Dict: Index statistics
        """
        try:
            stats = self.es.indices.stats(index=self.index_name)
            index_stats = stats.get('indices', {}).get(self.index_name, {})
            
            return {
                'document_count': index_stats.get('total', {}).get('docs', {}).get('count', 0),
                'storage_size': index_stats.get('total', {}).get('store', {}).get('size_in_bytes', 0),
                'indexing_stats': index_stats.get('total', {}).get('indexing', {}),
                'search_stats': index_stats.get('total', {}).get('search', {})
            }
            
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {}
    
    def close(self):
        """Close the Elasticsearch connection."""
        try:
            if hasattr(self, 'es'):
                self.es.close()
                logger.info("Elasticsearch connection closed")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")


# Example usage and testing
if __name__ == "__main__":
    # Initialize manager
    manager = HelpdeskElasticsearchManager()
    
    try:
        # Create index
        if manager.create_index():
            print("Index created successfully")
            
            # Get index stats
            stats = manager.get_index_stats()
            print(f"Index stats: {stats}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        manager.close()
