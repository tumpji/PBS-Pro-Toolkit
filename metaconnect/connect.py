#!/usr/bin/python3.11
from collections import defaultdict, OrderedDict
from io import StringIO
import csv
import operator
import re
import argparse
from fuzzywuzzy import process

server_csv = '''
skirit.ics.muni.cz 	Debian 11 	/storage/brno2/home/ 	meta-pbs.metacentrum.cz 	
alfrid.meta.zcu.cz 	Debian 11 	/storage/plzen1/home/ 	meta-pbs.metacentrum.cz 	
tarkil.grid.cesnet.cz 	Debian 11 	/storage/praha1/home/ 	meta-pbs.metacentrum.cz 	
nympha.zcu.cz 	Debian 11 	/storage/plzen1/home/ 	meta-pbs.metacentrum.cz 	
charon.nti.tul.cz 	Debian 11 	/storage/liberec3-tul/home/ 	meta-pbs.metacentrum.cz 	
minos.zcu.cz 	Debian 11 	/storage/plzen1/home/ 	meta-pbs.metacentrum.cz 	alias for nympha.zcu.cz 	
perian.grid.cesnet.cz 	Debian 10 	/storage/brno2/home/ 	meta-pbs.metacentrum.cz 	
onyx.metacentrum.cz 	Debian 10 	/storage/brno2/home/ 	meta-pbs.metacentrum.cz 	alias for perian.grid.cesnet.cz
tilia.ibot.cas.cz 	Debian 11 	/storage/pruhonice1-ibot/home/ 	meta-pbs.metacentrum.cz 	Cluster of the Institute of Botany, CAS
zuphux.cerit-sc.cz 	CentOS 7.9 	/storage/brno3-cerit/home/ 	cerit-pbs.cerit-sc.cz 	
elmo.elixir-czech.cz 	Debian 11 	/storage/praha5-elixir/home/ 	elixir-pbs.elixir-czech.cz 	
''' + \
'''
builder.metacentrum.cz	Debian 11	/storage/praha1/home/	meta-pbs.metacentrum.cz	
'''


def normalize_string(s):
    s = s.lower().strip()
    return s


def maybe_str_or_int(arg):
    try:
        return int(arg)
    except ValueError:
        pass
    return arg


def maybe_str_or_int_server(arg):
    r = maybe_str_or_int(arg)
    if isinstance(r, int):
        if r < 0:
            raise ValueError('Negative values for index of servers are forbiden')
        elif r >= len(Node.DICT_SERVER):
            raise ValueError('There is no server with that index')
        return list(Node.DICT_SERVER.items())[r][0]
    else:
        option = process.extractOne(r,
                                    list(Node.DICT_SERVER),
                                    score_cutoff=30)
        if option is None:
            raise ValueError('No server with similar name is found')
        return Node.DICT_SERVER[option[0]][0]


def maybe_str_or_int_storage(arg):
    r = maybe_str_or_int(arg)
    if isinstance(r, int):
        if r < 0:
            raise ValueError('Negative values for index of storages are forbiden')
        elif r >= len(Node.DICT_STORAGE):
            raise ValueError('There is no storage with that index')
        return list(Node.DICT_STORAGE.items())[r][0]
    else:
        option = process.extractOne(r,
                                    list(Node.DICT_STORAGE),
                                    score_cutoff=30)
        if option is None:
            raise ValueError('No storage with similar name is found')
        return Node.DICT_STORAGE[option[0]][0]


class Node:
    ALL_NODES = []

    DICT_STORAGE = defaultdict(list)
    DICT_SERVER = defaultdict(list)
    DICT_OS = defaultdict(list)
    DICT_ORGANIZATION = defaultdict(list)

    def __init__(self, settings):
        self.SERVER_URL = settings[0]
        self.SERVER = re.match(r'[^\.]*', self.SERVER_URL)[0]
        self.OS = normalize_string(settings[1])
        self.STORAGE = re.match(r'/[^/]*/([^/]*)', settings[2]).group(1)
        self.ORGANIZATION = settings[3]

        Node.ALL_NODES.append(self)
        Node.DICT_STORAGE[self.STORAGE].append(self)
        Node.DICT_SERVER[self.SERVER].append(self)
        Node.DICT_OS[self.OS].append(self)
        Node.DICT_ORGANIZATION[self.ORGANIZATION].append(self)

    def __repr__(self):
        return self.SERVER

    @classmethod
    def finalize(cls):
        for attrb in ['STORAGE', 'SERVER', 'OS', 'ORGANIZATION']:
            attrb = f'DICT_{attrb}'
            obj = OrderedDict(sorted(
                getattr(cls, attrb).items(), key=operator.itemgetter(0)))
            setattr(cls, attrb, obj)

    @classmethod
    def initialize(cls):
        reader = csv.reader(StringIO(server_csv), delimiter='\t')
        for x in reader:
            if len(x):
                Node(x)

    @classmethod
    def print_options(cls):
        print('-'*80, io)
        for name, dct in [
                ('Servers:', cls.DICT_SERVER),
                ('Storages:', cls.DICT_STORAGE)]:
            print(name)
            for i, x in enumerate(dct):
                print(f'\t{i:<3} {x}')


Node.initialize()
Node.finalize()

if __name__ == '__main__':
    # defines parser
    parser = argparse.ArgumentParser(
        prog='SSHMeta',
        description='Establish a connection to MetaCentrum servers',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('-s', '--server',
                        type=maybe_str_or_int_server,
                        help='Name or index of a server:\n' + '\n'.join(
                            f'\t{i}) {n[0]}' for i,n in enumerate(Node.DICT_SERVER.values())),
                        )
    parser.add_argument('-d', '--storage', '--disk',
                        type=maybe_str_or_int_storage,
                        help='Name or index of a storage:\n' + '\n'.join(
                            f'\t{i}) {n[0]}' for i,n in enumerate(Node.DICT_STORAGE.values())),
                        )

    args = parser.parse_args()

    # defines default response
    if args.server is None and args.storage is None:
        server = Node.ALL_NODES[0]
    else:
        server = args.server or args.storage

    print('Processing:')
    print(server)



