import requests
import logging
from django.conf import settings
from datetime import datetime
from django.utils import timezone
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from .models import NewsArticle
import json
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

from django.contrib.auth import get_user_model
User = get_user_model()

def get_default_author():
    """Get or create a default superuser to associate with news articles."""
    try:
        return User.objects.filter(is_superuser=True).first() or User.objects.create_superuser(
            username='newsadmin',
            email='newsadmin@example.com',
            password='securepassword'  # Change this in production
        )
    except Exception:
        # If there's any error, try to get any user
        return User.objects.first()

logger = logging.getLogger(__name__)

ALLOWED_CATEGORIES = ['politics', 'technology', 'business', 'sports', 'entertainment']

# We'll update this with dynamic sources from APIs
ALLOWED_SOURCES = {
    'bbc-news': 'BBC News',
    'reuters': 'Reuters',
    'the-hindu': 'The Hindu',
    'wion': 'WION',
    'cnn': 'CNN',
    'the-times-of-india': 'The Times of India',
    'al-jazeera-english': 'Al Jazeera',
    'the-washington-post': 'Washington Post',
    'the-guardian': 'The Guardian',
    'bloomberg': 'Bloomberg',
    'associated-press': 'Associated Press',
    'google-news': 'Google News'
}

# Mapping between source codes and full names
SOURCE_NAME_MAPPING = {
    'BBC': 'BBC News',
    'REU': 'Reuters',
    'TH': 'The Hindu',
    'WION': 'WION',
    'TOI': 'The Times of India',
    'NDTV': 'NDTV'
}

# Reverse mapping for lookups (lowercase keys for case-insensitive matching)
REVERSE_SOURCE_MAPPING = {name.lower(): code for code, name in SOURCE_NAME_MAPPING.items()}
for code, name in SOURCE_NAME_MAPPING.items():
    REVERSE_SOURCE_MAPPING[code.lower()] = code

CATEGORY_KEYWORDS = {
    'politics': ['election', 'government', 'senate', 'parliament', 'law', 'political', 'president', 'minister', 'democracy', 'vote', 'campaign', 'policy'],
    'technology': ['ai', 'tech', 'innovation', 'robotics', 'software', 'digital', 'computing', 'internet', 'app', 'device', 'smartphone', 'computer'],
    'business': ['stocks', 'market', 'finance', 'economy', 'trade', 'investment', 'corporate', 'startup', 'profit', 'revenue', 'company', 'economic'],
    'sports': ['football', 'cricket', 'tennis', 'nba', 'olympics', 'league', 'tournament', 'championship', 'player', 'match', 'game', 'team', 'win'],
    'entertainment': ['movie', 'bollywood', 'hollywood', 'music', 'celebrity', 'film', 'actor', 'television', 'star', 'show', 'drama', 'award', 'concert']
}

# Cache for dynamically discovered sources
DYNAMIC_SOURCES = {}

def extract_source_from_url(url):
    """Extract a readable source name from a URL"""
    if not url:
        return "Unknown Source"
    
    try:
        domain = urlparse(url).netloc
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Split by dots and get the first part (the domain name)
        parts = domain.split('.')
        if len(parts) > 0:
            # Format nicely with spaces between words if needed
            name_parts = parts[0].split('-')
            source_name = ' '.join(part.capitalize() for part in name_parts)
            return source_name
        return domain.capitalize()
    except:
        return "Unknown Source"

def force_categorize(title, description=None):
    """Forces an article into one of the allowed categories based on keywords in title and description."""
    if not title and not description:
        return 'politics'  # Default to politics if no text content
    
    content = (title or "") + " " + (description or "")
    content = content.lower()
    
    # Count keyword matches for each category
    category_scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        category_scores[category] = sum(1 for keyword in keywords if keyword.lower() in content)
    
    # Return the category with the most keyword matches
    max_category = max(category_scores.items(), key=lambda x: x[1])
    
    # If no keywords matched, assign based on first letter of title
    if max_category[1] == 0:
        first_char = title[0].lower() if title else 'p'
        if first_char in 'abcd':
            return 'politics'
        elif first_char in 'efghi':
            return 'business'
        elif first_char in 'jklmn':
            return 'technology'
        elif first_char in 'opqrs':
            return 'sports'
        else:
            return 'entertainment'
    
    return max_category[0]

