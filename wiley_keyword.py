import requests
import csv
import xml.etree.ElementTree as ET
import os
import time
import random
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

# Base URL for SRU search
BASE_URL = 'https://onlinelibrary.wiley.com/action/sru'

# Add your Wiley API key here (if required)
API_KEY = os.getenv('WILEY_API_KEY')

# Date range for the search (current week to present day)
end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime('%Y-%m-%d')

# Define namespaces
namespaces = {
    'zs': 'http://www.loc.gov/zing/srw/',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'dcterms': 'http://purl.org/dc/terms/',
    'prism': 'http://prismstandard.org/namespaces/basic/2.1/'
}

def fetch_metadata(keyword):
    print(f"Fetching metadata for keyword: {keyword}")
    
    query = f"dc.title={keyword} AND dc.date>={start_date} AND dc.date<={end_date}"
    
    params = {
        'query': query,
        'version': '1.2',
        'maximumRecords': 20
    }

    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://onlinelibrary.wiley.com',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
    }

    delay = random_delay()
    print(f"Delaying for {delay:.2f} seconds to avoid CAPTCHA...")

    response = requests.get(BASE_URL, params=params, headers=headers)

    if response.status_code == 200:
        root = ET.fromstring(response.content)
        records = root.findall('.//zs:record', namespaces)

        if not records:
            print(f"No records found for keyword: {keyword}")
            return []

        results = []
        for record in records:
            dc_data = record.find('.//dc:dc', namespaces)
            if dc_data is None:
                continue

            metadata = {
                'keyword': keyword,
                'Title': get_element_text(dc_data, 'dc:title'),
                'First Author': 'N/A',
                'Final Author': 'N/A',
                'Other authors': 'N/A',
                'Type of publication': get_element_text(dc_data, 'dc:type'),
                'Journal': get_element_text(dc_data, 'dcterms:isPartOf'),
                'Year': get_element_text(dc_data, 'dc:date')[:4] if get_element_text(dc_data, 'dc:date') else 'N/A',
                'vol': 'N/A',
                'page': 'N/A',
                'DOI': get_element_text(dc_data, 'dc:identifier'),
                'DOI Unique': get_element_text(dc_data, 'dc:identifier'),
                'Affiliation': 'N/A',
                'Other Institution': 'N/A',
                'Other Institution 2': 'N/A',
                'Area': 'N/A',
                'Other Areas': 'N/A',
                'Other Areas 2': 'N/A',
                'Article Classification': 'N/A',
                'KW 1': 'N/A',
                'KW 2': 'N/A',
                'KW 3': 'N/A',
                'KW 4': 'N/A',
                'KW 5': 'N/A',
                'KW 6': 'N/A',
                'Abstract': get_element_text(dc_data, 'dc:description')
            }

            results.append(metadata)

        print(f"Metadata for keyword '{keyword}' extracted successfully.")
        return results
    else:
        print(f"Error: {response.status_code} for keyword '{keyword}' - {response.text}")
        return []

def get_element_text(element, tag):
    el = element.find(tag, namespaces)
    return el.text.strip() if el is not None and el.text else 'N/A'

def random_delay():
    delay = random.uniform(5, 10)
    time.sleep(delay)
    return delay

def save_to_csv(data, filename='wiley_week.csv'):
    if not data:
        print("No data to write to CSV.")
        return

    fieldnames = [
        'keyword', 'Title', 'First Author', 'Final Author', 'Other authors',
        'Type of publication', 'Journal', 'Year', 'vol', 'page', 'DOI', 'DOI Unique',
        'Affiliation', 'Other Institution', 'Other Institution 2', 'Area',
        'Other Areas', 'Other Areas 2', 'Article Classification',
        'KW 1', 'KW 2', 'KW 3', 'KW 4', 'KW 5', 'KW 6', 'Abstract'
    ]
    
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

    print(f"Data successfully written to {filename}")

def load_keywords():
    keywords_file = 'keywords.txt'
    if not os.path.exists(keywords_file):
        print(f"Error: '{keywords_file}' not found in the root directory.")
        return []
    
    with open(keywords_file, 'r', encoding='utf-8') as file:
        keywords = [line.strip() for line in file if line.strip()]
    
    return keywords

def main():
    all_metadata = []

    keywords = load_keywords()
    if not keywords:
        print("No keywords found. Exiting.")
        return

    for keyword in keywords:
        metadata = fetch_metadata(keyword)
        if metadata:
            all_metadata.extend(metadata)

    if all_metadata:
        save_to_csv(all_metadata)
        print(f"Metadata saved to 'wiley_week.csv'.")
    else:
        print("No metadata collected. CSV not created.")

if __name__ == '__main__':
    main()
