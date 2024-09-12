import requests
import csv
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

# Springer API base URL
BASE_URL = "https://api.springernature.com/meta/v2/json"

# Your Springer API key
API_KEY = os.getenv("SPRINGER_API_KEY")

# Read keywords from the 'keywords.txt' file in the root directory
def load_keywords_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file.readlines()]

keywords_file_path = os.path.join(os.getcwd(), 'keywords.txt')
keywords = load_keywords_from_file(keywords_file_path)

# Date range for the current week
today = datetime.today()
start_date = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')  # Start of the current week (Monday)
end_date = today.strftime('%Y-%m-%d')  # Today's date

# CSV file to save the extracted data
csv_filename = "springer_articles_current_week.csv"

# Function to fetch articles based on keywords and date range
def fetch_springer_articles(keyword, start_date, end_date):
    params = {
        'q': keyword,  # Query term (keyword)
        'api_key': API_KEY,  # Your API key
        'p': 5,  # Number of results per page
        'date-facet-mode': 'between',  # Filter mode
        'date-facet': f"[{start_date} TO {end_date}]",  # Date range
    }
    response = requests.get(BASE_URL, params=params)
    
    # Check if the response is valid
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching data for keyword '{keyword}': {response.status_code}")
        return None

def extract_data_from_response(response):
    articles = []
    if response and 'records' in response:
        for record in response['records']:
            title = record.get('title', 'N/A')
            doi = record.get('doi', 'N/A')
            abstract = record.get('abstract', 'N/A')
            publication_date = record.get('publicationDate', 'N/A')

            # Extract authors
            authors_list = record.get('creators', [])
            first_author = authors_list[0]['creator'] if authors_list else 'N/A'
            final_author = authors_list[-1]['creator'] if len(authors_list) > 1 else 'N/A'
            other_authors = ', '.join([author['creator'] for author in authors_list[1:-1]]) if len(authors_list) > 2 else 'N/A'

            # Extract other metadata
            publication_type = record.get('contentType', 'N/A')
            journal = record.get('publicationName', 'N/A')
            year = publication_date.split('-')[0] if publication_date != 'N/A' else 'N/A'
            volume = record.get('volume', 'N/A')
            page = record.get('startingPage', 'N/A')

            # Extract affiliation and institution information
            creators = record.get('creators', [])
            affiliations = []
            institutions = []
            for creator in creators:
                if 'affiliation' in creator:
                    affiliations.append(creator['affiliation'])
                if 'organization' in creator:
                    institutions.append(creator['organization'])
            
            affiliation = '; '.join(affiliations) if affiliations else 'N/A'
            institution = institutions[0] if institutions else 'N/A'
            other_institution = institutions[1] if len(institutions) > 1 else 'N/A'

            # Extract areas (subjects and disciplines)
            subjects = record.get('subjects', [])
            disciplines = record.get('disciplines', [])
            
            area1 = subjects[0] if subjects else 'N/A'
            area2 = subjects[1] if len(subjects) > 1 else 'N/A'
            area3 = disciplines[0]['term'] if disciplines else 'N/A'

            # Extract article classification
            article_classification = record.get('genre', 'N/A')

            # Extract keywords (up to KW1-KW6)
            keywords = record.get('keyword', [])
            kw1 = keywords[0] if len(keywords) > 0 else 'N/A'
            kw2 = keywords[1] if len(keywords) > 1 else 'N/A'
            kw3 = keywords[2] if len(keywords) > 2 else 'N/A'
            kw4 = keywords[3] if len(keywords) > 3 else 'N/A'
            kw5 = keywords[4] if len(keywords) > 4 else 'N/A'
            kw6 = keywords[5] if len(keywords) > 5 else 'N/A'

            # Append the extracted data to the articles list
            articles.append([
                title, first_author, final_author, other_authors, publication_type, journal, year, volume, page,
                doi, doi, affiliation, institution, other_institution, area1, area2, area3,
                article_classification, kw1, kw2, kw3, kw4, kw5, kw6, abstract
            ])
    
    return articles

# Function to save the data into a CSV file
def save_to_csv(data, filename):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow([
            'Title', 'First Author', 'Final Author', 'Other Authors', 'Type of Publication', 'Journal',
            'Year', 'Volume', 'Page', 'DOI', 'DOI Unique', 'Affiliation', 'Institution',
            'Other Institution', 'Area 1', 'Area 2', 'Area 3', 'Article Classification', 
            'KW 1', 'KW 2', 'KW 3', 'KW 4', 'KW 5', 'KW 6', 'Abstract'
        ])
        writer.writerows(data)  # Write data

def main():
    all_articles = []
    
    for keyword in keywords:
        print(f"Fetching articles for keyword: {keyword} within date range {start_date} to {end_date}")
        response = fetch_springer_articles(keyword, start_date, end_date)
        articles = extract_data_from_response(response)
        all_articles.extend(articles)
        
        # Message after each keyword data is processed
        print(f"Data for keyword '{keyword}' extracted and added to the list.")
    
    # Save the collected articles to a CSV file
    save_to_csv(all_articles, csv_filename)
    print(f"Data saved to {csv_filename}")

if __name__ == "__main__":
    main()
