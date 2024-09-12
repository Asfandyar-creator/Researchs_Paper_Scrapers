import os
import csv
from habanero import Crossref
import pandas as pd
from bs4 import BeautifulSoup
import html
from datetime import datetime, timedelta

# Initialize Crossref API
cr = Crossref()

# Load keywords from the txt file in the root directory
def load_keywords():
    try:
        root_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(root_dir, 'keywords.txt')
        with open(file_path, 'r') as f:
            keywords = [line.strip() for line in f.readlines() if line.strip()]
        print(f"Keywords loaded: {keywords}")
        return keywords
    except Exception as e:
        print(f"Error loading keywords: {e}")
        return []

# Function to get the start of the current week
def get_start_of_week():
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())  # Monday of the current week
    return start_of_week.strftime('%Y-%m-%d')

# Function to fetch metadata based on keyword
def fetch_metadata(keyword):
    start_of_week = get_start_of_week()
    print(f"Fetching metadata for keyword: {keyword} from {start_of_week} to today")
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        results = cr.works(query=keyword, filter={'from-pub-date': start_of_week, 'until-pub-date': today}, limit=10)
        metadata_list = []

        for item in results['message']['items']:
            title = item.get('title', [''])[0]
            authors = item.get('author', [])
            first_author = f"{authors[0]['family']}, {authors[0]['given']}" if authors else ''
            final_author = f"{authors[-1]['family']}, {authors[-1]['given']}" if len(authors) > 1 else ''
            other_authors = ', '.join([f"{author['family']}, {author['given']}" for author in authors[1:-1]]) if len(authors) > 2 else ''
            pub_type = item.get('type', '')
            journal = item.get('container-title', [''])[0]
            year = item.get('published-print', {}).get('date-parts', [[None]])[0][0]
            vol = item.get('volume', '')
            page = item.get('page', '')
            doi = item.get('DOI', '')
            doi_unique = f"https://doi.org/{doi}" if doi else ''
            affiliations = ''
            if authors and 'affiliation' in authors[0] and authors[0]['affiliation']:
                affiliations = authors[0]['affiliation'][0].get('name', '')
            other_institutions = [author['affiliation'][0].get('name', '') for author in authors[1:] if 'affiliation' in author and author['affiliation']]
            other_institution = other_institutions[0] if len(other_institutions) > 0 else ''
            other_institution_2 = other_institutions[1] if len(other_institutions) > 1 else ''
            raw_abstract = item.get('abstract', '')
            soup = BeautifulSoup(raw_abstract, 'html.parser')
            clean_abstract = html.unescape(soup.get_text())
            keywords_list = item.get('subject', [])

            metadata = {
                'Title': title,
                'First Author': first_author,
                'Final Author': final_author,
                'Other authors': other_authors,
                'Type of publication': pub_type,
                'Journal': journal,
                'Year': year,
                'Volume': vol,
                'Page': page,
                'DOI': doi,
                'DOI Unique': doi_unique,
                'Affiliation': affiliations,
                'Other Institution': other_institution,
                'Other Institution 2': other_institution_2,
                'Area': '',  # Placeholder for Area
                'Area 2': '',  # Placeholder for Other Areas
                'Article Classification': '',  # Placeholder for classification
                'KW(keyword) 1': keywords_list[0] if len(keywords_list) > 0 else '',
                'KW(keyword) 2': keywords_list[1] if len(keywords_list) > 1 else '',
                'KW(keyword) 3': keywords_list[2] if len(keywords_list) > 2 else '',
                'KW(keyword) 4': keywords_list[3] if len(keywords_list) > 3 else '',
                'KW(keyword) 5': keywords_list[4] if len(keywords_list) > 4 else '',
                'KW(keyword) 6': keywords_list[5] if len(keywords_list) > 5 else '',
                'Abstract': clean_abstract
            }

            metadata_list.append(metadata)

        print(f"Fetched metadata for keyword: {keyword} - {len(metadata_list)} items found")
        return metadata_list
    except Exception as e:
        print(f"Error fetching metadata for keyword {keyword}: {e}")
        return []

# Load keywords from the txt file
keywords = load_keywords()

# Collect metadata for all keywords
all_metadata = []
for keyword in keywords:
    print(f"Processing keyword: {keyword}")
    metadata = fetch_metadata(keyword)
    all_metadata.extend(metadata)
    print(f"Completed processing for keyword: {keyword}")

# Save to CSV
try:
    df = pd.DataFrame(all_metadata)
    df.to_csv('crossref_week.csv', index=False)
    print("Metadata saved to crossref_week.csv")
except Exception as e:
    print(f"Error saving to CSV: {e}")
