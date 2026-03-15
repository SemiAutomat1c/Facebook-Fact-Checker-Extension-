import json
import os
import glob
import re
from sentence_transformers import SentenceTransformer, util
import torch

class ClaimVerifier:
    def __init__(self):
        # Load a model specifically fine-tuned for claim matching
        print("🔄 Loading pre-trained claim matching model...")
        self.model = SentenceTransformer("Sami92/multiling-e5-large-instruct-claim-matching")
        
        self.data_dir = os.path.join("ScrapedNews", "Scraped")
        print("✅ Model loaded!")
    
    def clean_json_content(self, content):
        """Clean JSON content by removing JavaScript wrapper if present"""
        content = content.strip()
        
        # Try to parse as pure JSON first
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Remove JavaScript wrapper - pattern matches: functionName({ ... });
        match = re.search(r'\(\s*(\{.*\})\s*\)\s*;', content, re.DOTALL)
        if match:
            json_str = match.group(1)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Try to find anything between { and }
        start = content.find('{')
        end = content.rfind('}') + 1
        if start != -1 and end > start:
            json_str = content[start:end]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # If all attempts fail
        raise ValueError(f"Could not extract valid JSON from content: {content[:100]}...")
    
    def encode_texts(self, texts, is_query=False):
        """Encode texts using the appropriate prompt format"""
        if is_query:
            # The model expects specific prompts for queries
            return self.model.encode(
                texts, 
                prompt="Instruct: Retrieve semantically similar text.\nQuery: ",
                convert_to_tensor=True
            )
        else:
            return self.model.encode(texts, convert_to_tensor=True)
    
    def verify_claim(self, claim, threshold=0.6, show_all_matches=True):
        """
        Verify claim and return matching articles with scores
        
        Args:
            claim: The claim to verify
            threshold: Similarity threshold (0-1)
            show_all_matches: Whether to show all matches or just top
        
        Returns:
            Dictionary with verification results and matching articles
        """
        print(f"\n🔍 Verifying: '{claim}'")
        print("="*70)
        
        # Load all articles
        articles = []
        article_texts = []
        
        json_files = glob.glob(os.path.join(self.data_dir, "*.json"))
        print(f"📁 Processing {len(json_files)} files...")
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Clean and parse the JSON content
                data = self.clean_json_content(content)
                
                if 'results' in data:
                    for result in data['results']:
                        # Extract article text
                        title = result.get('titleNoFormatting', '')
                        content_text = result.get('contentNoFormatting', '')
                        
                        # Get description from richSnippet if available
                        description = ''
                        if 'richSnippet' in result and 'metatags' in result['richSnippet']:
                            description = result['richSnippet']['metatags'].get('ogDescription', '')
                        
                        text = ' '.join([title, content_text, description])
                        
                        if text.strip():
                            articles.append({
                                'title': title,
                                'url': result.get('unescapedUrl', ''),
                                'source': result.get('visibleUrl', ''),
                                'description': description,
                                'full_text': text
                            })
                            article_texts.append(text)
            except Exception as e:
                print(f"⚠️ Error processing {json_file}: {e}")
                continue
        
        if not article_texts:
            print("❌ No articles found in database")
            return {
                'claim': claim,
                'verified': False,
                'score': 0,
                'matches': [],
                'total_articles': 0
            }
        
        print(f"📚 Loaded {len(articles)} articles from database")
        
        # Encode claim and articles
        print("🔄 Computing semantic similarities...")
        claim_embedding = self.encode_texts([claim], is_query=True)
        article_embeddings = self.encode_texts(article_texts)
        
        # Calculate cosine similarities
        similarities = util.cos_sim(claim_embedding, article_embeddings)[0]
        
        # Find all matches above threshold
        matches = []
        all_scores = []
        
        for idx, score in enumerate(similarities):
            all_scores.append({
                'score': float(score),
                'title': articles[idx]['title'],
                'url': articles[idx]['url'],
                'source': articles[idx]['source'],
                'description': articles[idx]['description']
            })
            
            if score > threshold:
                matches.append({
                    'score': float(score),
                    'title': articles[idx]['title'],
                    'url': articles[idx]['url'],
                    'source': articles[idx]['source'],
                    'description': articles[idx]['description']
                })
        
        # Sort all by similarity score
        all_scores.sort(key=lambda x: x['score'], reverse=True)
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        # Display results
        print("\n" + "="*70)
        print("📊 VERIFICATION RESULTS")
        print("="*70)
        
        if matches:
            print(f"\n✅ Found {len(matches)} matching articles (threshold: {threshold:.0%})")
            print(f"🎯 Top match score: {matches[0]['score']:.2%}\n")
            
            # Show top matches
            print("📰 TOP MATCHING ARTICLES:")
            print("-"*70)
            
            for i, match in enumerate(matches[:5], 1):  # Show top 5
                print(f"\n{i}. Score: {match['score']:.2%}")
                print(f"   Title: {match['title']}")
                print(f"   Source: {match['source']}")
                print(f"   URL: {match['url']}")
                if match['description']:
                    print(f"   Preview: {match['description'][:150]}...")
            
            if len(matches) > 5:
                print(f"\n... and {len(matches) - 5} more matches")
            
            # Determine verification level
            top_score = matches[0]['score']
            if top_score > 0.85:
                verification_level = "VERIFIED ✅"
                explanation = "Strong match with existing news articles"
            elif top_score > 0.75:
                verification_level = "LIKELY TRUE ✓"
                explanation = "Good match with existing news articles"
            elif top_score > 0.65:
                verification_level = "POSSIBLY TRUE ⚠️"
                explanation = "Moderate match - may be partially accurate"
            else:
                verification_level = "WEAK SUPPORT ❓"
                explanation = "Some related articles but weak direct match"
            
            print("\n" + "="*70)
            print(f"📌 VERDICT: {verification_level}")
            print(f"📈 Confidence: {top_score:.2%}")
            print(f"💡 Explanation: {explanation}")
            
        else:
            print("\n❌ No matching articles found above threshold")
            
            # Show closest matches even if below threshold
            print("\n📊 CLOSEST ARTICLES (below threshold):")
            print("-"*70)
            for i, match in enumerate(all_scores[:3], 1):
                print(f"\n{i}. Score: {match['score']:.2%}")
                print(f"   Title: {match['title']}")
                print(f"   Source: {match['source']}")
            
            print("\n" + "="*70)
            print("📌 VERDICT: UNVERIFIED ❓")
            print(f"📈 Confidence: {all_scores[0]['score']:.2%} (below threshold)")
            print("💡 Explanation: No strong matches found in database")
        
        print("="*70)
        
        return {
            'claim': claim,
            'verified': len(matches) > 0,
            'top_score': matches[0]['score'] if matches else 0,
            'matches': matches[:5] if matches else [],
            'closest_matches': all_scores[:3] if not matches else [],
            'total_matches': len(matches),
            'total_articles': len(articles)
        }