def fetch_from_newsapi(category=None, source=None):
    """Fetch news from NewsAPI with strict filtering."""
    try:
        url = "https://newsapi.org/v2/top-headlines"
        page_size = 50
        total_articles = []
        max_pages = 2
        
        # If both filters are provided, we need to decide which one to use for the API
        # and then manually filter for the other
        primary_filter = "source" if source else "category"
        
        for page in range(1, max_pages + 1):
            params = {
                'apiKey': settings.NEWSAPI_KEY,
                'pageSize': page_size,
                'language': 'en',
                'sortBy': 'publishedAt',
                'page': page
            }
            
            # Set the primary filter for the API call
            if primary_filter == "source" and source:
                params['sources'] = source.lower()
            elif primary_filter == "category" and category:
                params['category'] = category.lower()
            
            logger.info(f"NewsAPI: Fetching news (Page {page}) with primary filter: {primary_filter}")
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != 'ok':
                logger.error(f"NewsAPI error: {data.get('message', 'Unknown error')}")
                break
            
            articles = data.get('articles', [])
            if not articles:
                break
            
            for article in articles:
                # Get source details
                source_id = article.get('source', {}).get('id')
                source_name = article.get('source', {}).get('name')
                
                # If no source name, try to extract from URL
                if not source_name:
                    source_name = extract_source_from_url(article.get('url'))
                
                # Add to dynamic sources if not already known
                if source_name and source_id:
                    source_id = source_id.lower()
                    if source_id not in ALLOWED_SOURCES:
                        ALLOWED_SOURCES[source_id] = source_name
                    
                    # Also add to dynamic sources
                    DYNAMIC_SOURCES[source_id] = source_name
                elif source_name:
                    # Create a key from the name if id not available
                    source_key = source_name.lower().replace(' ', '-')
                    if source_key not in ALLOWED_SOURCES:
                        ALLOWED_SOURCES[source_key] = source_name
                    
                    # Also add to dynamic sources
                    DYNAMIC_SOURCES[source_key] = source_name
                
                # Skip article if it doesn't match our secondary filter
                if primary_filter == "category" and source and source_id != source.lower():
                    continue
                
                # Force article into one of our allowed categories
                title = article.get('title', '')
                description = article.get('description', '')
                assigned_category = force_categorize(title, description)
                
                # Skip if category filter is applied and doesn't match
                if category and assigned_category.lower() != category.lower():
                    continue
                
                # Add this article
                total_articles.append({
                    'id': str(article.get('url')),
                    'title': title,
                    'description': description or 'No description available',
                    'url': article.get('url'),
                    'urlToImage': article.get('urlToImage'),
                    'publishedAt': article.get('publishedAt'),
                    'source': source_name or extract_source_from_url(article.get('url')),
                    'source_id': source_id,
                    'category': assigned_category,
                    'api_source': 'newsapi'
                })
            
            if len(articles) < page_size:
                break
        
        logger.info(f"NewsAPI: Total fetched articles after strict filtering: {len(total_articles)}")
        return total_articles
        
    except requests.RequestException as e:
        logger.error(f"NewsAPI Error: {str(e)}")
        return []

def fetch_from_gnews(category=None, source=None):
    """Fetch news from GNews API with strict filtering."""
    try:
        url = "https://gnews.io/api/v4/top-headlines"
        total_articles = []
        
        params = {
            'token': settings.GNEWS_API_KEY,
            'lang': 'en',
            'max': 50,
        }
        
        # GNews only supports topic-based filtering in the API
        if category:
            category_mapping = {
                'business': 'business',
                'entertainment': 'entertainment',
                'sports': 'sports',
                'technology': 'technology',
                'politics': 'world',  # GNews doesn't have politics, use world instead
            }
            params['topic'] = category_mapping.get(category.lower(), 'general')
        
        logger.info(f"GNews: Fetching news with params: {params}")
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        articles = data.get('articles', [])
        
        for article in articles:
            article_source = article.get('source', {}).get('name')
            
            # If no source name, try to extract from URL
            if not article_source:
                article_source = extract_source_from_url(article.get('url'))
                
            source_id = None
            
            # Add to dynamic sources if not already known
            if article_source:
                source_id = article_source.lower().replace(' ', '-')
                if source_id not in ALLOWED_SOURCES:
                    ALLOWED_SOURCES[source_id] = article_source
                
                # Also add to dynamic sources
                DYNAMIC_SOURCES[source_id] = article_source
            
            title = article.get('title', '')
            description = article.get('description', '')
            
            # Skip if source filter is applied and doesn't match
            if source and (not article_source or source.lower() not in article_source.lower()):
                continue
            
            # Force categorize the article
            assigned_category = force_categorize(title, description)
            
            # Skip if category filter is applied and doesn't match
            if category and assigned_category.lower() != category.lower():
                continue
                
            # Format published date to match NewsAPI format
            pub_date = article.get('publishedAt')
            if pub_date and 'T' not in pub_date:
                pub_date = datetime.strptime(pub_date, '%Y-%m-%d %H:%M:%S %Z').strftime('%Y-%m-%dT%H:%M:%SZ')
            
            total_articles.append({
                'id': str(article.get('url')),
                'title': title,
                'description': description or 'No description available',
                'url': article.get('url'),
                'urlToImage': article.get('image'),
                'publishedAt': pub_date,
                'source': article_source or extract_source_from_url(article.get('url')),
                'source_id': source_id,
                'category': assigned_category,
                'api_source': 'gnews'
            })
        
        logger.info(f"GNews: Total fetched articles after strict filtering: {len(total_articles)}")
        return total_articles
        
    except requests.RequestException as e:
        logger.error(f"GNews Error: {str(e)}")
        return []

