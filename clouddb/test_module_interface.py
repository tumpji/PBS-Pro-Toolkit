#!/usr/bin/python3
import unittest
import itertools
import tempfile
import runpy
import json
import sys
import os
from mock import patch

import clouddb as db


def main(kwargs):
    path = kwargs['path']
    del kwargs['path']

    with open(path, 'a') as f:
        f.write(json.dumps(kwargs, sort_keys=True))
        f.write('\n')


if __name__ == '__main__':
    class TestArguments(unittest.TestCase):
        def setUp(self) -> None:
            self.db = db.DBConnection('test')
            self.db.drop_everything()

            self.tmpfileObj = tempfile.NamedTemporaryFile()
            self.tmpfile = self.tmpfileObj.__enter__()

            args = itertools.product(
                [11, 12, 20],
                ['ahoj', 'jak', 'se'],
                [111.5, 2.75, 4.25],
                [True, False],
                [self.tmpfile.name, ]
            )
            for intarg, strarg, floatarg, boolarg, path in args:
                self.db.insert_one_unfinished_job({
                    'intarg': intarg,
                    'strarg': strarg,
                    'boolarg': boolarg,
                    'floatarg': floatarg,
                    'path': path
                })

        def tearDown(self) -> None:
            path = self.tmpfile.name
            self.tmpfileObj.__exit__(None, None, None)
            if os.path.exists(path):
                raise NotImplementedError('AAA')

        def is_valid_item(self, data):
            self.assertIn('intarg', data)
            self.assertIn('floatarg', data)
            self.assertIn('boolarg', data)
            self.assertIn('strarg', data)

            self.assertIsInstance(data['intarg'], int)
            self.assertIsInstance(data['strarg'], str)
            self.assertIsInstance(data['floatarg'], float)
            self.assertIsInstance(data['boolarg'], bool)

            self.assertIn(data['intarg'], [11, 12, 20])
            self.assertIn(data['strarg'], ['ahoj', 'jak', 'se'])
            self.assertIn(data['floatarg'], [111.5, 2.75, 4.25])
            self.assertIn(data['boolarg'], [True, False])

        def test_typing(self):
            with self.db as data:
                self.is_valid_item(data)

        def test_number_of_arguments(self):
            with self.db as data:
                self.assertEqual(len(data), 5)

        def test_function_main(self):
            sys.argv = ['cloudDB.__main__',
                        '--collection', 'test',
                        '--package', 'test_module_interface']

            with open(os.devnull, 'w') as devnull:
                with patch('sys.stdout', devnull):
                    with patch('sys.stderr', devnull):
                        runpy.run_module('cloudDB', run_name='__main__')

            dlist = []
            with open(self.tmpfile.name, 'r') as f:
                for line in f:
                    d = json.loads(line)
                    self.is_valid_item(d)
                    dlist.append(d)

            args = itertools.product(
                [11, 12, 20],
                ['ahoj', 'jak', 'se'],
                [111.5, 2.75, 4.25],
                [True, False],
            )

            for intarg, strarg, floatarg, boolarg in args:
                d = {'intarg': intarg,
                     'strarg': strarg,
                     'boolarg': boolarg,
                     'floatarg': floatarg}
                self.assertIn(d, dlist)

    unittest.main(verbosity=2)

