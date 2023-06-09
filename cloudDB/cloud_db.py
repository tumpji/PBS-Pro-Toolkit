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
#        result = connection.insert_one_unfinished_job(data)
#
#    # ------------------------------------------------------------------
#    # get work from database
#
#    try:
#        while True:
#            with connection as data:
#                print(f"Processing: {data}")
#                # if raise, the data will be in the errored db
#
#    except NoMoreWork:
#        print('Finished')
#
#    # ------------------------------------------------------------------
#    # move erroed to free
#    connection.renew_all_errored()

import os
import datetime
from typing import List, Dict, Any
from urllib.parse import quote_plus as quote

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

import configparser

JobType = Dict[str, Any]


class NoMoreWork(StopIteration):
    pass


class DBConnectionBase:
    '''
    Connects to the database specified by the configuration file

    '''

    def __init__(self, collection_name: str, config_path=None):
        config = configparser.ConfigParser()

        # 1. try to find AUTHENTICATION.ini
        if config_path is not None:
            config.read(config_path)
        elif 'CloudDBAuthenticationPath' in os.environ:
            config.read(os.environ['CloudDBAuthenticationPath'])
        elif 'AUTHENTICATION.ini' in os.listdir():
            config.read('AUTHENTICATION.ini')
        else:
            raise FileNotFoundError('The AUTHENTICATION.ini file is not found')

        config = config['CloudDB']

        urluser = f"{quote(config['USERNAME'])}:{quote(config['PASSWORD'])}"
        urlhost = f"{config['HOST']}:{config['PORT']}"
        uri = f"mongodb://{urluser}@{urlhost}/{collection_name}?authSource=admin"

        self.client = MongoClient(uri)
        self.db = self.client[collection_name]


class DBConnectionToolKit(DBConnectionBase):
    '''
        Defines basic operations with db database
        this subset of operations uses the user

        JOBS_UNFINISHED --------------------------------------> JOBS_BLOCKED
          ^-- [renew_blocked_timedelta, renew_all_blocked] ------- .   .
                                                                   .  JOBS_FINISHED
                                                                   .
          ^---[renew_all_errored] --------------------------- JOBS_ERRORED
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.jobs_unfinished = self.db.jobs_unfinished
        self.jobs_blocked = self.db.jobs_blocked
        self.jobs_errored = self.db.jobs_errored
        self.jobs_finished = self.db.jobs_finished

    def number_of(self, collection: Collection):
        ''' returns the number of elements in the collection '''
        return collection.count_documents({})

    def insert_one_unfinished_job(self, job: JobType):
        self.jobs_unfinished.insert_one(job)

    def insert_many_unfinished_jobs(self, jobs: List[JobType]):
        self.jobs_unfinished.insert_many(jobs)

    # removals
    def drop(self, collection: Collection) -> None:
        collection.drop()

    def drop_everything(self) -> None:
        self.drop(self.jobs_finished)
        self.drop(self.jobs_unfinished)
        self.drop(self.jobs_errored)
        self.drop(self.jobs_blocked)

    def renew_all_errored(self) -> None:
        with self.client.start_session() as session:
            with session.start_transaction():
                # remove column '_start_time'
                self.jobs_errored.update_many({}, {'$unset': {'_start_time': ''}})
                result = self.jobs_errored.find({})
                self.jobs_unfinished.insert_many(result)
                self.jobs_errored.delete_many({})

    def renew_all_blocked(self) -> None:
        with self.client.start_session() as session:
            with session.start_transaction():
                # remove column '_start_time'
                self.jobs_blocked.update_many({}, {'$unset': {'_start_time': ''}})
                result = self.jobs_blocked.find({})
                self.jobs_unfinished.insert_many(result)
                self.jobs_blocked.delete_many({})

    def renew_blocked_timedelta(self, timedelta: datetime.timedelta) -> None:
        time = datetime.datetime.utcnow() - timedelta
        result = self.jobs_blocked.find({'_start_time': {'$lte': time}})
        for job in result:
            del job['_start_time']
            with self.client.start_session() as session:
                with session.start_transaction():
                    self.jobs_blocked.find_one_and_delete({'_id': job['_id']})
                    self.insert_one_unfinished_job(job)

    def move_job_from_blocked_to_errored(self, jid: int) -> None:
        with self.client.start_session() as session:
            with session.start_transaction():
                result = self.jobs_blocked.find_one_and_delete({'_id': jid})
                del result['_start_time']
                self.jobs_errored.insert_one(result)

    def move_job_from_blocked_to_finished(self, jid: int) -> None:
        with self.client.start_session() as session:
            with session.start_transaction():
                result = self.jobs_blocked.find_one_and_delete({'_id': jid})
                self.jobs_finished.insert_one({
                    **result,
                    '_finish_time': datetime.datetime.utcnow()
                })

    def move_job_from_unfinished_to_blocked(self) -> Dict:
        with self.client.start_session() as session:
            with session.start_transaction():
                document = self.jobs_unfinished.find_one_and_delete({})

                if document is None:
                    return None

                self.jobs_blocked.insert_one(
                    {**document, '_start_time': datetime.datetime.utcnow()}
                )
                return document


class DBConnection(DBConnectionToolKit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._jobid = None

    def __enter__(self):
        job = self.move_job_from_unfinished_to_blocked()

        if job is None:
            raise NoMoreWork()

        self._jobid = job['_id']
        del job['_id']
        return job

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is None:
            self.move_job_from_blocked_to_finished(self._jobid)
        else:
            self.move_job_from_blocked_to_errored(self._jobid)
        self._jobid = None





'''
class DBConnectionPlus(DBConnection):
    def list_databases(self):
        for db in self.client.list_databases():
            print(db)

    def list_collections(self):
        for col in self.db.list_collections():
            print(f"{col['name']}: \t{self.db[col['name']].count_documents({})}")
