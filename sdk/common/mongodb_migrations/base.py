import pymongo


class BaseMigration(object):
    session = None
    max_db_lock_ttl = 600

    def __init__(
        self,
        host="127.0.0.1",
        port="27017",
        database=None,
        user=None,
        password=None,
        url=None,
    ):
        if url and database:
            # provide auth_database in url (mongodb://mongohostname:27017/auth_database)
            self.client = pymongo.MongoClient(url)
            self.db = self.client.get_database(database)
        else:
            raise Exception("no database, url or auth_database in url provided")

    def upgrade(self):
        raise NotImplementedError

    def downgrade(self):
        raise NotImplementedError

    def upgrade_base(self, _collection_index_map, _collections_to_be_created):

        existing_collections = self.db.list_collection_names()

        for c in _collections_to_be_created:
            if c not in existing_collections:
                self.db.create_collection(c)

        # 1. removing all indexes
        for k in _collection_index_map.keys():
            collection = self.db.get_collection(k)
            if collection is not None:
                collection.drop_indexes()

        # 2. recreate indexes
        for c in _collections_to_be_created:
            if c in _collection_index_map:
                for i in _collection_index_map.get(c):
                    self.db.get_collection(c).create_index(**i)
