import requests
import csv
import xml.etree.ElementTree as ET
import os
from time import sleep
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

# Function to search PubMed and retrieve article IDs
def search_pubmed(api_key, keyword, mindate, maxdate):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": keyword,
        "retmax": 10,  # Number of articles to retrieve per keyword
        "mindate": mindate,
        "maxdate": maxdate,
        "datetype": "pdat",  # Search based on publication date
        "api_key": api_key,
        "retmode": "xml"
    }
    response = requests.get(base_url, params=params)
    tree = ET.fromstring(response.content)
    ids = [id_elem.text for id_elem in tree.findall(".//Id")]
    return ids

# Function to fetch details (title, DOI, abstract, and other metadata) for a list of article IDs using EFetch
def fetch_article_details(api_key, article_ids):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": ",".join(article_ids),
        "retmode": "xml",
        "api_key": api_key
    }
    response = requests.get(base_url, params=params)
    tree = ET.fromstring(response.content)
    
    articles = []
    
    # Loop through PubmedArticle elements to extract details
    for article in tree.findall(".//PubmedArticle"):
        title = first_author = final_author = other_authors = pub_type = journal = year = vol = page = doi = doi_unique = affiliation = institution = area = classification = kw1 = kw2 = kw3 = kw4 = kw5 = kw6 = abstract = "N/A"
        
        # Extract title
        title_elem = article.find(".//ArticleTitle")
        if title_elem is not None:
            title = title_elem.text

        # Extract authors
        author_list = article.findall(".//Author")
        if author_list:
            first_author = author_list[0].findtext("LastName", "N/A")
            final_author = author_list[-1].findtext("LastName", "N/A")
            other_authors = ", ".join([author.findtext("LastName", "N/A") for author in author_list[1:-1]]) if len(author_list) > 2 else "N/A"

        # Extract type of publication
        pub_type_elem = article.find(".//PublicationType")
        if pub_type_elem is not None:
            pub_type = pub_type_elem.text

        # Extract journal
        journal_elem = article.find(".//Journal/Title")
        if journal_elem is not None:
            journal = journal_elem.text
        
        # Extract year, volume, and page
        year_elem = article.find(".//PubDate/Year")
        vol_elem = article.find(".//JournalIssue/Volume")
        page_elem = article.find(".//Pagination/MedlinePgn")
        
        year = year_elem.text if year_elem is not None else "N/A"
        vol = vol_elem.text if vol_elem is not None else "N/A"
        page = page_elem.text if page_elem is not None else "N/A"

        # Extract DOI
        doi_elem = article.find(".//ELocationID[@EIdType='doi']")
        if doi_elem is not None:
            doi = doi_elem.text
            doi_unique = doi.split("/")[-1]  # Extracting unique DOI part

        # Extract affiliation
        affiliation_elem = article.find(".//AffiliationInfo/Affiliation")
        if affiliation_elem is not None:
            affiliation = affiliation_elem.text

        # Extract keywords (up to 6)
        keyword_list = article.findall(".//Keyword")
        keywords = [kw.text for kw in keyword_list[:6]]
        kw1, kw2, kw3, kw4, kw5, kw6 = (keywords + ["N/A"] * 6)[:6]  # Fill N/A for missing keywords
        
        # Extract abstract
        abstract_elem = article.find(".//Abstract/AbstractText")
        if abstract_elem is not None:
            abstract = abstract_elem.text

        # Placeholder for other institutions and area (these can be customized based on your data)
        institution = "N/A"
        area = "N/A"
        classification = "N/A"

        articles.append([title, first_author, final_author, other_authors, pub_type, journal, year, vol, page, doi, doi_unique, affiliation, institution, area, classification, kw1, kw2, kw3, kw4, kw5, kw6, abstract])

    return articles

# Function to save the results to a CSV file
def save_to_csv(filename, data):
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([
            "Title", "First Author", "Final Author", "Other Authors", "Type of Publication", "Journal", "Year", "Volume", "Page", "DOI", 
            "DOI Unique", "Affiliation", "Other Institution", "Area", "Article Classification", "KW 1", "KW 2", "KW 3", "KW 4", "KW 5", "KW 6", "Abstract"
        ])
        writer.writerows(data)

# Function to read keywords from the 'keywords.txt' file
def read_keywords_from_file():
    with open('keywords.txt', 'r', encoding='utf-8') as file:
        keywords = [line.strip() for line in file.readlines() if line.strip()]
    return keywords

def main(api_key, mindate, maxdate):
    keywords = read_keywords_from_file()  # Load keywords from file
    all_articles = []

    for keyword in keywords:
        print(f"Processing keyword: {keyword}")
        article_ids = search_pubmed(api_key, keyword, mindate, maxdate)
        
        if article_ids:
            articles = fetch_article_details(api_key, article_ids)
            all_articles.extend(articles)
            print(f"Fetched {len(article_ids)} articles for keyword: {keyword}")
        else:
            print(f"No articles found for keyword: {keyword}")
        
        # To respect PubMed rate limits, sleep for 1 second between requests
        sleep(1)

    # Save the extracted data into a CSV file
    save_to_csv("pubmed_keywords.csv", all_articles)
    print("Data saved to pubmed_keywords.csv")

if __name__ == "__main__":
    api_key = os.getenv('PUBMED_API_KEY')  # Replace with your actual PubMed API key
    
    # Calculate date range (current week to present day)
    today = datetime.now()
    mindate = (today - timedelta(days=today.weekday())).strftime('%Y/%m/%d')  # Start of the current week
    maxdate = today.strftime('%Y/%m/%d')  # Current day
    
    main(api_key, mindate, maxdate)
