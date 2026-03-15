import json
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from typing import List, Dict, Any
import os

# Download required NLTK data (run once)
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')
    nltk.download('punkt_tab')

class NewsSearcher:
    def __init__(self, json_file_path: str):
        """
        Initialize the searcher with the path to gma.json file
        """
        self.json_file_path = json_file_path
        self.news_data = self._load_json_data()
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
    def _parse_jsonp(self, content: str) -> dict:
        """
        Parse JSONP content by extracting the JSON object from the function call
        """
        # Remove the leading /*O_o*/ comment if present
        content = re.sub(r'^\/\*.*?\*\/\s*', '', content)
        
        # Find the JSON object between the function call parentheses
        # Pattern matches: functionName({...});
        match = re.search(r'[\w\.]+\((.*)\);?\s*$', content, re.DOTALL)
        if match:
            json_str = match.group(1)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # If that fails, try to find anything that looks like JSON
                pass
        
        # Try to find anything that looks like a JSON object
        match = re.search(r'({.*})', content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        raise json.JSONDecodeError("Could not parse JSONP content", content, 0)
    
    def _load_json_data(self) -> List[Dict[str, Any]]:
        """
        Load and parse the gma.json file (handles both pure JSON and JSONP)
        """
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as file:
                content = file.read().strip()
                
                # Try parsing as pure JSON first
                try:
                    data = json.loads(content)
                except json.JSONDecodeError:
                    # If that fails, try parsing as JSONP
                    print("Detected JSONP format, attempting to parse...")
                    data = self._parse_jsonp(content)
                
                # Extract the results from the Google CSE API response format
                if isinstance(data, dict):
                    if 'results' in data:
                        return data['results']
                    elif 'items' in data:
                        return data['items']
                    elif 'responseData' in data and isinstance(data['responseData'], dict):
                        if 'results' in data['responseData']:
                            return data['responseData']['results']
                
                # If data is a list, return it directly
                if isinstance(data, list):
                    return data
                
                print(f"Warning: Unexpected JSON structure in {self.json_file_path}")
                print("Data keys:", list(data.keys()) if isinstance(data, dict) else "Not a dictionary")
                return []
                
        except FileNotFoundError:
            print(f"Error: File {self.json_file_path} not found.")
            return []
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON/JSONP in {self.json_file_path}")
            print(f"Details: {e}")
            print("\nFirst 200 characters of file:")
            try:
                with open(self.json_file_path, 'r', encoding='utf-8') as file:
                    print(file.read(200) + "...")
            except:
                pass
            return []
    
    def preprocess_text(self, text: str) -> str:
        """
        Clean and preprocess text by removing stopwords and lemmatizing
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and numbers (keep only letters and spaces)
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords and lemmatize
        processed_tokens = [
            self.lemmatizer.lemmatize(token) 
            for token in tokens 
            if token not in self.stop_words and len(token) > 2
        ]
        
        return ' '.join(processed_tokens)
    
    def user_description_search(self, user_input: str, threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        Search through news articles based on user description
        Returns articles that match the processed user input
        """
        # Preprocess user input
        processed_query = self.preprocess_text(user_input)
        query_words = set(processed_query.split())
        
        if not query_words:
            print("No valid search terms after preprocessing.")
            return []
        
        print(f"\nProcessed search query: {processed_query}")
        print(f"Searching for articles containing these terms...\n")
        
        matching_articles = []
        
        for article in self.news_data:
            # Get content from contentNoFormatting or content field
            content = article.get('contentNoFormatting', '')
            if not content:
                content = article.get('content', '')
            
            # Also check title for matches
            title = article.get('titleNoFormatting', '') or article.get('title', '')
            
            if content or title:
                # Combine title and content for better matching
                full_text = f"{title} {content}".strip()
                
                # Preprocess article content
                processed_content = self.preprocess_text(full_text)
                content_words = set(processed_content.split())
                
                # Calculate match score (percentage of query words found in content)
                if content_words:
                    common_words = query_words.intersection(content_words)
                    match_score = len(common_words) / len(query_words)
                    
                    if match_score >= threshold:
                        matching_articles.append({
                            'article': article,
                            'match_score': match_score,
                            'matched_terms': list(common_words)
                        })
        
        # Sort by match score (highest first)
        matching_articles.sort(key=lambda x: x['match_score'], reverse=True)
        
        return matching_articles
    
    def display_results(self, results: List[Dict[str, Any]], max_results: int = 5):
        """
        Display search results in a readable format
        """
        if not results:
            print("No matching articles found.")
            return
        
        print(f"Found {len(results)} matching articles (showing top {min(max_results, len(results))}):\n")
        print("=" * 80)
        
        for i, result in enumerate(results[:max_results], 1):
            article = result['article']
            print(f"\n--- Result {i} (Match Score: {result['match_score']:.2%}) ---")
            
            # Try different possible title fields
            title = (article.get('titleNoFormatting') or 
                    article.get('title') or 
                    article.get('richSnippet', {}).get('metatags', {}).get('ogTitle', 'N/A'))
            print(f"Title: {title}")
            
            # Try to get date
            date = (article.get('richSnippet', {}).get('metatags', {}).get('ogPubdate') or
                   article.get('publishedDate', 'N/A'))
            print(f"Date/Time: {date}")
            
            print(f"URL: {article.get('url', 'N/A')}")
            print(f"Matched terms: {', '.join(result['matched_terms'])}")
            
            # Get content snippet
            content = (article.get('contentNoFormatting') or 
                      article.get('content') or 
                      article.get('snippet', ''))
            if content:
                print(f"\nContent snippet:")
                # Clean HTML tags if present
                content = re.sub(r'<[^>]+>', '', content)
                print(f"{content[:200]}..." if len(content) > 200 else content)
            print("-" * 60)

def main():
    # Path to your gma.json file
    json_file_path = os.path.join('ScrapedNews', 'Scraped', 'gma.json')
    
    # Check if file exists
    if not os.path.exists(json_file_path):
        print(f"Error: Could not find {json_file_path}")
        print("Please make sure the file path is correct.")
        return
    
    print(f"Attempting to load: {json_file_path}")
    
    # Initialize searcher
    searcher = NewsSearcher(json_file_path)
    
    if not searcher.news_data:
        print("No news data loaded. Exiting.")
        return
    
    print("=" * 80)
    print("News Article Search Engine")
    print("=" * 80)
    print(f"Loaded {len(searcher.news_data)} articles from {json_file_path}")
    print("\nEnter a description of the news you're looking for.")
    print("Example: 'On January 12, 2026, Iranian President Masoud Pezeshkian alleged that the United States and Israel were trying to destabilize Iran'")
    print("Type 'quit' to exit.\n")
    
    while True:
        # Get user input
        user_input = input("\nEnter your description: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if not user_input:
            print("Please enter a valid description.")
            continue
        
        # Search for matching articles
        results = searcher.user_description_search(user_input)
        
        # Display results
        searcher.display_results(results)
        
        # Ask if user wants to see more results
        if len(results) > 5:
            see_more = input("\nSee more results? (y/n): ").strip().lower()
            if see_more == 'y':
                searcher.display_results(results, max_results=len(results))

if __name__ == "__main__":
    main()