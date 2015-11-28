import pymongo
from bson import ObjectId


class MongoPipeline(object):

    collection_name = 'imdb_movies'

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        spider.db = self.db
        spider.collection_name = self.collection_name

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        if item['date']:
            self.db[self.collection_name].update({"_id": ObjectId(item["_id"])}, {"$set": {"releaseDate": item["date"]}})
        return item