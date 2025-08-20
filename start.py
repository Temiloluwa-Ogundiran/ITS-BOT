#!/usr/bin/env python3
"""
Startup script for the Helpdesk Knowledge Base system.
This script initializes the system and provides a simple CLI interface.
"""

import json
import sys
import argparse
from helpdesk_elasticsearch import HelpdeskElasticsearchManager


def initialize_system():
    """Initialize the helpdesk knowledge base system."""
    print("🚀 Initializing Helpdesk Knowledge Base System...")
    
    try:
        # Initialize manager
        manager = HelpdeskElasticsearchManager()
        
        # Create index
        print("📋 Creating index...")
        if manager.create_index():
            print("✅ Index created successfully!")
        else:
            print("⚠️  Index already exists or creation failed")
        
        # Load sample data
        print("📚 Loading sample articles...")
        try:
            with open('sample_articles.json', 'r') as f:
                sample_articles = json.load(f)
            
            print(f"📖 Found {len(sample_articles)} sample articles")
            
            # Bulk index articles
            print("🔍 Indexing articles...")
            bulk_result = manager.bulk_index_articles(sample_articles)
            print(f"✅ Indexed {bulk_result['successful']} articles successfully")
            
            if bulk_result['failed'] > 0:
                print(f"⚠️  Failed to index {bulk_result['failed']} articles")
            
        except FileNotFoundError:
            print("⚠️  Sample articles file not found. Skipping data loading.")
        
        # Get system stats
        stats = manager.get_index_stats()
        print(f"📊 System ready! {stats['document_count']} documents indexed")
        
        manager.close()
        return True
        
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        return False


def search_demo():
    """Demonstrate search functionality."""
    print("\n🔍 Search Demo")
    print("=" * 30)
    
    try:
        manager = HelpdeskElasticsearchManager()
        
        # Search examples
        queries = [
            ("password reset", "Password-related issues"),
            ("printer", "Printer problems"),
            ("slow internet", "Internet speed issues"),
            ("blue screen", "System crashes")
        ]
        
        for query, description in queries:
            print(f"\n🔎 {description}: '{query}'")
            results = manager.search_articles(query=query, size=3)
            print(f"   Found {results['total']} articles:")
            
            for article in results['articles']:
                print(f"   - {article['title']} (Score: {article['_score']:.2f})")
        
        manager.close()
        
    except Exception as e:
        print(f"❌ Search demo failed: {e}")


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Helpdesk Knowledge Base System")
    parser.add_argument('--init', action='store_true', help='Initialize the system')
    parser.add_argument('--search', action='store_true', help='Run search demo')
    parser.add_argument('--demo', action='store_true', help='Run full demo')
    
    args = parser.parse_args()
    
    if not any([args.init, args.search, args.demo]):
        # Default: show help
        parser.print_help()
        return
    
    if args.init:
        initialize_system()
    
    if args.search:
        search_demo()
    
    if args.demo:
        print("🎬 Running full demo...")
        try:
            import example_usage
            example_usage.main()
        except ImportError:
            print("❌ Example usage module not found")
        except Exception as e:
            print(f"❌ Demo failed: {e}")


if __name__ == "__main__":
    main()
