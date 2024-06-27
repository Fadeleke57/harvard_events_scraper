"""
To find events with fields that might differ from the rest or not properly scraped
"""
import json

with open('C:/Users/fadel/harvard_events_scraper/events_crawler/result.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

outliers = {}

for article in data:
    for field in article:
        if article[field] == None:
            if field not in outliers:
                outliers[field] = []
            outliers[field].append(article['link_to_article'])

with open('C:/Users/fadel/harvard_events_scraper/events_crawler/outliers.json', 'w', encoding='utf-8') as file:
    json.dump(outliers, file, indent=4)
