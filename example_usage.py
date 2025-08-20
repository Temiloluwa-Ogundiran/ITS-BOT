#!/usr/bin/env python3
"""
Example usage script for the Helpdesk Knowledge Base Elasticsearch system.
"""

import json
import logging
from helpdesk_elasticsearch import HelpdeskElasticsearchManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Main function demonstrating the helpdesk system usage."""
    
    print("🚀 Helpdesk Knowledge Base Elasticsearch System Demo")
    print("=" * 60)
    
    try:
        # Initialize the Elasticsearch manager
        print("\n1. Initializing Elasticsearch connection...")
        manager = HelpdeskElasticsearchManager(
            host="localhost",
            port=9200,
            index_name="helpdesk_kb"
        )
        
        # Create the index
        print("\n2. Creating helpdesk knowledge base index...")
        if manager.create_index():
            print("✅ Index created successfully!")
        else:
            print("⚠️  Index creation failed or index already exists")
        
        # Load sample articles
        print("\n3. Loading sample articles...")
        with open('sample_articles.json', 'r') as f:
            sample_articles = json.load(f)
        
        print(f"📚 Loaded {len(sample_articles)} sample articles")
        
        # Bulk index the articles
        print("\n4. Indexing sample articles...")
        bulk_result = manager.bulk_index_articles(sample_articles)
        print(f"✅ Bulk indexing completed: {bulk_result['successful']} successful, {bulk_result['failed']} failed")
        
        # Get index statistics
        print("\n5. Getting index statistics...")
        stats = manager.get_index_stats()
        print(f"📊 Index stats: {stats['document_count']} documents, {stats['storage_size']} bytes")
        
        # Demonstrate search functionality
        print("\n6. Demonstrating search functionality...")
        
        # Search by text query
        print("\n   a) Full-text search for 'password':")
        results = manager.search_articles(query="password", size=3)
        print(f"   Found {results['total']} articles")
        for article in results['articles']:
            print(f"   - {article['title']} (Score: {article['_score']:.2f})")
        
        # Search by category
        print("\n   b) Search by category 'Hardware':")
        results = manager.search_articles(category="Hardware", size=5)
        print(f"   Found {results['total']} hardware articles")
        for article in results['articles']:
            print(f"   - {article['title']} ({article['subcategory']})")
        
        # Search by difficulty level
        print("\n   c) Search for easy articles:")
        results = manager.search_articles(difficulty_level="easy", size=5)
        print(f"   Found {results['total']} easy articles")
        for article in results['articles']:
            print(f"   - {article['title']} (Time: {article['estimated_time_minutes']} min)")
        
        # Demonstrate CRUD operations
        print("\n7. Demonstrating CRUD operations...")
        
        # Create a new article
        print("\n   a) Creating a new article...")
        new_article = {
            "article_id": 999,
            "title": "How to Connect to WiFi Network",
            "content": "Step-by-step guide to connect your device to a WiFi network.",
            "category": "Network",
            "subcategory": "WiFi",
            "difficulty_level": "easy",
            "keywords": ["wifi", "wireless", "network connection"],
            "symptoms": ["Cannot connect to WiFi", "WiFi not working"],
            "solution_steps": [
                {
                    "order": 1,
                    "title": "Open WiFi Settings",
                    "content": "Go to your device's WiFi settings"
                }
            ],
            "diagnostic_questions": [],
            "success_rate": 0.95,
            "estimated_time_minutes": 5,
            "is_active": True
        }
        
        doc_id = manager.index_article(new_article)
        if doc_id:
            print(f"   ✅ New article created with ID: {doc_id}")
        
        # Retrieve the article
        print("\n   b) Retrieving the new article...")
        retrieved_article = manager.get_article(doc_id)
        if retrieved_article:
            print(f"   ✅ Retrieved: {retrieved_article['title']}")
        
        # Update the article
        print("\n   c) Updating the article...")
        update_data = {
            "content": "Updated step-by-step guide to connect your device to a WiFi network.",
            "estimated_time_minutes": 8
        }
        if manager.update_article(doc_id, update_data):
            print("   ✅ Article updated successfully")
        
        # Final statistics
        print("\n8. Final system statistics...")
        final_stats = manager.get_index_stats()
        print(f"   📊 Total documents: {final_stats['document_count']}")
        print(f"   💾 Storage size: {final_stats['storage_size']:,} bytes")
        
        print("\n🎉 Demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        logger.error(f"Demo failed: {e}", exc_info=True)
    
    finally:
        # Clean up
        if 'manager' in locals():
            manager.close()
            print("\n🔌 Elasticsearch connection closed")


if __name__ == "__main__":
    main()
    print("\n" + "=" * 60)
    print("📚 Helpdesk Knowledge Base System Demo Complete!")
