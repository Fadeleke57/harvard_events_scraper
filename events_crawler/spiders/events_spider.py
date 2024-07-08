import scrapy
import re
import pandas as pd
from datetime import datetime

class HarvardEventsSpider(scrapy.Spider):
    name = "harvard_events"

    def __init__(self, *args, **kwargs):
        super(HarvardEventsSpider, self).__init__(*args, **kwargs)
        self.events_data = []

    def start_requests(self):
        start_urls = ['https://www.math.harvard.edu/event_archive/']
        for url in start_urls:
            yield scrapy.Request(url, self.parse_search_results)

        for i in range(2, 170):  # number of pages for events
            yield scrapy.Request(f'https://www.math.harvard.edu/event_archive/page/{i}/', self.parse_search_results)

    def parse_search_results(self, response):
        if response.status != 200:
            self.logger.error(f"Failed to retrieve search results: {response.url} with status {response.status}")
            return

        articles = response.css('article')
        if not articles:
            self.logger.warning(f"No articles found on search results page: {response.url}")

        for article in articles:
            article_link = article.css('div.event_item a::attr(href)').get()
            if article_link:
                yield scrapy.Request(article_link, self.parse_article)

    def parse_article(self, response):
        if response.status != 200:
            self.logger.error(f"Failed to retrieve article: {response.url} with status {response.status}")
            return

        header = response.css('h1::text').get()
        category = response.css('p.evt-cat::text').get()

        venue_and_address = response.css('div.event-venue *::text').getall()
        venue_and_address = ''.join(venue_and_address).strip()
        venue_and_address = re.sub('[\n\t\r]', '', venue_and_address) if venue_and_address else None

        date = response.xpath('/html/body/div/div/div/div/main/div/div[1]/div/div/div[1]/div[1]/div/div[1]/span/text()').get()
        time = response.xpath('/html/body/div/div/div/div/main/div/div[1]/div/div/div[1]/div[1]/div/div[1]/span/text()[2]').get()
        date_time = (f'{date}{time}') if date and time else None
        date_time = re.sub('[\n\t\r]', '', date_time) if date_time else None

        link_to_article = response.url
        speaker = response.xpath('//*[@id="main"]/div/div[1]/div/div/p[2]/text()').get()
        speaker_details = response.xpath('/html/body/div/div/div/div/main/div/div[1]/div/div/p[2]/em/text()').get()
        full_speaker = (f'{speaker}{speaker_details}') if speaker and speaker_details else speaker

        texts = response.xpath('//*[@id="main"]/div/div[1]/div/div//p//text()').getall()[3:]
        text = '\n'.join(texts)

        if not text: #text fallback
            texts = response.xpath('//*[@id="main"]/div/div[1]/div/div//div//text()').getall()[2:]
            text = '\n'.join(texts)

        images = response.css('div.event_item img::attr(src)').getall()

        modified_date = response.css('meta[property="article:modified_time"]::attr(content)').get()

        if modified_date:
            date_object = datetime.strptime(modified_date, "%Y-%m-%dT%H:%M:%S%z")
            formatted_date = date_object.strftime("%m/%d/%Y %I:%M %p")
        else:
            formatted_date = "No date value found"

        event_data = {
            'type': 'event',
            'header': header,
            'category': category,
            'venue_and_address': venue_and_address,
            'date': date_time,
            'abstract': full_speaker,
            'text': text,
            'images': images,
            'link_to_article': link_to_article,
            'date_created' : formatted_date
        }

        self.events_data.append(event_data)

    def closed(self, reason):
        df = pd.DataFrame(self.events_data)
        df.to_excel('harvard_events.xlsx', index=False)