#!/usr/bin/python3
import unittest
import time

import datetime
from clouddb import DBConnection


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

