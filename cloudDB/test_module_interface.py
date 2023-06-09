#!/usr/bin/python3
import unittest
import itertools
import cloud_db as db


if __name__ == '__main__':
    class TestArguments(unittest.TestCase):
        def setUp(self) -> None:
            self.db = db.DBConnection('test')
            self.db.drop_everything()

            args = itertools.product(
                [11, 12, 20],
                ['ahoj', 'jak', 'se'],
                [111.5, 2.75, 4.25],
                [True, False],
            )
            for intarg, strarg, floatarg, boolarg in args:
                self.db.insert_one_unfinished_job({
                    'intarg': intarg,
                    'strarg': strarg,
                    'boolarg': boolarg,
                    'floatarg': floatarg
                })

        def testTypes(self):
            with self.db as data:
                self.assertIn('intarg', data)
                self.assertIn('floatarg', data)
                self.assertIn('boolarg', data)
                self.assertIn('strarg', data)

                self.assertIsInstance(data['intarg'], int)
                self.assertIsInstance(data['strarg'], str)
                self.assertIsInstance(data['floatarg'], float)
                self.assertIsInstance(data['boolarg'], bool)

    unittest.main(verbosity=2)

