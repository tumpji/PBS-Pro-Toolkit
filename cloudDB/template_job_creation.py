#!/usr/bin/python3
import os
import itertools
from typing import Generator, Dict, Union
from multiprocessing import Process, Queue
import argparse

import cloud_db as db

CHUNK_SIZE = 100
MAX_QUEUE_SIZE = 100


def generator() -> Generator[Dict[str, Union[int, float, str, bool]], None, None]:
    raise NotImplementedError('TODO')
    # example
    #
    # for i in [1,2,3,4,5,6]:
    #     for y in [1,2,3,4,5,6]:
    #         for z in [1,2,3,4,5,6]:
    #             yield {'i': i, 'y': y, 'z': z}


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


if __name__ == '__main__':
    assert(__file__.endswith('.py'))
    experiment_name = os.path.basename(__file__)[:-3]

    parser = argparse.ArgumentParser()
    parser.add_argument('--collection', default=experiment_name, required=False)

    # action
    parser.add_argument('--action',
                        choices=[
                            'insert', 'add',
                            'drop_all', 'clean_all',
                            'refresh_blocked', 'refresh_blocks', 'clean_blocked', 'clean_blocks',
                            'refresh_errored', 'refresh_errors', 'clean_errored', 'clean_errors',
                            'show', 'list', 'display'],
                        required=True)

    # only for inserts
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--multiprocessing', action='store_true')
    parser.add_argument('--threads', type=int, default=None)
    args = parser.parse_args()

    print('Establishing connection...')
    connection = db.DBConnection(args.collection)

    match args.action:
        case 'insert' | 'add':
            print('Insert...')
            if args.multiprocessing:
                multiprocessing(connection, args)
            else:
                for batch_job in get_chunks():
                    connection.insert_many_unfinished_jobs(batch_job)
            print('Ok...')
        case 'drop_all' | 'clean_all':
            print('Droping...')
            connection.drop_everything()
            print('Ok...')
        case 'refresh_blocked' | 'refresh_blocks' | 'clean_blocked' | 'clean_blocks':
            print('Renewing all blocked...')
            connection.renew_all_blocked()
            print('Ok...')
        case 'refresh_errored' | 'refresh_errors' | 'clean_errored' | 'clean_errors':
            print('Renewing all errorred...')
            connection.renew_all_errored()
            print('Ok...')
        case 'show' | 'list' | 'display':
            a = connection.number_of(connection.jobs_unfinished)
            b = connection.number_of(connection.jobs_blocked)
            c = connection.number_of(connection.jobs_errored)
            d = connection.number_of(connection.jobs_finished)
            r = (a + b + c + d)/100
            print(f"Unfinished: {a}, Blocked: {b}, Errored: {c}, Finished: {d}")
            if r > 0:
                print(f"Unfinished: {a/r:.2f}, Blocked: {b/r:.2f}, Errored: {c/r:.2f}, Finished: {d/r:.2f}")
        case _:
            raise NotImplementedError(f"The option '{args.action}' is not implemented")

