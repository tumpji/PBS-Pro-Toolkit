#!/usr/bin/python3
from io import StringIO
import csv
import operator
import re
import argparse
import functools

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
'''


def normalize_string(s):
    s = s.lower().strip()
    return s


class Node:
    def __init__(self, settings):
        self.SERVER_URL = settings[0]
        self.SERVER = re.match(r'[^\.]*', self.SERVER_URL)[0]
        self.OS = normalize_string(settings[1])
        self.STORAGE = re.match(r'/[^/]*/([^/]*)', settings[2]).group(1)
        self.ORGANIZATION = settings[3]

    def __repr__(self):
        return self.SERVER

    @staticmethod
    def list_data(field):
        return dict(enumerate(sorted(set(
        map(operator.attrgetter(field), nodes)
        ))))

    @staticmethod
    @functools.lru_cache()
    def servers():
        return Node.list_data('SERVER')

    @staticmethod
    @functools.lru_cache()
    def storages():
        return Node.list_data('STORAGE')


nodes = []

reader = csv.reader(StringIO(server_csv), delimiter='\t')
for x in reader:
    if len(x):
        nodes.append(Node(x))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='SSHMeta',
        description='Establish a connection to MetaCentrum servers')
    parser.add_argument('-s', '--server', type=int)
    parser.add_argument('-d', '--disk', '--storage', type=int)
    args = parser.parse_args()

    if args.server is None and args.disk is None:
        print('-'*80)

        print('Servers:')
        for i,x in Node.servers().items():
            print(f'\t{i:<3} {x}')

        print('Disks:')
        for i,x in Node.storages().items():
            print(f'\t{i:<3} {x}')

        exit(0)

    #pool = []
    #if args.




