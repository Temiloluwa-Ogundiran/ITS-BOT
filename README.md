# Helpdesk Knowledge Base - Elasticsearch System

A comprehensive Elasticsearch-based knowledge base system designed for helpdesk and technical support teams. This system provides advanced search capabilities, custom analyzers, and a robust Python API for managing helpdesk articles.

## 🚀 Features

- **Advanced Search**: Full-text search with custom analyzers for technical content
- **Custom Analyzers**: Synonym handling, symptom matching, and keyword extraction
- **Structured Data**: Nested objects for solution steps and diagnostic questions
- **Flexible Schema**: Comprehensive field mapping for helpdesk articles
- **Python API**: Complete CRUD operations and search functionality
- **Docker Support**: Easy local development with Docker Compose
- **Multi-Environment**: Configuration for development, staging, and production

## 📋 System Requirements

- Python 3.8+
- Elasticsearch 8.x
- Docker and Docker Compose (for local development)
- 4GB+ RAM (for Elasticsearch)

## 🏗️ Architecture

### Elasticsearch Mapping

The system uses a sophisticated mapping with:

- **Content Fields**: Title, content, keywords with custom analyzers
- **Categorization**: Category, subcategory, difficulty level
- **Problem Description**: Symptoms array with synonym handling
- **Solution Structure**: Nested solution steps with ordering
- **Diagnostic Support**: Nested diagnostic questions
- **Metadata**: Success rates, time estimates, timestamps

### Custom Analyzers

1. **Content Analyzer**: Standard tokenization with stemming and stop words
2. **Symptom Analyzer**: Synonym-aware analysis for problem descriptions
3. **Keyword Analyzer**: Optimized for technical term extraction
4. **Synonym Filter**: Handles common IT terminology variations

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd ITS-SELF-SERVICE
pip install -r requirements.txt
```

### 2. Start Elasticsearch with Docker

```bash
docker-compose up -d
```

Wait for services to be healthy:
```bash
docker-compose ps
```

### 3. Create Index and Load Data

```bash
python example_usage.py
```

### 4. Access Services

- **Elasticsearch**: http://localhost:9200
- **Kibana**: http://localhost:5601

## 📚 Usage Examples

### Basic Setup

```python
from helpdesk_elasticsearch import HelpdeskElasticsearchManager

# Initialize manager
manager = HelpdeskElasticsearchManager(
    host="localhost",
    port=9200,
    index_name="helpdesk_kb"
)

# Create index
manager.create_index()

# Load sample data
with open('sample_articles.json', 'r') as f:
    articles = json.load(f)

# Bulk index articles
result = manager.bulk_index_articles(articles)
```

### Search Operations

```python
# Full-text search
results = manager.search_articles(query="password reset")

# Category-based search
results = manager.search_articles(category="Email")

# Difficulty-based search
results = manager.search_articles(difficulty_level="easy")

# Symptom-based search
results = manager.search_articles(symptoms=["cannot log in"])

# Complex search
results = manager.search_articles(
    query="printer offline",
    category="Hardware",
    difficulty_level="medium"
)
```

### CRUD Operations

```python
# Create article
article_data = {
    "title": "How to Fix WiFi Issues",
    "content": "Step-by-step guide...",
    "category": "Network",
    "difficulty_level": "easy",
    # ... other fields
}
doc_id = manager.index_article(article_data)

# Retrieve article
article = manager.get_article(doc_id)

# Update article
update_data = {"content": "Updated content..."}
manager.update_article(doc_id, update_data)

# Delete article
manager.delete_article(doc_id)
```

## 🔧 Configuration

### Environment Variables

```bash
# Development (default)
ENVIRONMENT=development

# Staging
ENVIRONMENT=staging
ES_HOST=staging-elasticsearch.example.com
ES_PORT=9200
ES_USE_SSL=true
ES_USERNAME=user
ES_PASSWORD=pass

