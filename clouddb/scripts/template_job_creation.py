#!/usr/bin/python3
#insertpath
import os
import itertools
from typing import Generator, Dict, Union
from multiprocessing import Process, Queue
import argparse

import clouddb as db

CHUNK_SIZE = 100
MAX_QUEUE_SIZE = 100


def generator() -> Generator[Dict[str, Union[int, float, str, bool]], None, None]:
    #raise NotImplementedError('TODO')
    for fid in range(1, 24+1):
        for dim in [2,5,10,20]:
            for seed in [1,2,3,4,5]:
                yield dict(locals())

                # or 
                # yield {'i': i, 'y': y, 'z': z}


def slave(connection: db.DBConnection, queue: Queue):
    while True:
        batch_job = queue.get()

        if batch_job is None:
            break

        connection.insert_many_unfinished_jobs(batch_job)


def multiprocessing(connection, args):
    n_process = args.threads or os.cpu_count() or 4

    print(f'Creating {n_process} workers...')

    queue = Queue(maxsize=MAX_QUEUE_SIZE)
    processes = []

    for i in range(n_process):
        process = Process(target=slave, args=(connection, queue))
        process.start()
        processes.append(process)

    for chunk in get_chunks():
        queue.put(chunk)

    for _ in range(n_process):
        queue.put(None)

    for i in range(n_process):
        processes[i].join()


def get_chunks():
    ''' uses the generator to create lists of objects insted of object '''
    iterator = iter(generator())
    while True:
        chunk = list(itertools.islice(iterator, CHUNK_SIZE))
        if len(chunk) == 0:
            break
        yield chunk


def parse_args(default_experiment_name):
    # set up the parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--collection', default=experiment_name, required=False)

    subparsers = parser.add_subparsers(
        dest='action',
        metavar='ACTION',
        required=True
    )

    # insert
    insert = subparsers.add_parser(
                'insert',
                help='insert jobs specified in the generator() function'
    )
    insert.add_argument('--multiprocessing', action='store_true')
    insert.add_argument('--threads', type=int, default=None)

    # drop
    drop = subparsers.add_parser(
                'drop',
                help='drop jobs in DESTINATION collection'
    )
    drop.add_argument('destination',
                      choices=['all', ],
                      metavar='DESTINATION'
                      )

    # refresh
    refresh = subparsers.add_parser(
                'refresh',
                help='moves all elements in collection YYY back to start')
    refresh.add_argument('destination',
                         choices=['block', 'error'],
                         )

    # show
    show = subparsers.add_parser(
                'show',
                help='displays information about the database')
    show.add_argument('destination',
                      nargs=argparse.REMAINDER,
                      choices=['stats', 'unfinished', 'error', 'block', 'finished'],
                      )

    return parser.parse_args()


if __name__ == '__main__':
    assert(__file__.endswith('.py'))
    experiment_name = os.path.basename(__file__)[:-3]

    args = parse_args(experiment_name)

    print('Establishing connection...')
    connection = db.DBConnection(args.collection)

    if args.action == 'insert':
        print('Insert...')
        if args.multiprocessing:
            multiprocessing(connection, args)
        else:
            for batch_job in get_chunks():
                connection.insert_many_unfinished_jobs(batch_job)
    elif args.action == 'drop' and args.destination == 'all':
        print('Removing all documents...')
        connection.drop_everything()
    elif args.action == 'refresh' and args.destination == 'block':
        print('Renewing all blocked...')
        connection.renew_all_blocked()
    elif args.action == 'refresh' and args.destination == 'error':
        print('Renewing all errorred...')
        connection.renew_all_errored()
    elif args.action == 'show':
        if 'stats' in args.destination:
            print('\nStats:')
            a = connection.number_of(connection.jobs_unfinished)
            b = connection.number_of(connection.jobs_blocked)
            c = connection.number_of(connection.jobs_errored)
            d = connection.number_of(connection.jobs_finished)
            r = (a + b + c + d)/100
            print(f"Unfinished: {a}, Blocked: {b}, Errored: {c}, Finished: {d}")
            if r > 0:
                print(f"Unfinished: {a/r:.2f}%, Blocked: {b/r:.2f}%, Errored: {c/r:.2f}%, Finished: {d/r:.2f}%")
        if 'unfinished' in args.destination:
            print('\nUnfinished:')
            print(connection.get_unfinished_jobs())
        if 'block' in args.destination:
            print('\nBlocked:')
            print(connection.get_blocked_jobs())
        if 'error' in args.destination:
            print('\nErrored:')
            print(connection.get_errored_jobs())
        if 'finished' in args.destination:
            print('\nFinished:')
            print(connection.get_finished_jobs())
    else:
        raise NotImplementedError(f"The option '{args}' is not implemented")