def fetch_from_currents_api(category=None, source=None):
    """Fetch news from Currents API with strict filtering."""
    try:
        url = "https://api.currentsapi.services/v1/latest-news"
        
        params = {
            'apiKey': settings.CURRENTS_API_KEY,
            'language': 'en',
            'limit': 50
        }
        
        # Currents API supports category-based filtering
        if category:
            category_mapping = {
                'politics': 'politics',
                'technology': 'technology',
                'business': 'business',
                'sports': 'sports',
                'entertainment': 'entertainment'
            }
            params['category'] = category_mapping.get(category.lower(), None)
            
            # Skip the API call if we don't have a mapping for this category
            if not params.get('category'):
                return []
        
        # Currents can filter by domain
        if source:
            # Extract domain from source name if possible
            source_domain = source.lower().replace(' ', '')
            if '.' not in source_domain:
                source_domain = f"{source_domain}.com"
            params['domain'] = source_domain
            
        logger.info(f"CurrentsAPI: Fetching news with params: {params}")
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        articles = data.get('news', [])
        total_articles = []
        
        for article in articles:
            article_source = article.get('source', {}).get('name', article.get('source'))
            
            # If no source name, try to extract from URL
            if not article_source:
                article_source = extract_source_from_url(article.get('url'))
                
            source_id = None
            
            # Add to dynamic sources if not already known
            if article_source:
                source_id = article_source.lower().replace(' ', '-')
                if source_id not in ALLOWED_SOURCES:
                    ALLOWED_SOURCES[source_id] = article_source
                
                # Also add to dynamic sources
                DYNAMIC_SOURCES[source_id] = article_source
            
            title = article.get('title', '')
            description = article.get('description', '')
            
            # Skip if source filter is applied and doesn't match
            if source and (not article_source or source.lower() not in article_source.lower()):
                continue
            
            # Force categorize the article
            assigned_category = force_categorize(title, description)
            
            # Skip if category filter is applied and doesn't match
            if category and assigned_category.lower() != category.lower():
                continue
            
            # Convert date format
            pub_date = article.get('published')
            if pub_date:
                try:
                    dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                    pub_date = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
                except (ValueError, TypeError):
                    pub_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
            
            total_articles.append({
                'id': str(article.get('url')),
                'title': title,
                'description': description or 'No description available',
                'url': article.get('url'),
                'urlToImage': article.get('image', article.get('imageUrl')), 
                'publishedAt': pub_date,
                'source': article_source or extract_source_from_url(article.get('url')),
                'source_id': source_id,
                'category': assigned_category,
                'api_source': 'currentsapi'
            })
        
        logger.info(f"CurrentsAPI: Total fetched articles after strict filtering: {len(total_articles)}")
        return total_articles
        
    except requests.RequestException as e:
        logger.error(f"CurrentsAPI Error: {str(e)}")
        return []

