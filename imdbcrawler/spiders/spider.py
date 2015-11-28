# -*- coding: utf-8 -*-
import re
from datetime import datetime

import scrapy
from dateutil import parser

from imdbcrawler.items import MovieItem, CastItem, AwardItem, RatingItem, PersonItem, ReleaseInfoItem


class ImdbSpider(scrapy.Spider):
    name = "ImdbMovieCrawler"
    allowed_domains = ["imdb.com"]
    url_bases = ["http://www.imdb.com/"]
    start_urls = [
        "http://www.imdb.com/search/title?at=0&count=100&release_date=2002-01-01,2016-02-01&title_type=feature",
    ]
    max_release_info = 10
    db = None
    collection_name = None

    def parse(self, response):
        query = self.db[self.collection_name].find({'releaseDate': {'$exists': False}})
        print "Items to crawl: %s" % query.count()
        for doc in query:
            yield scrapy.Request(response.urljoin(doc["url"]) + "releaseinfo?ref_=tt_ov_inf", meta={'item': {'_id': str(doc["_id"])}}, callback=self.parse_release_info)

    def parse_release_info(self, response):
        # parse the release info
        doc = response.meta['item']
        date = None
        for idx, sel in enumerate(response.xpath("//table[@id='release_dates']/tr")):
            cSel = sel.xpath("td[1]/a/text()")
            if cSel and 'USA' in cSel.extract()[0]:
                dateStr = self.get_xpath("td[2]/text()", sel, 0) + " " + self.get_xpath("td[2]/a/text()", sel, 0)
                date = parser.parse(dateStr)
                break
        return { '_id': doc['_id'], 'date': date}

    #         self.set_item(rel_inf, "Date", self.get_xpath("td[2]/text()", sel, 0) + " " + self.get_xpath("td[2]/a/text()", sel, 0))
    #         self.set_item(rel_inf, "Country", self.get_xpath("td[1]/a/text()", sel, 0))
    #         self.set_item(rel_inf, "Info", self.get_xpath("td[3]/text()", sel, 0))
    #         release_infos.append(rel_inf)
    #     self.set_item(item, "releaseInfo", release_infos)
    #     return scrapy.Request(item["url"] + "awards?ref_=tt_awd", meta={'item':item }, callback=self.parse_awards, priority=4)

    # def parse(self, response):
    #     for idx, sel in enumerate(response.xpath("//*[@class='results']/tr")):
    #         if idx == 0:
    #             continue
    #         base_url = self.get_xpath("td[@class='title']/a/@href", sel, 0)
    #         imdb_id = self.resolve_id(base_url, '/title/')
    #         if self.db[self.collection_name].find({'imdbId': imdb_id}).limit(1).count():
    #             continue
    #
    #         item = MovieItem()
    #         title = self.get_xpath("td[@class='title']/a/text()", sel, 0)
    #         self.set_item(item, 'title', title)
    #         self.set_item(item, 'imdbId', imdb_id)
    #         self.set_item(item, 'url', response.urljoin(base_url))
    #         yield scrapy.Request(response.urljoin(item['url']), meta={'item': item}, callback=self.parse_movies, priority=1)
    #
    #     # get the next page
    #     page_button_title = response.xpath("//*[@class='pagination']/a/text()").extract()[-1]
    #     if 'Next' in page_button_title:
    #         next_page = response.xpath("//*[@class='pagination']/a/@href").extract()[-1]
    #         if next_page:
    #             yield scrapy.Request(response.urljoin(next_page), callback=self.parse)
    #
    # def parse_movies(self, response):
    #     item = response.meta['item']
    #
    #     # parse director
    #     dir = PersonItem()
    #     self.set_item(dir, 'name', self.get_xpath("//div[@itemprop='director']/a/span/text()", response, 0))
    #     dir_base_url = self.get_xpath("//div[@itemprop='director']/a/@href", response, 0)
    #     if dir_base_url:
    #         self.set_item(dir, 'url', response.urljoin(dir_base_url))
    #         self.set_item(dir, 'imdbId', self.resolve_id(dir_base_url, '/name/'))
    #     self.set_item(item, 'director', dir)
    #
    #     # parse ranking
    #     self.set_item(item, 'ranking', self.get_xpath("//*[@id='meterRank']/text()", response, 0))
    #
    #     # parse writers
    #     writers = []
    #     for idx, writerSel in enumerate(response.xpath("//div[@itemprop='creator']/a/span/text()").extract()):
    #         wri = PersonItem()
    #         self.set_item(wri, 'name', writerSel.strip())
    #         wri_base_url = self.get_xpath("//div[@itemprop='creator']/a[" + str(idx + 1) + "]/@href", response, 0)
    #         if wri_base_url:
    #             self.set_item(wri, 'url', response.urljoin(wri_base_url))
    #             self.set_item(wri, 'imdbId', self.resolve_id(wri_base_url, '/name/'))
    #         writers.append(wri)
    #     self.set_item(item, "writers", writers)
    #
    #     # parse genre
    #     self.set_item(item, 'genres', self.get_xpath("//div[@itemprop='genre']/a/text()", response, -1))
    #
    #     item = self.parse_rating(item, response)
    #     item = self.get_details(item, response)
    #
    #     return self.parse_casts(item, response)
    #
    # def parse_release_info(self, response):
    #     # parse the release info
    #     item = response.meta['item']
    #     release_infos = []
    #     for idx, sel in enumerate(response.xpath("//table[@id='release_dates']/tr")):
    #         if idx >= self.max_release_info:
    #             break
    #         rel_inf = ReleaseInfoItem()
    #         self.set_item(rel_inf, "Date", self.get_xpath("td[2]/text()", sel, 0) + " " + self.get_xpath("td[2]/a/text()", sel, 0))
    #         self.set_item(rel_inf, "Country", self.get_xpath("td[1]/a/text()", sel, 0))
    #         self.set_item(rel_inf, "Info", self.get_xpath("td[3]/text()", sel, 0))
    #         release_infos.append(rel_inf)
    #     self.set_item(item, "releaseInfo", release_infos)
    #     return scrapy.Request(item["url"] + "awards?ref_=tt_awd", meta={'item':item }, callback=self.parse_awards, priority=4)
    #
    # def parse_rating(self, item, response):
    #     # parse imdb rating
    #     imdb_rat = RatingItem()
    #     self.set_item(imdb_rat, "avgScore", self.get_xpath("//span[@itemprop='ratingValue']/text()", response, 0))
    #     self.set_item(imdb_rat, "maxScore", self.get_xpath("//span[@itemprop='bestRating']/text()", response, 0))
    #     self.set_item(imdb_rat, "ratingCount", self.get_xpath("//span[@itemprop='ratingCount']/text()", response, 0))
    #     self.set_item(item, "rating", imdb_rat)
    #     return item
    #
    # # Parses the award page of a movie
    # def parse_awards(self, response):
    #     item = response.meta['item']
    #     awards = []
    #
    #     for idx, sel in enumerate(response.xpath("//div[@class='article listo']/table[@class='awards']")):
    #         name = self.get_xpath("//div[@class='article listo']/h3[" + str(idx + 1) + "]/text()", sel, 0)
    #         year = self.get_xpath("//div[@class='article listo']/h3[" + str(idx + 1) + "]/a/text()", sel, 0)
    #
    #         for _idx, _sel in enumerate(sel.xpath("tr")):
    #             award = AwardItem()
    #             self.set_item(award, "name", name)
    #             self.set_item(award, "year", year)
    #             self.set_item(award, "category", self.get_xpath("td[@class='title_award_outcome']/span[@class='award_category']/text()", _sel, 0))
    #             self.set_item(award, "categoryDesc", self.get_xpath("td[@class='award_description']/text()", _sel, 0))
    #             self.set_item(award, "outcome", self.get_xpath("td[@class='title_award_outcome']/b/text()", _sel, 0))
    #             self.set_item(award, "members", self.get_xpath("td[@class='award_description']/a/text()", _sel, -1))
    #             awards.append(award)
    #
    #     self.set_item(item, "awards", awards)
    #     yield item
    #
    # # Parses the cast object
    # def parse_casts(self, item, response):
    #     cast_members = []
    #     for idx, sel in enumerate(response.xpath("//*[@id='titleCast']/table/tr")):
    #         if idx == 0:
    #             continue
    #         cast = CastItem()
    #         self.set_item(cast, 'ranking', idx)
    #         self.set_item(cast, 'name', self.get_xpath("td[2]/a/span/text()", sel, 0))
    #         base_url = self.get_xpath("td[2]/a/@href", sel, 0)
    #         if base_url:
    #             self.set_item(cast, 'url', response.urljoin(base_url))
    #             self.set_item(cast, 'imdbId', self.resolve_id(base_url, '/name/'))
    #         # Cast's character name could be a link
    #         if sel.xpath("td[4]/div/a/text()"):
    #             self.set_item(cast, 'characterName', self.get_xpath("td[4]/div/a/text()", sel, 0))
    #         elif sel.xpath("td[4]/div/text()"):
    #             self.set_item(cast, 'characterName', self.get_xpath("td[4]/div/text()", sel, 0))
    #         cast_members.append(cast)
    #
    #     self.set_item(item, 'cast_members', cast_members)
    #     return scrapy.Request(item["url"] + "releaseinfo?ref_=tt_ov_inf", meta={'item':item }, callback=self.parse_release_info, priority=3)
    #
    # def get_details(self, item, response):
    #     for index, sel in enumerate(response.xpath("//*[@id='titleDetails']/div")):
    #         details = self.get_xpath("h4/text()", sel, -1)
    #         if details:
    #             item = self.map_details(response, details, item, index + 1)
    #     return item
    #
    # def map_details(self, response, details, item, index):
    #     if details:
    #         if "Language:" in details:
    #             self.set_item(item, 'languages', self.get_xpath("//*[@id='titleDetails']/div[" + str(index) + "]/a/text()", response, -1))
    #         elif "Country:" in details:
    #             self.set_item(item, 'countries', self.get_xpath("//*[@id='titleDetails']/div[" + str(index) + "]/a/text()", response, -1))
    #         elif "Budget:" in details:
    #             self.set_item(item, 'budget', re.sub("\s\s+", " ", " ".join(self.get_xpath("//*[@id='titleDetails']/div[" + str(index) + "]/text() | //*[@id='titleDetails']/div[" + str(index) + "]/*[not(self::h4)]/text()", response, -1)).strip()))
    #         elif "Gross:" in details:
    #             self.set_item(item, 'grossProfit', re.sub("\s\s+", " ", " ".join(self.get_xpath("//*[@id='titleDetails']/div[" + str(index) + "]/text() | //*[@id='titleDetails']/div[" + str(index) + "]/*[not(self::h4)]/text()", response, -1)).strip()))
    #         elif "Opening Weekend:" in details:
    #             self.set_item(item, 'openingWeekendProfit', re.sub("\s\s+", " ", " ".join(self.get_xpath("//*[@id='titleDetails']/div[" + str(index) + "]/text() | //*[@id='titleDetails']/div[" + str(index) + "]/*[not(self::h4)]/text()", response, -1)).strip()))
    #         elif "Runtime:" in details:
    #             self.set_item(item, 'runtime', self.get_xpath("//*[@id='titleDetails']/div[" + str(index) + "]/time/text()", response, 0))
    #     return item
    #
    @staticmethod
    def set_item(item, key, prop):
        if not prop or (hasattr(prop, "__len__") and not len(prop)>0):
            return
        item[key] = prop

    @staticmethod
    def get_xpath(path, response, index):
        parsed = response.xpath(path)
        if parsed:
            striped = [x.strip() for x in parsed.extract()]
            if index < 0 or index > len(striped)-1:
                return striped
            return striped[index]
        return None

    @staticmethod
    def resolve_id(url, sub):
        return re.sub('/.*?.*', '', re.sub(sub, '', url))