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

import pandas as pd

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

    def get_collectin(self, collection):
        out = list(collection.find({}))
        if len(out):
            return pd.DataFrame(out).drop(columns=['_id',])
        else:
            return None

    def get_unfinished_jobs(self):
        return self.get_collectin(self.jobs_unfinished)

    def get_finished_jobs(self):
        return self.get_collectin(self.jobs_finished)

    def get_blocked_jobs(self):
        return self.get_collectin(self.jobs_blocked)

    def get_errored_jobs(self):
        return self.get_collectin(self.jobs_errored)


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
                result = list(self.jobs_errored.find({}))
                if len(result):
                    self.jobs_unfinished.insert_many(result)
                    self.jobs_errored.delete_many({})

    def renew_all_blocked(self) -> None:
        with self.client.start_session() as session:
            with session.start_transaction():
                # remove column '_start_time'
                self.jobs_blocked.update_many({}, {'$unset': {'_start_time': ''}})
                result = list(self.jobs_blocked.find({}))
                if len(result):
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