def fetch_news_from_api(category=None, source=None):
    """Fetch news from multiple APIs with strict filtering for both category and source."""
    apis = []
    
    # Add available APIs based on configuration
    if hasattr(settings, 'NEWSAPI_KEY'):
        apis.append(('newsapi', fetch_from_newsapi))
    
    if hasattr(settings, 'GNEWS_API_KEY'):
        apis.append(('gnews', fetch_from_gnews))
        
    if hasattr(settings, 'CURRENTS_API_KEY'):
        apis.append(('currentsapi', fetch_from_currents_api))
    
    if not apis:
        logger.error("No API keys configured. Please add at least one news API key in settings.")
        return []
    
    # Fetch from all APIs in parallel
    with ThreadPoolExecutor(max_workers=len(apis)) as executor:
        futures = {api_name: executor.submit(fetch_func, category, source) 
                  for api_name, fetch_func in apis}
        
        results = []
        for api_name, future in futures.items():
            try:
                api_results = future.result()
                logger.info(f"{api_name} returned {len(api_results)} articles after strict filtering")
                results.extend(api_results)
            except Exception as e:
                logger.error(f"Error fetching from {api_name}: {str(e)}")
    
    # Remove duplicates by URL
    unique_results = {}
    for article in results:
        if article['url'] not in unique_results:
            unique_results[article['url']] = article
    
    logger.info(f"Total unique articles after filtering by both category and source: {len(unique_results)}")
    return list(unique_results.values())

def update_news(request):
    """Fetch and store the latest news articles in the database without duplicating existing ones."""
    category = request.GET.get('category', '').strip().lower() or None
    source = request.GET.get('source', '').strip().lower() or None

    articles = fetch_news_from_api(category, source)
    articles_created = 0
    duplicates_skipped = 0

    for article in articles:
        # Check if article with same URL already exists
        article_url = article.get('url', 'https://example.com')
        if NewsArticle.objects.filter(url=article_url).exists():
            duplicates_skipped += 1
            continue
            
        # Create a unique timestamp to ensure each article is stored as a new record
        unique_id = f"{article.get('id')}_{timezone.now().timestamp()}"
        
        # Get the category in the correct format for your model
        category_map = {
            'politics': 'POL',
            'technology': 'TECH',
            'business': 'BUS',
            'sports': 'SPO',
            'entertainment': 'ENT'
        }
        
        article_category = category_map.get(article.get('category', '').lower(), 'POL')
        
        # Extract source name
        source_display = article.get('source', 'Unknown Source')
        if source_display == "Unknown Source" and article.get('url'):
            source_display = extract_source_from_url(article.get('url'))
        
        # Map source to your model's SOURCE_CHOICES if possible
        source_code = REVERSE_SOURCE_MAPPING.get(source_display.lower(), None)
        
        if not source_code:
            # If not in our mapping, store the original source name
            # This creates a custom source code based on the source name
            source_code = source_display[:4].upper()
            
            # Add to our mappings for future use
            if source_display and source_code not in SOURCE_NAME_MAPPING:
                SOURCE_NAME_MAPPING[source_code] = source_display
                REVERSE_SOURCE_MAPPING[source_display.lower()] = source_code
        
        # Create new record if it doesn't exist
        NewsArticle.objects.create(
            api_source_id=unique_id,
            title=article.get('title', 'No title available'),
            content=article.get('description', 'No content available'),
            url=article_url,
            image=article.get('urlToImage', ''),
            source=source_code,  # Use the code but preserve original name
            category=article_category,
            author=request.user if request.user.is_authenticated else get_default_author(),
            created_at=timezone.make_aware(
                datetime.strptime(article.get('publishedAt', timezone.now().strftime('%Y-%m-%dT%H:%M:%SZ')), 
                '%Y-%m-%dT%H:%M:%SZ')
            ) if article.get('publishedAt') else timezone.now()
        )
        articles_created += 1

    # Redirect to the news list with a query parameter to show articles from DB
    return redirect(f'news_list?from_db=true&created={articles_created}&skipped={duplicates_skipped}')

