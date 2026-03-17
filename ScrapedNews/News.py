import requests
import json
from datetime import datetime
import os
import sys
from urllib.parse import quote
import argparse

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
    
    def search(self, search_term, save_files=True):
        """
        Perform search for a given term
        
        Args:
            search_term (str): The term to search for
            save_files (bool): Whether to save response to files
        
        Returns:
            dict: Parsed response data
        """
        # Update parameters with the search term
        params = self.base_params.copy()
        params['q'] = search_term
        params['oq'] = search_term
        
        # Update callback to be unique for this request
        timestamp = datetime.now().strftime("%H%M%S")
        params['callback'] = f"google.search.cse.api{timestamp}"
        
        # Update rurl based on config
        if self.config_name == "gmanetwork":
            params['rurl'] = f'https://www.gmanetwork.com/news/search/?q={quote(search_term)}#gsc.tab=0&gsc.q={quote(search_term)}&gsc.page=3'
        else:  # inquirer
            params['rurl'] = f'https://www.inquirer.net/search/?q={quote(search_term)}'
        
        try:
            # Make the request
            print(f"🔍 [{self.config_name}] Searching for: '{search_term}'")
            print("Fetching data from Google CSE API...")
            print(f"URL: {self.base_url}")
            print(f"Params: {params}")
            
            response = requests.get(self.base_url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            print(f"✅ Response received! Status code: {response.status_code}")
            print(f"Response size: {len(response.text):,} bytes")
            
            # Process response
            data = self._process_response(response)
            
            if save_files:
                success = self._save_response(data, search_term)
                if success:
                    print(f"✅ File saved successfully!")
                else:
                    print(f"❌ Failed to save file!")
            
            # Print preview
            if data:
                self._print_preview(data)
            else:
                print("⚠️ No data to preview")
            
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status code: {e.response.status_code}")
                print(f"Response text: {e.response.text[:500]}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _process_response(self, response):
        """Process the response (handle JSONP)"""
        response_text = response.text
        
        # Try to extract JSON from JSONP callback
        import re
        callback_pattern = r'^google\.search\.cse\.api\d+\((.*)\)$'
        match = re.match(callback_pattern, response_text, re.DOTALL)
        
        if match:
            json_str = match.group(1)
            try:
                # Try to parse the JSON
                data = json.loads(json_str)
                print("✅ Successfully parsed JSONP response")
                return data
            except json.JSONDecodeError as e:
                print(f"⚠️ Failed to parse JSONP: {e}")
                # Return the raw text if JSON parsing fails
                return response_text
        else:
            try:
                # Try to parse as regular JSON
                data = response.json()
                print("✅ Successfully parsed JSON response")
                return data
            except json.JSONDecodeError:
                print("⚠️ Response is not JSON, saving as text")
                return response_text
    
    def _save_response(self, data, search_term):
        """Save response to ScrapedNews/Scraped directory with fixed filenames"""
        try:
            filepath = os.path.join(self.output_dir, self.fixed_filename)
            
            print(f"💾 Attempting to save to: {filepath}")
            
            # Save parsed JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                if isinstance(data, (dict, list)):
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    print(f"📝 Saved as formatted JSON")
                else:
                    f.write(str(data))
                    print(f"📝 Saved as text")
            
            # Check if file was created and get size
            if os.path.exists(filepath):
                json_size = os.path.getsize(filepath)
                print(f"📁 File exists: {filepath}")
                print(f"📊 File size: {json_size:,} bytes")
                
                # Verify file can be read back
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"✅ Verified file can be read ({len(content):,} characters)")
                
                return True
            else:
                print(f"❌ File was not created: {filepath}")
                return False
                
        except Exception as e:
            print(f"❌ Error saving file: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _print_preview(self, data):
        """Print a preview of the results"""
        print("\n📄 Preview:")
        if isinstance(data, dict):
            # Print top-level keys
            print(f"Top-level keys: {list(data.keys())}")
            
            if 'results' in data:
                print(f"Found {len(data['results'])} results")
                for i, result in enumerate(data['results'][:3], 1):
                    title = result.get('title', 'No title')
                    print(f"  {i}. {title[:80]}...")
            elif 'items' in data:
                print(f"Found {len(data['items'])} items")
                for i, item in enumerate(data['items'][:3], 1):
                    title = item.get('title', 'No title')
                    print(f"  {i}. {title[:80]}...")
            else:
                # Print first few items of the response
                preview = json.dumps(data, indent=2, ensure_ascii=False)[:500]
                print(preview + "..." if len(json.dumps(data)) > 500 else preview)
        else:
            preview = str(data)[:500]
            print(preview + "..." if len(str(data)) > 500 else preview)

def search_all_configs(search_term, configs=None):
    """Search using multiple CSE configurations"""
    if configs is None:
        configs = ['gmanetwork', 'inquirer']
    
    results = {}
    for config in configs:
        print("\n" + "=" * 60)
        print(f"🔧 Using config: {config}")
        searcher = GoogleCSESearcher(config)
        results[config] = searcher.search(search_term)
        print("=" * 60)
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Search Google CSE API with different configurations')
    parser.add_argument('terms', nargs='*', help='Search terms')
    parser.add_argument('--config', '-c', choices=['gmanetwork', 'inquirer', 'both'], 
                       default='both', help='CSE configuration to use')
    parser.add_argument('--file', '-f', help='File containing search terms (one per line)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Google CSE API Response Fetcher")
    print("=" * 60)
    print(f"📁 Output directory: {os.path.abspath('ScrapedNews/Scraped')}")
    print("📁 Files will be saved as:")
    print("   - ScrapedNews/Scraped/gma.json")
    print("   - ScrapedNews/Scraped/inquirer.json")
    print("=" * 60)
    
    # Verify directory exists and is writable
    output_dir = os.path.join("ScrapedNews", "Scraped")
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
            print(f"✅ Created directory: {output_dir}")
        except Exception as e:
            print(f"❌ Failed to create directory: {e}")
            return
    
    # Test write permissions
    test_file = os.path.join(output_dir, "test_write.txt")
    try:
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print("✅ Directory is writable")
    except Exception as e:
        print(f"❌ Directory is not writable: {e}")
        return
    
    # Determine search terms
    search_terms = []
    
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                search_terms = [line.strip() for line in f if line.strip()]
            print(f"📋 Loaded {len(search_terms)} terms from {args.file}")
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return
    
    if args.terms:
        search_terms.extend(args.terms)
    
    # If no terms provided, use interactive mode
    if not search_terms:
        print("\nEnter search terms (comma-separated for multiple):")
        user_input = input("Search for: ").strip()
        
        if not user_input:
            search_terms = ["iran"]  # Default
        elif ',' in user_input:
            search_terms = [term.strip() for term in user_input.split(',')]
        else:
            search_terms = [user_input]
    
    # Determine which configs to use
    if args.config == 'both':
        configs = ['gmanetwork', 'inquirer']
    else:
        configs = [args.config]
    
    # Perform searches
    for term in search_terms:
        print(f"\n🔍 Processing search term: '{term}'")
        if len(configs) == 1:
            print("\n" + "=" * 60)
            searcher = GoogleCSESearcher(configs[0])
            result = searcher.search(term)
            if result:
                print(f"✅ Search completed for {configs[0]}")
            else:
                print(f"❌ Search failed for {configs[0]}")
            print("=" * 60)
        else:
            results = search_all_configs(term, configs)
            for config, result in results.items():
                if result:
                    print(f"✅ {config}: Success")
                else:
                    print(f"❌ {config}: Failed")
    
    print("\n" + "=" * 60)
    print("Process completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()