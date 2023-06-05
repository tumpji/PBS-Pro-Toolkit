#!/usr/bin/python3
import os
import re
import operator
from collections import defaultdict, OrderedDict

import csv
import config_path
import configparser

import argparse
import subprocess
from thefuzz import process


def chain_map(*lambdas):
    def wrapper(x):
        for lam in lambdas:
            x = lam(x)
        return x
    return wrapper


def yes_or_no(question):
    while True:
        reply = str(input(question+' (y/n): ')).lower().strip()
        if reply[0] == 'y':
            return True
        if reply[0] == 'n':
            return False


class ConfigurationManager:
    def __init__(self):
        self.path_obj = config_path.ConfigPath('metaconnect', 'psb-pro-toolkit', '.ini')
        self.directory_path = self.path_obj.saveFolderPath(mkdir=True)

        self.config_path = os.path.join(self.directory_path, 'ssh.ini')
        self.server_list_path = os.path.join(self.directory_path, 'servers.csv')

        self.config = configparser.ConfigParser()

        if os.path.exists(self.config_path):
            self.config.read(self.config_path)
        else:
            self.config.read_string(self._default_config())
            with open(self.config_path, 'w') as file:
                self.config.write(file)

        # server list
        if os.path.exists(self.server_list_path):
            path = self.server_list_path
        else:
            path = self._default_server_list_path()

        self.server_list = []
        with open(path, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            for line in reader:
                if len(line):
                    self.server_list.append(line)

    def _default_config(self):
        return f'''[AUTHENTICATION]
USER={os.getlogin()}
KEYFILE=
'''

    def _default_server_list_path(self):
        return os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'DEFAULT_SERVER_LIST.csv'
        )

    def __getitem__(self, item):
        return self.config[item]


def normalize_string(s):
    s = s.lower().strip()
    return s


def maybe_str_or_int(arg):
    try:
        return int(arg)
    except ValueError:
        pass
    return arg


def generate_str_or_int(name, dic, alternative=None):
    def wrapper(arg):
        r = maybe_str_or_int(arg)
        if isinstance(r, int):
            if r < 0:
                raise ValueError(f'Negative values for index of {name}s are forbiden')
            elif r >= len(dic):
                raise ValueError('There is no server with that index')
            return list(dic.items())[r][0]
        else:
            full_options = dict((x, x) for x in dic)
            if alternative:
                for x in dic:
                    alt = alternative(x)
                    for a in alt if alt is not None else []:
                        full_options[a] = x

            option = process.extractOne(r, full_options, score_cutoff=30)
            if option is None:
                raise ValueError(f'No {name} with similar name is found')

            return dic[full_options[option[0]]][0]
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
    def initialize(cls, configuration):
        for x in configuration.server_list:
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


configuration = ConfigurationManager()
Node.initialize(configuration)
Node.finalize()


maybe_str_or_int_server = generate_str_or_int('server', Node.DICT_SERVER)
maybe_str_or_int_storage = generate_str_or_int(
    'server', Node.DICT_STORAGE, alternative=lambda x: x.split('-'))
maybe_str_or_int_organization = generate_str_or_int('server', Node.DICT_ORGANIZATION)


def main(*args):
    # defines parser
    parser = argparse.ArgumentParser(
        prog='SSHMeta',
        description='Establish a connection to MetaCentrum servers',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('-s', '--server',
                        type=maybe_str_or_int_server,
                        help='Name or index of a server:\n' + '\n'.join(
                            f'\t{i}) {n[0]}' for i, n in enumerate(Node.DICT_SERVER.values())),
                        )
    parser.add_argument('-d', '--storage', '--disk',
                        type=maybe_str_or_int_storage,
                        help='Name or index of a storage:\n' + '\n'.join(
                            f'\t{i}) {n}' for i, n in enumerate(Node.DICT_STORAGE.keys())),
                        )
    parser.add_argument('-o', '--organization', '--org',
                        type=maybe_str_or_int_organization,
                        help='Name or index of an organization:\n' + '\n'.join(
                            f'\t{i}) {n}' for i, n in enumerate(Node.DICT_ORGANIZATION.keys())),
                        )
    parser.add_argument('--scp',
                        nargs=2, type=str,
                        help='download #1 argument to #2 argument'
                        )
    parser.add_argument('--command', '--cmd', type=str,
                        help='run this command only'
                        )

    args = parser.parse_args(*args)

    if args.server is not None:
        server = args.server
    elif args.storage is not None:
        server = args.storage
    elif args.organization is not None:
        server = args.organization
    else:
        server = Node.ALL_NODES[0]

    if args.scp and args.command:
        print('The use of SCP and command is not supported')
        exit(1)

    print(f'Connecting to the {server}:')
    print(f'\t{server.STORAGE}\t{server.ORGANIZATION}')
    print('-'*60)

    user = configuration['AUTHENTICATION']['USER']

    if args.scp is not None:
        subprocess.call([
            'scp',
            f'{user}@{server.SERVER_URL}:{args.scp[0]}',
            args.scp[1]
        ])
    else:
        subprocess.call([
                'ssh',
                f'{user}@{server.SERVER_URL}'
            ]
            +
            ([args.command] if args.command else [])
        )


if __name__ == '__main__':
    main()