def interactive_verifier():
    """Interactive mode to verify multiple claims"""
    print("\n" + "="*70)
    print("🤖 CLAIM VERIFIER - Interactive Mode")
    print("="*70)
    print("Enter claims to verify against your news database")
    print("Type 'quit' to exit")
    print("-"*70)
    
    verifier = ClaimVerifier()
    
    while True:
        print("\n" + "-"*70)
        claim = input("Enter claim to verify: ").strip()
        
        if claim.lower() in ['quit', 'exit', 'q']:
            print("Goodbye! 👋")
            break
        
        if not claim:
            continue
        
        # Verify the claim
        result = verifier.verify_claim(claim, threshold=0.6)
        
        # Optional: Ask if user wants to see all matches
        if result['matches'] and len(result['matches']) > 0:
            print("\n" + "-"*70)
            see_all = input("Show all matches? (y/n): ").strip().lower()
            if see_all == 'y':
                print("\n📰 ALL MATCHES:")
                for i, match in enumerate(result['matches'], 1):
                    print(f"\n{i}. Score: {match['score']:.2%}")
                    print(f"   Title: {match['title']}")
                    print(f"   URL: {match['url']}")

# Test with your specific claim
def test_specific_claim():
    """Test a specific claim and show which news articles match"""
    verifier = ClaimVerifier()
    
    # Your claim
    claim = "Iranian Missiles Impact Occupied Jerusalem & Hezbollah Rockets Hit Haifa"
    
    # Verify and show matches
    result = verifier.verify_claim(claim, threshold=0.5)  # Lower threshold to see more matches
    
    return result

if __name__ == "__main__":
    # Choose which mode to run
    print("\n🔍 CLAIM VERIFIER")
    print("1. Test specific claim (Iranian Missiles...)")
    print("2. Interactive mode (enter your own claims)")
    print("3. Exit")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == '1':
        test_specific_claim()
    elif choice == '2':
        interactive_verifier()
    else:
        print("Goodbye! 👋")