import requests
import json
from datetime import datetime
import os
import sys
from urllib.parse import quote
import argparse
import re

# NLP libraries
import spacy
from transformers import pipeline
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
import dateutil.parser
from datefinder import find_dates

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('maxent_ne_chunker')
    nltk.download('words')

class NLPAnalyzer:
    """Advanced NLP analysis using pre-trained models"""
    
    def __init__(self):
        print("🔄 Loading NLP models...")
        
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
            print("✅ spaCy model loaded")
        except:
            print("⚠️ spaCy model not found. Downloading...")
            os.system("python -m spacy download en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
        
        # Load zero-shot classification model
        try:
            self.classifier = pipeline("zero-shot-classification", 
                                     model="facebook/bart-large-mnli")
            print("✅ Zero-shot classifier loaded")
        except:
            print("⚠️ Could not load transformer model")
            self.classifier = None
        
        # Common news categories
        self.news_categories = [
            "politics", "conflict", "disaster", "economy", "health",
            "technology", "environment", "sports", "entertainment",
            "crime", "accident", "protest", "election", "diplomacy",
            "military", "terrorism", "human rights", "science"
        ]
        
    def extract_entities(self, text):
        """Extract named entities using spaCy"""
        doc = self.nlp(text)
        
        entities = {
            'PERSON': [],
            'ORG': [],  # Organizations
            'GPE': [],  # Geopolitical entities (countries, cities)
            'LOC': [],  # Locations
            'DATE': [],
            'TIME': [],
            'MONEY': [],
            'PERCENT': [],
            'EVENT': [],
            'LAW': [],
            'PRODUCT': []
        }
        
        for ent in doc.ents:
            if ent.label_ in entities:
                entities[ent.label_].append({
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char
                })
        
        return entities
    
    def extract_dates(self, text):
        """Extract dates using datefinder"""
        dates = []
        try:
            matches = list(find_dates(text))
            for match in matches:
                dates.append(match.strftime("%Y-%m-%d"))
        except:
            pass
        return dates
    
    def extract_keywords(self, text):
        """Extract important keywords using spaCy"""
        doc = self.nlp(text)
        
        # Extract nouns, proper nouns, and adjectives
        keywords = []
        for token in doc:
            if token.pos_ in ['NOUN', 'PROPN', 'ADJ'] and not token.is_stop:
                keywords.append(token.text.lower())
        
        # Get noun chunks (phrases)
        phrases = [chunk.text.lower() for chunk in doc.noun_chunks]
        
        return list(set(keywords)), list(set(phrases))
    
    def classify_claim(self, text):
        """Classify the claim into categories"""
        if self.classifier:
            result = self.classifier(text, self.news_categories)
            return {
                'categories': result['labels'][:3],
                'scores': result['scores'][:3]
            }
        else:
            # Fallback to simple keyword matching
            categories = []
            text_lower = text.lower()
            for category in self.news_categories:
                if category in text_lower:
                    categories.append(category)
            return {
                'categories': categories[:3],
                'scores': [1.0] * len(categories[:3])
            }
    
    def extract_relationships(self, text):
        """Extract subject-verb-object relationships"""
        doc = self.nlp(text)
        
        relationships = []
        for token in doc:
            if token.dep_ in ('nsubj', 'nsubjpass') and token.head.pos_ == 'VERB':
                subject = token.text
                verb = token.head.text
                # Find object
                obj = None
                for child in token.head.children:
                    if child.dep_ in ('dobj', 'pobj', 'attr'):
                        obj = child.text
                        break
                
                if obj:
                    relationships.append({
                        'subject': subject,
                        'verb': verb,
                        'object': obj
                    })
        
        return relationships

class ClaimSearchOptimizer:
    """Optimizes search terms based on NLP analysis"""
    
    def __init__(self):
        self.nlp_analyzer = NLPAnalyzer()
        
    def analyze_claim(self, claim):
        """Comprehensive claim analysis"""
        print("\n" + "="*70)
        print("🔍 CLAIM ANALYSIS")
        print("="*70)
        
        # Extract entities
        entities = self.nlp_analyzer.extract_entities(claim)
        print(f"\n📌 Named Entities:")
        for entity_type, entity_list in entities.items():
            if entity_list:
                values = [e['text'] for e in entity_list]
                print(f"   {entity_type}: {', '.join(values)}")
        
        # Extract dates
        dates = self.nlp_analyzer.extract_dates(claim)
        if dates:
            print(f"\n📅 Dates found: {', '.join(dates)}")
        
        # Extract keywords and phrases
        keywords, phrases = self.nlp_analyzer.extract_keywords(claim)
        print(f"\n🔑 Keywords: {', '.join(keywords[:10])}")
        if phrases:
            print(f"📝 Key phrases: {', '.join(phrases[:5])}")
        
        # Classify claim
        classification = self.nlp_analyzer.classify_claim(claim)
        print(f"\n🏷️ Categories:")
        for cat, score in zip(classification['categories'], classification['scores']):
            print(f"   • {cat} ({score:.2f})")
        
        # Extract relationships
        relationships = self.nlp_analyzer.extract_relationships(claim)
        if relationships:
            print(f"\n🔄 Relationships found:")
            for rel in relationships[:3]:
                print(f"   • {rel['subject']} {rel['verb']} {rel['object']}")
        
        return {
            'claim': claim,
            'entities': entities,
            'dates': dates,
            'keywords': keywords,
            'phrases': phrases,
            'categories': classification['categories'],
            'category_scores': classification['scores'],
            'relationships': relationships
        }
    
    def generate_search_terms(self, analysis):
        """Generate optimized search terms based on analysis"""
        search_terms = []
        term_weights = {}  # Store weight for each term
        
        # 1. Person names (highest weight)
        for person in analysis['entities'].get('PERSON', []):
            term = person['text']
            search_terms.append(term)
            term_weights[term] = 1.0
        
        # 2. Organizations
        for org in analysis['entities'].get('ORG', []):
            term = org['text']
            search_terms.append(term)
            term_weights[term] = 0.9
        
        # 3. Locations/Countries
        for loc in analysis['entities'].get('GPE', []):
            term = loc['text']
            search_terms.append(term)
            term_weights[term] = 0.9
        for loc in analysis['entities'].get('LOC', []):
            term = loc['text']
            search_terms.append(term)
            term_weights[term] = 0.8
        
        # 4. Events
        for event in analysis['entities'].get('EVENT', []):
            term = event['text']
            search_terms.append(term)
            term_weights[term] = 0.9
        
        # 5. Key phrases
        for phrase in analysis['phrases'][:5]:  # Limit to top 5 phrases
            if len(phrase.split()) > 1:  # Only multi-word phrases
                search_terms.append(phrase)
                term_weights[phrase] = 0.7
        
        # 6. Individual keywords (lower weight)
        for keyword in analysis['keywords'][:10]:
            if keyword not in [t.lower() for t in search_terms]:
                search_terms.append(keyword)
                term_weights[keyword] = 0.5
        
        # 7. Add date if present
        if analysis['dates']:
            date_term = analysis['dates'][0]
            search_terms.append(date_term)
            term_weights[date_term] = 0.6
        
        # Remove duplicates while preserving order
        unique_terms = []
        seen = set()
        for term in search_terms:
            if term.lower() not in seen:
                unique_terms.append(term)
                seen.add(term.lower())
        
        return unique_terms, term_weights

# Modified GoogleCSESearcher class with your existing code plus these additions

class GoogleCSESearcher:
    """Class to handle Google CSE API searches with different configurations"""
    
    def __init__(self, config_name="gmanetwork"):
        """
        Initialize with specific CSE configuration
        
        Args:
            config_name (str): 'gmanetwork' or 'inquirer'
        """
        self.config_name = config_name
        self.base_url = "https://cse.google.com/cse/element/v1"
        self.headers = self._get_headers()
        self.base_params = self._get_base_params()
        self.claim_optimizer = ClaimSearchOptimizer()
        
        # Create output directory if it doesn't exist
        self.output_dir = os.path.join("ScrapedNews", "Scraped")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set fixed filename based on config
        if self.config_name == "gmanetwork":
            self.fixed_filename = "gma.json"
        else:  # inquirer
            self.fixed_filename = "inquirer.json"
        
        print(f"📁 Will save to: {os.path.join(self.output_dir, self.fixed_filename)}")
    
    def _get_headers(self):
        """Get headers (same for both configs)"""
        return {
            'authority': 'cse.google.com',
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'en,en-US;q=0.9,uk;q=0.8,zh-TW;q=0.7,zh;q=0.6,as;q=0.5',
            'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'script',
            'sec-fetch-mode': 'no-cors',
            'sec-fetch-site': 'cross-site',
            'sec-fetch-storage-access': 'active',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36',
            'x-browser-channel': 'stable',
            'x-browser-copyright': 'Copyright 2026 Google LLC. All Rights reserved.',
            'x-browser-validation': 'mGtxj/IERUi4uQ9hLSvZZF4DQgA=',
            'x-browser-year': '2026',
            'x-client-data': 'CJC2yQEIprbJAQipncoBCP3nygEIlqHLAQiFoM0BGJ6wzwE='
        }
    
    def _get_base_params(self):
        """Get base parameters based on configuration"""
        if self.config_name == "gmanetwork":
            return {
                'rsz': 'filtered_cse',
                'num': '10',
                'hl': 'en',
                'source': 'gcsc',
                'cselibv': '61bbf1f9762e96cd',
                'cx': '017416762253162668457:um3ldanwe9s',
                'safe': 'off',
                'cse_tok': 'AEXjvhJ_U5ngwFMSUBf2RIMALtld:1773625620430',
                'filter': '1',
                'sort': '',
                'exp': 'cc,apo',
                'fexp': '73152290,73152291',
                'gs_l': 'partner-generic.3...240136.242786.0.243365.0.0.0.0.0.0.0.0..0.0.csems,nrl=10...0....1.34.partner-generic..0.0.0.',
                'callback': 'google.search.cse.api3984',
                'rurl': 'https://www.gmanetwork.com/news/search/?q=israel#gsc.tab=0&gsc.q=israel&gsc.page=3'
            }
        elif self.config_name == "inquirer":
            return {
                'rsz': 'filtered_cse',
                'num': '10',
                'hl': 'en',
                'source': 'gcsc',
                'cselibv': '61bbf1f9762e96cd',
                'cx': 'partner-pub-3470805887229135:3785249262',
                'safe': 'active',
                'cse_tok': 'AEXjvhIncno2BE5wrlIK4jjpzOo8:1773625708470',
                'sort': '',
                'exp': 'cc,apo',
                'fexp': '73152292,73152290',
                'gs_l': 'partner-generic.3...1120226.1121789.0.1123099.7.7.0.0.0.0.290.878.3j3j1.7.0.csems,nrl=10...0....1.34.partner-generic..5.2.391.qKLA8d9l1RI',
                'callback': 'google.search.cse.api11831',
                'rurl': 'https://www.inquirer.net/search/?q=iran'
            }
        else:
            raise ValueError(f"Unknown config: {self.config_name}")
    
    def search_with_claim(self, claim):
        """Analyze claim and perform optimized searches"""
        print("\n" + "="*70)
        print("🔬 CLAIM VERIFICATION SYSTEM")
        print("="*70)
        
        # Step 1: Analyze the claim
        print("\n📊 STEP 1: Analyzing claim...")
        analysis = self.claim_optimizer.nlp_analyzer.extract_entities(claim)
        
        # Step 2: Generate search terms
        print("\n🎯 STEP 2: Generating optimized search terms...")
        search_terms, weights = self.claim_optimizer.generate_search_terms(
            self.claim_optimizer.analyze_claim(claim)
        )
        
        print("\n📋 Generated search terms (with weights):")
        for i, term in enumerate(search_terms[:5], 1):
            print(f"   {i}. '{term}' (weight: {weights.get(term, 0.5):.1f})")
        
        # Step 3: Perform searches
        print("\n🔍 STEP 3: Performing searches...")
        all_results = []
        
        for term in search_terms[:3]:  # Use top 3 search terms
            print(f"\n   Searching for: '{term}'")
            result = self.search(term, save_files=False)  # Don't save individual searches
            if result and isinstance(result, dict) and 'results' in result:
                for article in result['results']:
                    article['search_term'] = term
                    article['term_weight'] = weights.get(term, 0.5)
                    all_results.append(article)
        
        # Step 4: Rank and filter results
        print("\n📊 STEP 4: Ranking results...")
        
        # Calculate relevance scores
        for article in all_results:
            relevance_score = 0
            title = article.get('title', '').lower()
            content = article.get('content', '').lower()
            full_text = title + " " + content
            
            # Check for entity matches
            for entity_type, entity_list in analysis.items():
                for entity in entity_list:
                    if entity['text'].lower() in full_text:
                        relevance_score += 2  # Entity matches are valuable
            
            # Check for keyword matches
            for keyword in search_terms[:10]:
                if keyword.lower() in full_text:
                    relevance_score += 1
            
            article['relevance_score'] = relevance_score
        
        # Sort by relevance
        all_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Step 5: Display results
        print("\n" + "="*70)
        print(f"📋 TOP {min(5, len(all_results))} MATCHING ARTICLES:")
        print("="*70)
        
        for i, article in enumerate(all_results[:5], 1):
            print(f"\n{i}. [{article.get('visibleUrl', 'Unknown')}]")
            print(f"   Title: {article.get('title', 'N/A')[:100]}")
            print(f"   Relevance: {article.get('relevance_score', 0)}")
            print(f"   URL: {article.get('unescapedUrl', article.get('url', 'N/A'))}")
        
        # Save combined results
        self._save_combined_results(claim, analysis, search_terms, all_results)
        
        return all_results
    
    def _save_combined_results(self, claim, analysis, search_terms, results):
        """Save comprehensive analysis results"""
        output = {
            'timestamp': datetime.now().isoformat(),
            'claim': claim,
            'analysis': analysis,
            'search_terms': search_terms,
            'results': results[:20]  # Save top 20 results
        }
        
        filepath = os.path.join(self.output_dir, f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Full analysis saved to: {filepath}")
    
    def search(self, search_term, save_files=True):
        """Original search method (keep your existing implementation)"""
        # Your existing search method here
        params = self.base_params.copy()
        params['q'] = search_term
        params['oq'] = search_term
        
        timestamp = datetime.now().strftime("%H%M%S")
        params['callback'] = f"google.search.cse.api{timestamp}"
        
        if self.config_name == "gmanetwork":
            params['rurl'] = f'https://www.gmanetwork.com/news/search/?q={quote(search_term)}#gsc.tab=0&gsc.q={quote(search_term)}&gsc.page=3'
        else:
            params['rurl'] = f'https://www.inquirer.net/search/?q={quote(search_term)}'
        
        try:
            print(f"   Fetching data from Google CSE API...")
            response = requests.get(self.base_url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = self._process_response(response)
            
            if save_files:
                self._save_response(data, search_term)
            
            return data
            
        except Exception as e:
            print(f"   ❌ Search failed: {e}")
            return None
    
    def _process_response(self, response):
        """Process the response (handle JSONP)"""
        response_text = response.text
        
        callback_pattern = r'^google\.search\.cse\.api\d+\((.*)\)$'
        match = re.match(callback_pattern, response_text, re.DOTALL)
        
        if match:
            json_str = match.group(1)
            try:
                return json.loads(json_str)
            except:
                return response_text
        else:
            try:
                return response.json()
            except:
                return response_text
    
    def _save_response(self, data, search_term):
        """Save response to file"""
        try:
            filepath = os.path.join(self.output_dir, self.fixed_filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                if isinstance(data, (dict, list)):
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    f.write(str(data))
            
            return True
        except Exception as e:
            print(f"❌ Error saving file: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Search Google CSE API with claim analysis')
    parser.add_argument('--config', '-c', choices=['gmanetwork', 'inquirer', 'both'], 
                       default='both', help='CSE configuration to use')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🔬 AI-Powered Claim Verification System")
    print("=" * 70)
    
    # Get claim from user
    print("\n📝 Enter your claim to verify:")
    claim = input("Claim: ").strip()
    
    if not claim:
        print("❌ No claim entered. Exiting.")
        return
    
    # Determine which configs to use
    if args.config == 'both':
        configs = ['gmanetwork', 'inquirer']
    else:
        configs = [args.config]
    
    all_results = {}
    
    for config in configs:
        print("\n" + "=" * 70)
        print(f"📰 Searching {config.upper()}...")
        print("=" * 70)
        
        searcher = GoogleCSESearcher(config)
        results = searcher.search_with_claim(claim)
        all_results[config] = results
    
    print("\n" + "=" * 70)
    print("✅ Claim verification complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()