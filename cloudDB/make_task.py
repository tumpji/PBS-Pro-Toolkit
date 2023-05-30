#!/usr/bin/python3.11
#    # ------------------------------------------------------------------
#    # set up connection
#
#    connection = DBConnection('test')
#
#    # ------------------------------------------------------------------
#    # insert work to database
#
#    import itertools
#
#    options = [
#            [1, 2, 3],
#            ["ahoj jak se mas", "kolo", "stary mnich"],
#            [11, 22, 33]
#    ]
#
#    for argument1, argument2, argument3 in itertools.product(*options):
#        data = {
#            'argument1': argument1,
#            'argument2': argument2,
#            'argument3': argument3
#        }
#
#        print(f'inserting: {data}')
#        result = connection.insert_free(data)
#
#    # ------------------------------------------------------------------
#    # get work from database
#
#    try:
#        while True:
#            with connection as c:
#                print(f"Processing: {c.data}")
#                # if raise, the data will be in the errored db
#
#    except NoMoreWork:
#        print('Finished')
#
#    # ------------------------------------------------------------------
#    # move erroed to free
#    connection.renew_errored()

import configparser
import urllib.parse

from pymongo import MongoClient


class NoMoreWork(StopIteration):
    pass


class DBConnectionBase:
    def __init__(self, MONGO_DB, config_path='AUTHENTICATION.ini'):
        config = configparser.ConfigParser()
        config.read(config_path)

        # Replace these with your server details
        MONGO_HOST = "147.251.115.70"
        MONGO_PORT = "27017"
        MONGO_USER = urllib.parse.quote_plus(config['AUTHENTICATION']['USERNAME'])
        MONGO_PASS = urllib.parse.quote_plus(config['AUTHENTICATION']['PASSWORD'])

        uri = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin"
        self.client = MongoClient(uri)

        self.db = self.client[MONGO_DB]


class DBConnection(DBConnectionBase):
    def insert_free(self, data):
        result = self.db.free.insert_one(data)
        if not result.acknowledged:
            raise RuntimeError('insertion error')

    def drop_all(self):
        self.db.free.drop()
        self.db.finished.drop()
        self.db.errored.drop()
        self.db.blocked.drop()

    def renew_errored(self):
        data = self.db.errored.find({})
        self.db.free.insert_many(data)

    def renew_blocked(self):
        data = self.db.blocked.find({})
        self.db.free.insert_many(data)

    def _block_one(self):
        with self.client.start_session() as session:
            with session.start_transaction():
                document = self.db.free.find_one_and_delete({})
                if document is None:
                    return None, None

                result = self.db.blocked.insert_one(document)
                if not result.acknowledged:
                    raise RuntimeError('insertion error')

                document_id = document['_id']
                del document['_id']
                return document, document_id

    def _finish_one(self, document_id):
        result = self.db.blocked.find_one_and_delete({'_id': document_id})
        self.db.finished.insert_one(result)

    def _error_one(self, document_id):
        result = self.db.blocked.find_one_and_delete({'_id': document_id})
        self.db.errored.insert_one(result)

    def __enter__(self):
        document, document_id = self._block_one()
        self.document_id = document_id
        self.data = document

        if document is None:
            raise NoMoreWork()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is None:
            self._finish_one(self.document_id)
            self.document_id = None
        else:
            self._error_one(self.document_id)


class DBConnectionPlus(DBConnection):
    def list_databases(self):
        for db in self.client.list_databases():
            print(db)

    def list_collections(self):
        for col in self.db.list_collections():
            print(f"{col['name']}: \t{self.db[col['name']].count_documents({})}")


if __name__ == '__main__':
    import unittest

    class TestConnection(unittest.TestCase):
        def tearDown(self) -> None:
            self.connection.drop_all()
            return super().tearDown()

        def setUp(self) -> None:
            self.connection = DBConnectionPlus('test')
            self.connection.drop_all()
            return super().setUp()

        def test_insert(self):
            for a in range(111):
                self.connection.insert_free({'a': a})

            self.assertEqual(self.connection.db.free.count_documents({}), 111)

        def test_insert_block(self):
            for a in range(111):
                self.connection.insert_free({'a': a})

            returned = []

            for _ in range(100):
                with self.connection as c:
                    self.assertEqual(self.connection.db.blocked.count_documents({}), 1)
                    self.assertIsInstance(c.data['a'], int)
                    returned.append(c.data['a'])

            self.assertEqual(self.connection.db.free.count_documents({}), 11)
            self.assertEqual(self.connection.db.blocked.count_documents({}), 0)
            self.assertEqual(self.connection.db.finished.count_documents({}), 100)

            self.assertEqual(len(set(returned)), len(returned))
            self.assertLess(max(returned), 111)
            self.assertGreaterEqual(min(returned), 0)

        def test_insert_errors(self):
            for a in range(111):
                self.connection.insert_free({'a': a})

            returned = []

            for _ in range(100):
                try:
                    with self.connection as c:
                        self.assertEqual(self.connection.db.blocked.count_documents({}), 1)
                        if c.data['a'] % 2 == 0:
                            raise NotImplementedError('Ups ...')
                        returned.append(c.data)
                except NotImplementedError:
                    pass

            self.assertEqual(self.connection.db.free.count_documents({}), 11)
            self.assertEqual(self.connection.db.blocked.count_documents({}), 0)
            self.assertEqual(self.connection.db.finished.count_documents({}), len(returned))

            r = self.connection.db.free.find({})
            infree = list(map(lambda x: x['a'], r))
            r = self.connection.db.finished.find({})
            infinished = list(map(lambda x: x['a'], r))
            r = self.connection.db.errored.find({})
            inerrored = list(map(lambda x: x['a'], r))

            self.assertEqual(len(infree) + len(infinished) + len(inerrored), 111)
            self.assertEqual(len(set(infree + infinished + inerrored)), 111)

            for a in range(111):
                if a % 2 == 0:
                    self.assertTrue(a in inerrored or a in infree)
                else:
                    self.assertTrue(a in infree or a in infinished)

        def test_renew_errored(self):
            for a in range(111):
                self.connection.insert_free({'a': a})

            returned = []

            for _ in range(100):
                try:
                    with self.connection as c:
                        self.assertEqual(self.connection.db.blocked.count_documents({}), 1)
                        if c.data['a'] % 2 == 0:
                            raise NotImplementedError('Ups ...')
                        returned.append(c.data['a'])
                except NotImplementedError:
                    pass

            self.connection.renew_errored()

            try:
                for _ in range(100):
                    with self.connection as c:
                        self.assertEqual(self.connection.db.blocked.count_documents({}), 1)
                        returned.append(c.data['a'])
            except NoMoreWork:
                pass

            self.assertEqual(len(returned), len(set(returned)))
            self.assertEqual(len(returned), 111)

    unittest.main()
