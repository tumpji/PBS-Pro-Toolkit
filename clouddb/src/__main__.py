#!/usr/bin/python3
import sys
import runpy
import importlib
import argparse

from clouddb import DBConnection, NoMoreWork
from metastats import MetaStatsWithDefaults


parser = argparse.ArgumentParser()
parser.add_argument('--collection', type=str, required=True)
parser.add_argument('--package', type=str, required=True)

parser.add_argument('--end_prematurely_sec', type=int, default=30*60)

args = parser.parse_args()


print('CloudDB is establishing connection...')
connection = DBConnection(args.collection)

if args.use_function:

    imported_module = importlib.import_module(args.package)

try:
    while True:
        with connection as arg_dict:
            imported_module.main(**arg_dict)

            time_left = MetaStatsWithDefaults.time_remaining
            if time_left is not None:
                if time_left < args.end_prematurely_sec:
                    break
except NoMoreWork:
    print('CloudDB is signalling nothing to do...')
