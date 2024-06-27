import scrapy
import re

class HarvardEventsSpider(scrapy.Spider):
    name = "harvard_events"

    def start_requests(self):
        start_urls = ['https://www.math.harvard.edu/event_archive/']
        for url in start_urls:
            yield scrapy.Request(url, self.parse_search_results)

        for i in range(2, 169):  # number of pages for events
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

        yield {
            'type': 'event',
            'header': header,
            'category': category,
            'venue_and_adress': venue_and_address,
            'date': date_time,
            'speaker': full_speaker,
            'text': text,
            'link_to_article': link_to_article,
        }