# Production
ENVIRONMENT=production
ES_HOST=prod-elasticsearch.example.com
ES_PORT=9200
ES_USE_SSL=true
ES_USERNAME=prod_user
ES_PASSWORD=prod_pass
```

### Custom Analyzers

The system includes predefined analyzers for:

- **Synonyms**: email/mail/e-mail, password/pwd, etc.
- **Technical Terms**: computer/PC/desktop, software/program/app
- **Problem Descriptions**: error/issue/problem/bug
- **Solutions**: fix/resolve/repair

## 📊 Sample Data

The system includes 8 sample helpdesk articles covering:

1. **Email Password Reset** - Easy, 10 minutes
2. **Printer Connection Issues** - Medium, 20 minutes
3. **Slow Internet Connection** - Medium, 25 minutes
4. **Software Updates** - Easy, 15 minutes
5. **Blue Screen Errors** - Hard, 45 minutes
6. **Two-Factor Authentication** - Medium, 20 minutes
7. **File Recovery** - Medium, 30 minutes
8. **Performance Optimization** - Medium, 35 minutes

Each article includes:
- Structured solution steps
- Diagnostic questions
- Success rates and time estimates
- Relevant keywords and symptoms

## 🧪 Testing

### Run Tests

```bash
pytest tests/
```

### Test Coverage

```bash
pytest --cov=helpdesk_elasticsearch tests/
```

### Manual Testing

```bash
# Test basic functionality
python example_usage.py

# Test search scenarios
python -c "
from helpdesk_elasticsearch import HelpdeskElasticsearchManager
manager = HelpdeskElasticsearchManager()
print('Connection successful!' if manager.es.ping() else 'Connection failed')
manager.close()
"
```

## 🔍 Search Capabilities

### Text Search

- **Fuzzy Matching**: Handles typos and variations
- **Synonym Expansion**: Finds related terms automatically
- **Stemming**: Matches word variations (connect, connecting, connection)

### Filtering

- **Category**: Email, Hardware, Network, Software, etc.
- **Difficulty**: Easy, Medium, Hard
- **Time**: Estimated resolution time
- **Success Rate**: Article effectiveness

### Advanced Queries

- **Multi-field Search**: Search across title, content, symptoms, keywords
- **Nested Object Search**: Search within solution steps and diagnostic questions
- **Scoring**: Relevance-based result ranking

## 🚀 Performance Optimization

### Index Settings

- **Sharding**: Configurable based on environment
- **Replicas**: 0 for development, 1+ for production
- **Refresh Interval**: 1 second for real-time search
- **Bulk Operations**: Optimized for large data imports

### Search Optimization

- **Result Window**: Configurable pagination limits
- **Timeout Settings**: Environment-specific timeouts
- **Caching**: Elasticsearch query result caching

## 🔒 Security

### Development

- Security disabled for easy local development
- CORS enabled for frontend integration
- No authentication required

### Production

- SSL/TLS encryption
- User authentication
- Network security policies
- Audit logging

## 📈 Monitoring

### Health Checks

```bash
# Elasticsearch health
curl http://localhost:9200/_cluster/health

# Index stats
curl http://localhost:9200/helpdesk_kb/_stats
```

### Kibana Dashboards

- Document counts and growth
- Search performance metrics
- Error rates and response times
- User query analytics

## 🛠️ Development

### Code Quality

```bash
# Format code
black helpdesk_elasticsearch.py

# Lint code
flake8 helpdesk_elasticsearch.py

# Type checking
mypy helpdesk_elasticsearch.py
```

### Adding New Features

1. **New Analyzers**: Add to `elasticsearch_mapping.json`
2. **New Fields**: Update mapping and validation rules
3. **New Search Types**: Extend `search_articles` method
4. **New Operations**: Add methods to `HelpdeskElasticsearchManager`

## 📚 API Reference

### HelpdeskElasticsearchManager

#### Constructor
```python
HelpdeskElasticsearchManager(
    host="localhost",
    port=9200,
    index_name="helpdesk_kb",
    use_ssl=False,
    username=None,
    password=None
)
```

#### Methods

- `create_index(mapping_file)` - Create the knowledge base index
- `delete_index()` - Remove the entire index
- `index_article(article_data)` - Index a single article
- `get_article(article_id)` - Retrieve article by ID
- `update_article(article_id, update_data)` - Update existing article
- `delete_article(article_id)` - Remove article
- `search_articles(**kwargs)` - Search with various criteria
- `bulk_index_articles(articles)` - Bulk index multiple articles
- `get_index_stats()` - Get index statistics
- `close()` - Close Elasticsearch connection

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Check the documentation
- Review the example code
- Test with the sample data

## 🔮 Future Enhancements

- **Machine Learning**: Automatic article categorization
- **Natural Language Processing**: Better symptom matching
- **Analytics Dashboard**: User behavior insights
- **API Rate Limiting**: Production-ready throttling
- **Multi-language Support**: Internationalization
- **Real-time Updates**: WebSocket notifications
- **Advanced Search**: Semantic search capabilities

---

**Built with ❤️ for helpdesk teams everywhere**
