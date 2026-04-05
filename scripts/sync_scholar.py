import os
import re
import yaml
from datetime import datetime
from scholarly import scholarly, ProxyGenerator

# Configuration
SCHOLAR_ID = "MhlvmB4AAAAJ"
PUBLICATIONS_DIR = "_publications"
# For templates that use year subfolders, set this to True
USE_YEAR_FOLDERS = True 

def clean_filename(title):
    """Sanitize title for filename."""
    return re.sub(r'[^\w\s-]', '', title).strip().lower().replace(' ', '_')[:50]

def normalize_title(title):
    """Normalize title for reliable comparison."""
    return re.sub(r'[^a-zA-Z0-9]', '', title).lower().strip()

def get_existing_titles():
    """Scan the publications directory for existing paper titles to avoid duplicates."""
    titles = set()
    if not os.path.exists(PUBLICATIONS_DIR):
        return titles
    
    for root, dirs, files in os.walk(PUBLICATIONS_DIR):
        for file in files:
            if file.endswith(".md"):
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    content = f.read()
                    match = re.search(r'^title:\s*["\']?(.*?)["\']?$', content, re.MULTILINE)
                    if match:
                        titles.add(normalize_title(match.group(1)))
    return titles

def sync():
    print(f"Starting sync for Scholar ID: {SCHOLAR_ID}")
    
    # Set up proxy (optional but recommended for CI/CD)
    # pg = ProxyGenerator()
    # pg.FreeProxies()
    # scholarly.use_proxy(pg)

    author = scholarly.search_author_id(SCHOLAR_ID)
    scholarly.fill(author, sections=['publications'])
    
    existing_titles = get_existing_titles()
    new_count = 0

    for pub in author['publications']:
        # Fetch full publication details
        scholarly.fill(pub)
        bib = pub['bib']
        
        title = bib.get('title', 'Unknown Title')
        norm_title = normalize_title(title)
        if norm_title in existing_titles:
            print(f"Skipping duplicate: {title}")
            continue
            
        year = bib.get('pub_year', str(datetime.now().year))
        venue = bib.get('venue', bib.get('journal', ''))
        authors = bib.get('author', '').split(' and ')
        abstract = bib.get('abstract', '')
        pub_url = pub.get('pub_url', '')

        # Construct front matter for luost26/academic-homepage
        # Note: adjust fields as needed for specific template requirements
        front_matter = {
            'title': title,
            'date': f"{year}-01-01",
            'pub': venue,
            'authors': authors,
            'abstract': abstract,
            'selected': False, # Default to false, manual curation suggested
            'links': {}
        }
        
        if pub_url:
            front_matter['links']['pdf'] = pub_url

        # Determine path
        target_dir = PUBLICATIONS_DIR
        if USE_YEAR_FOLDERS:
            target_dir = os.path.join(PUBLICATIONS_DIR, str(year))
        
        os.makedirs(target_dir, exist_ok=True)
        
        filename = f"{clean_filename(title)}.md"
        filepath = os.path.join(target_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("---\n")
            yaml.dump(front_matter, f, sort_keys=False, default_flow_style=False, allow_unicode=True)
            f.write("---\n")
            
        print(f"New publication added: {title}")
        new_count += 1
        existing_titles.add(title.lower().strip())

    print(f"Sync complete. Added {new_count} new publications.")

if __name__ == "__main__":
    sync()
