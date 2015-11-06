# -*- coding: utf-8 -*-
import re

import scrapy
from imdbcrawler.items import MovieItem, CastItem, AwardItem, RatingItem, PersonItem, ReleaseInfoItem


class ImdbSpider(scrapy.Spider):
    name = "ImdbMovieCrawler"
    allowed_domains = ["imdb.com"]
    url_bases = ["http://www.imdb.com/"]
    start_urls = [
        "http://www.imdb.com/search/title?at=0&count=100&release_date=2002-01-01,2016-02-01&title_type=feature",
        "http://www.imdb.com/search/title?at=0&count=100&release_date=1972-01-01,2002-01-01&title_type=feature",
        "http://www.imdb.com/search/title?at=0&count=100&release_date=1930-01-01,1972-01-01&title_type=feature"
    ]

    def parse(self,response):
        for idx, sel in enumerate(response.xpath("//*[@class='results']/tr")):
            if idx == 0:
                continue
            baseUrl = self.getXpath("td[@class='title']/a/@href", sel, 0)
            imdbId = self.resolveId(baseUrl, '/title/')
            if self.db[self.collection_name].find({'imdbId': imdbId}).limit(1).count():
                continue

            item = MovieItem()
            item['title'] = self.getXpath("td[@class='title']/a/text()", sel, 0)
            item['imdbId'] = imdbId
            item['url'] = response.urljoin(baseUrl)
            yield scrapy.Request(response.urljoin(item['url']), meta={'item':item }, callback=self.parseMovies, priority=1)

        # get the next page
        next_page = response.xpath("//*[@class='pagination']/a/@href").extract()[-1]
        if next_page:
            yield scrapy.Request(response.urljoin(next_page), callback=self.parse)

    def parseMovies(self, response):
        item = response.meta['item']

        # parse Director
        dir = PersonItem()
        dir['name'] = self.getXpath("//div[@itemprop='director']/a/span/text()", response, 0)
        dirBaseUrl = self.getXpath("//div[@itemprop='director']/a/@href", response, 0)
        if dirBaseUrl:
            dir['url'] = response.urljoin(dirBaseUrl)
            dir['imdbId'] = self.resolveId(dirBaseUrl, '/name/')
        item['director'] = dir

        #parse ranking
        item['ranking'] = self.getXpath("//*[@id='meterRank']/text()", response, 0)

        # parse Writers
        item['writers'] = []
        for idx, writerSel in enumerate(response.xpath("//div[@itemprop='creator']/a/span/text()").extract()):
            wri = PersonItem()
            wri['name'] = writerSel.strip()
            wriBaseUrl = self.getXpath("//div[@itemprop='creator']/a["+str(idx+1)+"]/@href", response, 0)
            if wriBaseUrl:
                wri['url'] = response.urljoin(wriBaseUrl)
                wri['imdbId'] = self.resolveId(wriBaseUrl, '/name/')
            item['writers'].append(wri)

        # parse genre
        item['genres'] = self.getXpath("//div[@itemprop='genre']/a/text()", response, -1)

        item = self.parseRating(item, response)
        item = self.getDetails(item, response)

        return self.parseCasts(item, response)

    maxReleaseInfo = 10
    def parseReleaseInfo(self, response):
        # parse the release info
        item = response.meta['item']
        item["releaseInfo"] = []
        for idx, sel in enumerate(response.xpath("//table[@id='release_dates']/tr")):
            if idx >= self.maxReleaseInfo:
                break
            current = ReleaseInfoItem()
            current["Date"] = self.getXpath("td[2]/text()", sel, 0) + " " + self.getXpath("td[2]/a/text()", sel, 0)
            current["Country"] = self.getXpath("td[1]/a/text()", sel, 0)
            current["Info"] = self.getXpath("td[3]/text()", sel, 0)
            item["releaseInfo"].append(current)
        return scrapy.Request(item["url"] + "awards?ref_=tt_awd", meta={'item':item }, callback=self.parseAwards, priority=4)

    def parseRating(self, item, response):
        # parse imdb rating
        imdbRating = RatingItem()
        imdbRating["avgScore"] = self.getXpath("//span[@itemprop='ratingValue']/text()", response, 0)
        imdbRating["maxScore"] = self.getXpath("//span[@itemprop='bestRating']/text()", response, 0)
        imdbRating["ratingCount"] = self.getXpath("//span[@itemprop='ratingCount']/text()", response, 0)
        item["rating"] = imdbRating
        return item

    # Parses the award page of a movie
    def parseAwards(self, response):
        item = response.meta['item']
        item["awards"] = []

        for idx, sel in enumerate(response.xpath("//div[@class='article listo']/table[@class='awards']")):
            name = self.getXpath("//div[@class='article listo']/h3["+str(idx+1)+"]/text()", sel, 0)
            year = self.getXpath("//div[@class='article listo']/h3["+str(idx+1)+"]/a/text()", sel, 0)

            for idx, sel in enumerate(sel.xpath("tr")):
                award = AwardItem()
                award["name"] = name
                award["year"] = year
                award["category"] = self.getXpath("td[@class='title_award_outcome']/span[@class='award_category']/text()", sel, 0)
                award["categoryDesc"] = self.getXpath("td[@class='award_description']/text()", sel, 0)
                award["outcome"] = self.getXpath("td[@class='title_award_outcome']/b/text()", sel, 0)
                award["members"] = self.getXpath("td[@class='award_description']/a/text()", sel, -1)
                item['awards'].append(award)
        yield item

    # Parses the cast object
    def parseCasts(self, item, response):
        item['castMembers'] = []
        for idx, sel in enumerate(response.xpath("//*[@id='titleCast']/table/tr")):
            if idx == 0:
                continue
            cast = CastItem()
            cast['ranking'] = idx
            cast['name'] = self.getXpath("td[2]/a/span/text()", sel, 0)
            baseUrl = self.getXpath("td[2]/a/@href", sel, 0)
            if baseUrl:
                cast['url'] = response.urljoin(baseUrl)
                cast['imdbId'] = self.resolveId(baseUrl, '/name/')
            # Cast's character name could be a link
            if sel.xpath("td[4]/div/a/text()"):
                cast['characterName'] = self.getXpath("td[4]/div/a/text()", sel, 0)
            elif sel.xpath("td[4]/div/text()"):
                cast['characterName'] = self.getXpath("td[4]/div/text()", sel, 0)
            item['castMembers'].append(cast)
        return scrapy.Request(item["url"] + "releaseinfo?ref_=tt_ov_inf", meta={'item':item }, callback=self.parseReleaseInfo, priority=3)

    def getDetails(self, item, response):
        for index, sel in enumerate(response.xpath("//*[@id='titleDetails']/div")):
            details = self.getXpath("h4/text()", sel, -1)
            if(details):
                item = self.mapDetails(response, details, item, index + 1)
        return item

    def mapDetails(self, response, details, item, index):
        if details:
            if "Language:" in details:
                item['languages'] = self.getXpath("//*[@id='titleDetails']/div["+str(index)+"]/a/text()", response, -1)
            elif "Country:" in details:
                item['countries'] = self.getXpath("//*[@id='titleDetails']/div["+str(index)+"]/a/text()", response, -1)
            elif "Budget:" in details:
                item['budget'] = self.getXpath("//*[@id='titleDetails']/div["+str(index)+"]/text()[2]", response, 0)
            elif "Gross:" in details:
                item['grossProfit'] = self.getXpath("//*[@id='titleDetails']/div["+str(index)+"]/text()[2]", response, 0)
            elif "Opening Weekend:" in details:
                item['openingWeekendProfit'] = re.sub("\s\s+", " ", self.getXpath("//*[@id='titleDetails']/div["+str(index)+"]/text()[2]", response, 0))
            elif "Runtime:" in details:
                item['runtime'] = self.getXpath("//*[@id='titleDetails']/div["+str(index)+"]/time/text()", response, 0)
        return item

    def getXpath(self, path, response, index):
        parsed = response.xpath(path)
        if parsed:
            striped = [x.strip() for x in parsed.extract()]
            if 0 > index > len(striped):
                return striped
            return striped[index]
        return None

    def resolveId(self, url, sub):
        return re.sub('/.*?.*', '', re.sub(sub, '', url))