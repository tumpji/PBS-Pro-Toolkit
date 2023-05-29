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


def generate_str_or_int(name, dic ):
    def wrapper(arg):
        r = maybe_str_or_int(arg)
        if isinstance(r, int):
            if r < 0:
                raise ValueError(f'Negative values for index of {name}s are forbiden')
            elif r >= len(dic):
                raise ValueError('There is no server with that index')
            return list(dic.items())[r][0]
        else:
            option = process.extractOne(r, list(dic), score_cutoff=30)
            if option is None:
                raise ValueError(f'No {name} with similar name is found')
            return dic[option[0]][0]
    return wrapper


class Node:
    ALL_NODES = []

    DICT_STORAGE = defaultdict(list)
    DICT_SERVER = defaultdict(list)
    DICT_OS = defaultdict(list)
    DICT_ORGANIZATION = defaultdict(list)

    def __init__(self, settings):
        self.SERVER_URL = settings[0].rstrip()
        self.SERVER = re.match(r'[^\.]*', self.SERVER_URL)[0]
        self.OS = normalize_string(settings[1])
        self.STORAGE = re.match(r'/[^/]*/([^/]*)', settings[2]).group(1)
        self.ORGANIZATION = normalize_string(settings[3])

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
        print('-'*80)
        for name, dct in [
                ('Servers:', cls.DICT_SERVER),
                ('Storages:', cls.DICT_STORAGE)]:
            print(name)
            for i, x in enumerate(dct):
                print(f'\t{i:<3} {x}')


Node.initialize()
Node.finalize()

maybe_str_or_int_server = generate_str_or_int('server', Node.DICT_SERVER)
maybe_str_or_int_storage = generate_str_or_int('server', Node.DICT_STORAGE)
maybe_str_or_int_organization = generate_str_or_int('server', Node.DICT_ORGANIZATION)

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
                            f'\t{i}) {n}' for i,n in enumerate(Node.DICT_STORAGE.keys())),
                        )
    parser.add_argument('-o', '--organization', '--org',
                        type=maybe_str_or_int_organization,
                        help='Name or index of an organization:\n' + '\n'.join(
                            f'\t{i}) {n}' for i,n in enumerate(Node.DICT_ORGANIZATION.keys())),
                        )

    args = parser.parse_args()

    if args.server is not None:
        server = args.server
    elif args.storage is not None:
        server = args.storage
    elif args.organization is not None:
        server = args.organization
    else:
        server = Node.ALL_NODES[0]


    print('Processing:')
    print(server)