'''


if __name__ == '__main__':
    import unittest
    import time

    class TestConnection(unittest.TestCase):
        def tearDown(self) -> None:
            self.connection.drop_everything()
            return super().tearDown()

        def setUp(self) -> None:
            self.connection = DBConnection('test')
            self.connection.drop_everything()
            return super().setUp()

        @property
        def unfinished(self):
            return self.connection.number_of(self.connection.jobs_unfinished)

        @property
        def blocked(self):
            return self.connection.number_of(self.connection.jobs_blocked)

        @property
        def erroed(self):
            return self.connection.number_of(self.connection.jobs_errored)

        @property
        def finished(self):
            return self.connection.number_of(self.connection.jobs_finished)

        def test_insert_one(self):
            ''' insert_one_unfinished_job
                move_job_from_unfinished_to_blocked
            '''
            for a in range(11):
                self.connection.insert_one_unfinished_job({'a': a, 'b': a*2, 'aloha': 'agro'})
                self.assertEqual(a+1, self.unfinished)

            self.assertEqual(0, self.blocked)
            self.assertEqual(0, self.erroed)
            self.assertEqual(0, self.finished)

            h = set()
            for a in range(11):
                res = self.connection.move_job_from_unfinished_to_blocked()
                self.assertIsInstance(res, dict)
                self.assertEqual(res['aloha'], 'agro')
                self.assertEqual(res['b'], res['a']*2)
                h.add(res['a'])

                self.assertEqual(11-(a+1), self.unfinished)
                self.assertEqual(  +(a+1), self.blocked)

            self.assertEqual(set(range(11)), h)

        def test_insert_many(self):
            self.connection.insert_many_unfinished_jobs([{'a': b} for b in range(41)])
            self.assertEqual(41, self.unfinished)
            self.assertEqual(0, self.blocked)
            self.assertEqual(0, self.erroed)
            self.assertEqual(0, self.finished)

            res = self.connection.move_job_from_unfinished_to_blocked()
            self.assertLess(res['a'], 41)

        def test_renew_blocked(self):
            self.connection.insert_many_unfinished_jobs([{'a': b} for b in range(2)])
            self.connection.move_job_from_unfinished_to_blocked()

            self.assertEqual(1, self.unfinished)
            self.assertEqual(1, self.blocked)

            self.connection.renew_all_blocked()

            self.assertEqual(2, self.unfinished)
            self.assertEqual(0, self.blocked)

            t = set([
                self.connection.move_job_from_unfinished_to_blocked()['a'],
                self.connection.move_job_from_unfinished_to_blocked()['a']
            ])
            self.assertEqual(t, set(range(2)))

        def test_renew_errored(self):
            self.connection.insert_many_unfinished_jobs([{'a': b} for b in range(4)])

            ids = []
            for _ in range(2):
                res = self.connection.move_job_from_unfinished_to_blocked()
                self.connection.move_job_from_blocked_to_errored(res['_id'])
                ids.append(res['_id'])

            res = self.connection.move_job_from_unfinished_to_blocked()

            self.assertEqual(1, self.unfinished)
            self.assertEqual(1, self.blocked)
            self.assertEqual(2, self.erroed)
            self.assertEqual(0, self.finished)

            self.connection.renew_all_errored()

            self.assertEqual(3, self.unfinished)
            self.assertEqual(1, self.blocked)
            self.assertEqual(0, self.erroed)
            self.assertEqual(0, self.finished)

            next_ids = []
            for _ in range(3):
                res = self.connection.move_job_from_unfinished_to_blocked()
                next_ids.append(res['_id'])

            self.assertIn(ids[0], next_ids)
            self.assertIn(ids[1], next_ids)

        def test_renew_blocked_timedelta(self):
            self.connection.insert_many_unfinished_jobs([{'a': b} for b in range(4)])

            ids = []
            for _ in range(2):
                res = self.connection.move_job_from_unfinished_to_blocked()
                ids.append(res['_id'])

            time.sleep(5)
            for _ in range(2):
                res = self.connection.move_job_from_unfinished_to_blocked()

            self.connection.renew_blocked_timedelta(datetime.timedelta(seconds=3))

            self.assertEqual(2, self.unfinished)
            self.assertEqual(2, self.blocked)
            self.assertEqual(0, self.erroed)
            self.assertEqual(0, self.finished)

            t = set([
                self.connection.move_job_from_unfinished_to_blocked()['_id'],
                self.connection.move_job_from_unfinished_to_blocked()['_id']
            ])
            self.assertEqual(set(ids), t)

        def test_empty(self):
            res = self.connection.move_job_from_unfinished_to_blocked()
            self.assertIsNone(res)


    unittest.main()
