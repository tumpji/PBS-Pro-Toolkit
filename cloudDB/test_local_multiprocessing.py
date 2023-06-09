#!/usr/bin/python3
import os
import time
import tqdm
from multiprocessing import Process, Queue

import cloud_db as dbmodule


def compute(q: Queue):
    o = []
    try:
        while True:
            with connection as data:
                o.append(data['task'])

                assert(data['task'] == data['control'] // 2)
                assert(data['extra'] == 'extra')
                time.sleep(0.00001)

    except dbmodule.NoMoreWork:
        pass

    q.put(o)


print('Establish connection')
connection = dbmodule.DBConnection('test')

# remove data
print('Removing data from previous test')
connection.drop_everything()

# fill in work
N = 2000
print('Inserting data:')
for task in tqdm.tqdm(iterable=range(N), total=N):
    connection.insert_one_unfinished_job({'task': task, 'control': task * 2, 'extra': 'extra'})


# ---------------------------------------------------------------------------
# --- worker:

q = Queue()
processes = []

print('Creating Processes:')
for i in range(os.cpu_count() or 4):
    processes.append(Process(target=compute, args=(q,)))

print('Starting Processes:')
for i in range(len(processes)):
    processes[i].start()

print('Joining: ')
for process in tqdm.tqdm(iterable=processes):
    process.join()
    print(time.time())

print('\nValues: ')
while not q.empty():
    print(q.get())






