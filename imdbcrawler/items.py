# -*- coding: utf-8 -*-

from scrapy.item import Item, Field

class MovieItem(Item):
    imdbId = Field()
    ranking = Field()
    title = Field()
    rating = Field()
    releaseInfo = Field()
    url = Field()
    director = Field()
    writers = Field()
    runtime = Field()
    genres = Field()
    mpaaRating = Field()
    budget = Field()
    languages = Field()
    countries = Field()
    grossProfit = Field()
    openingWeekendProfit = Field()
    castMembers = Field()
    awards = Field()

class ReleaseInfoItem(Item):
    Date = Field()
    Country = Field()
    Info = Field()

class RatingItem(Item):
    avgScore = Field()
    maxScore = Field()
    ratingCount = Field()

class PersonItem(Item):
    name = Field()
    imdbId = Field()
    url = Field()

class AwardItem(Item):
    awardName = Field()
    year = Field()
    category = Field()
    categoryDesc = Field()
    members = Field()
    outcome = Field()

class CastItem(Item):
    imdbId = Field()
    actorName = Field()
    characterName = Field()
    url = Field()
    ranking = Field()
    # type = Field()
