#!/usr/bin/python3
import sys
import runpy
import importlib
import argparse

from cloud_db import DBConnection, NoMoreWork


parser = argparse.ArgumentParser()
parser.add_argument('--collection', type=str, required=True)
parser.add_argument('--package', type=str, required=True)
parser.add_argument('--use-function', action='store_false')

args = parser.parse_args()


print('CloudDB is establishing connection...')
connection = DBConnection(args.collection)

if args.use_function:
    imported_module = importlib.import_module(args.package)

try:
    while True:
        with connection as arg_dict:

            # set new args ...

            if args.use_function:
                imported_module.main(arg_dict)
            else:
                # set args 
                new_args = []
                for key, value in arg_dict.items():
                    new_args.extend((f'--{key}', str(value)))
                sys.argv = new_args

                # call __main__ of module/package
                runpy.run_module(args.package,
                                 run_name='__main__')
except NoMoreWork:
    print('CloudDB is signalling nothing to do...')


