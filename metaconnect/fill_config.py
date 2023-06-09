#!/usr/bin/python3.11
import argparse
import os

from metaconnect import Node

kerberos_config_string = '''
KerberosAuthentication yes
KerberosTicketCleanup yes
GSSAPIAuthentication yes
GSSAPICleanupCredentials yes
UseDNS yes
'''


def generate_ssh_config(node, config):
    result = f'''
Host {node.SERVER}
\tHostName {node.SERVER_URL}
\tUser {config.user}
'''
    if config.key is not None:
        result += f'''\tIdentityFile {config.key}
    '''
    if config.nopass is not None:
        result += '''\tPasswordAuthentication no
    '''
    return result


def yes_or_no(question):
    while True:
        reply = str(input(question+' (y/n): ')).lower().strip()
        if reply[0] == 'y':
            return True
        if reply[0] == 'n':
            return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='SSHMeta-fill-config',
        description='Adds shortcuts into /.ssh/config file + sshkeys',
    )

    # auth
    parser.add_argument('--user',
                        type=str,
                        default=os.getlogin(),
                        help='username for metacentrum')
    parser.add_argument('--key',
                        type=str,
                        help='path to ssh private key')
    parser.add_argument('--nopass',
                        action='store_true',
                        help='disable password auth.')
    parser.add_argument('--configpath',
                        type=str,
                        default=os.path.expanduser('~/.ssh/config'),
                        help='path where the ssh config is stored')

    args = parser.parse_args()

    # INTERNAL LOGIC:

    q = f'''The program appends {len(Node.ALL_NODES)} items into {args.configpath}
    User = {args.user}
    Key = {'no key' if args.key is None else args.key}
Is this OK? '''

    if yes_or_no(q):
        with open(args.configpath, 'a') as file:
            file.write('\n\n#  >> THIS IS THE START OF AUTOMATICALLY GENERATED INPUT <<\n')

            for node in Node.ALL_NODES:
                file.write(generate_ssh_config(node, args.user, args.key))

            file.write('\n\n#  >> THIS IS THE END OF AUTOMATICALLY GENERATED INPUT <<\n')


