import scrapy
import re

class HarvardEventsSpider(scrapy.Spider):
    name = "harvard_events"
    def start_requests(self):
        start_urls = [f'https://www.math.harvard.edu/event_archive/']
        for url in start_urls:
            yield scrapy.Request(url, self.parse_search_results)

        for i in range(2, 169): #number of pages for events
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

        venue = response.xpath('/html/body/div/div/div/div/main/div/div[1]/div/div/div[1]/div[1]/div/div[2]/span/text()').get()
        venue = re.sub('[\n\t\r]', '', venue) 
        address = response.xpath('/html/body/div/div/div/div/main/div/div[1]/div/div/div[1]/div[1]/div/div[2]/div/span[2]/text()').get()
        address = re.sub('[\n\t\r]', '', address)

        date = response.xpath('/html/body/div/div/div/div/main/div/div[1]/div/div/div[1]/div[1]/div/div[1]/span/text()').get()
        time = response.xpath('/html/body/div/div/div/div/main/div/div[1]/div/div/div[1]/div[1]/div/div[1]/span/text()[2]').get()
        date_time = (f'{date}{time}')
        date_time = re.sub('[\n\t\r]', '', date_time)

        link_to_article = response.url
        speaker = response.xpath('//*[@id="main"]/div/div[1]/div/div/p[2]/text()').get()
        speaker_details = response.xpath('/html/body/div/div/div/div/main/div/div[1]/div/div/p[2]/em/text()').get()
        if speaker_details:
            full_speaker = (f'{speaker}{speaker_details}')
        else:
            full_speaker = speaker

        texts = response.xpath('//*[@id="main"]/div/div[1]/div/div//p//text()').getall()[3:] #//*[@id="main"]/div/div[1]/div/div/div[3]
        text = '\n'.join(texts)

        if text == "":
            texts = response.xpath('//*[@id="main"]/div/div[1]/div/div//div//text()').getall()[2:]
            text = '\n'.join(texts)
        
        yield {
            'type': 'event',
            'header': header,
            'category': category,
            'venue': venue,
            'address': address,
            'date': date_time,
            'speaker': full_speaker,
            'text': text,
            'link_to_article': link_to_article,
        }