def news_list(request):
    """Display the latest news with strict category and source filters."""
    category = request.GET.get('category', '').strip().lower()
    source = request.GET.get('source', '').strip().lower()
    display_from_db = request.GET.get('from_db', 'false').lower() == 'true'
    
    if display_from_db:
        # Get articles from database, ordered by creation date (newest first)
        query = NewsArticle.objects.all().order_by('-created_at')
        
        if category and category in [c.lower() for c in ALLOWED_CATEGORIES]:
            category_map = {
                'politics': 'POL',
                'technology': 'TECH',
                'business': 'BUS',
                'sports': 'SPO',
                'entertainment': 'ENT'
            }
            cat_code = category_map.get(category, 'POL')
            query = query.filter(category=cat_code)
            
        if source and source in [s.lower() for s in ALLOWED_SOURCES.keys()]:
            # Find the corresponding source code
            source_code = None
            for key, value in ALLOWED_SOURCES.items():
                if key.lower() == source or value.lower() == source:
                    source_code = REVERSE_SOURCE_MAPPING.get(value.lower(), key.upper()[:4])
                    break
            
            if source_code:
                query = query.filter(source=source_code)
            
        articles = list(query.values(
            'id', 'title', 'content', 'url', 'image', 'source', 'category', 'created_at'
        ))
        
        # Format the articles to match the API response format
        for article in articles:
            article['description'] = article.pop('content')
            article['urlToImage'] = article.pop('image')
            article['publishedAt'] = article['created_at'].strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # Use the readable source name if available, otherwise use the code
            source_code = article.pop('source')
            article['source'] = SOURCE_NAME_MAPPING.get(source_code, source_code)
            
            article.pop('created_at')
    else:
        # Get articles from API with strict filtering
        articles = fetch_news_from_api(
            category if category in [c.lower() for c in ALLOWED_CATEGORIES] else None, 
            source if source in [s.lower() for s in ALLOWED_SOURCES.keys()] else None
        )

    logger.info(f"Final article count after all filtering: {len(articles)}")

    # Sort and paginate results
    try:
        articles = sorted(
            articles,
            key=lambda x: datetime.strptime(x.get('publishedAt', '2000-01-01T00:00:00Z'), '%Y-%m-%dT%H:%M:%SZ'),
            reverse=True
        )
    except Exception as e:
        logger.error(f"Error sorting articles: {str(e)}")

    paginator = Paginator(articles, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Use both predefined and dynamically discovered sources
    all_sources = ALLOWED_SOURCES.copy()
    all_sources.update(DYNAMIC_SOURCES)

    context = {
        'page_obj': page_obj,
        'categories': ALLOWED_CATEGORIES,  
        'sources': all_sources.items(), 
        'selected_category': category,
        'selected_source': source,
        'from_db': display_from_db,
        'articles_created': request.GET.get('created', '0'),
        'duplicates_skipped': request.GET.get('skipped', '0'),
    }

    return render(request, 'news/list.html', context)

def populate_database(request):
    """Populate the database with articles from all categories, avoiding duplicates."""
    categories = ['politics', 'technology', 'business', 'sports', 'entertainment']
    total_articles = 0
    duplicates_skipped = 0
    
    for category in categories:
        articles = fetch_news_from_api(category, None)
        default_author = get_default_author()
        
        for article in articles:
            # Check if article with same URL already exists
            article_url = article.get('url', 'https://example.com')
            if NewsArticle.objects.filter(url=article_url).exists():
                duplicates_skipped += 1
                continue
                
            unique_id = f"{article.get('id')}_{timezone.now().timestamp()}"
            
            category_map = {
                'politics': 'POL',
                'technology': 'TECH',
                'business': 'BUS',
                'sports': 'SPO',
                'entertainment': 'ENT'
            }
            
            article_category = category_map.get(article.get('category', '').lower(), 'POL')
            
            # Extract source name
            source_display = article.get('source', 'Unknown Source')
            if source_display == "Unknown Source" and article.get('url'):
                source_display = extract_source_from_url(article.get('url'))
            
            # Map source to your model's SOURCE_CHOICES if possible
            source_code = REVERSE_SOURCE_MAPPING.get(source_display.lower(), None)
            
            if not source_code:
                # If not in our mapping, store the original source name
                source_code = source_display[:4].upper()
                
                # Add to our mappings for future use
                if source_display and source_code not in SOURCE_NAME_MAPPING:
                    SOURCE_NAME_MAPPING[source_code] = source_display
                    REVERSE_SOURCE_MAPPING[source_display.lower()] = source_code
            
            NewsArticle.objects.create(
                api_source_id=unique_id,
                title=article.get('title', 'No title available'),
                content=article.get('description', 'No content available'),
                url=article_url,
                image=article.get('urlToImage', ''),
                source=source_code,
                category=article_category,
                author=default_author,
                created_at=timezone.make_aware(
                    datetime.strptime(article.get('publishedAt', timezone.now().strftime('%Y-%m-%dT%H:%M:%SZ')), 
                    '%Y-%m-%dT%H:%M:%SZ')
                ) if article.get('publishedAt') else timezone.now()
            )
            total_articles += 1
    
    return render(request, 'news/populate_success.html', {
        'total_articles': total_articles,
        'duplicates_skipped': duplicates_skipped,
        'categories': categories
    })