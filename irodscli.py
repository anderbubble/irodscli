#!/usr/bin/env python3

# TODO
# - change pwd to a collection?
# - handle EOF
# - handle invalid collection
# - handle ls of data object
# - handle ls of glob
# - rstrip /, restrict to collection
# - implement PurePosixPath.resolve()
# - implement cd
#   - cd
#   - cd -
# - implement ls -l
# - pwd
# - handle error parsing cli


import argparse
import getpass
import irods.collection
import irods.data_object
import irods.exception
import irods.session
import itertools
import os
import pathlib
import shlex
import sys
import urllib.parse


DEFAULT_PORT = 1247


def main ():
    script_parser = argparse.ArgumentParser()
    script_parser.add_argument('url')

    cli_parser = argparse.ArgumentParser(prog=None)
    cli_subparsers = cli_parser.add_subparsers(dest='command')

    ls_parser = cli_subparsers.add_parser('ls')
    ls_parser.add_argument('targets', nargs='*', type=pathlib.PurePosixPath)
    ls_parser.add_argument('-F', '--classify', action='store_true', default=False)
    ls_parser.add_argument('--sort', action='store_true', default=True)
    ls_parser.add_argument('-f', '--no-sort', action='store_false', dest='sort')

    cd_parser = cli_subparsers.add_parser('cd')
    cd_parser.add_argument('path', nargs='?')

    script_args = script_parser.parse_args()
    url = urllib.parse.urlparse(script_args.url)

    zone = pathlib.PurePosixPath(url.path).parts[1]

    user = url.username
    if user is None:
        user = getpass.getuser()

    password = url.password
    if password is None:
        password = os.environ.get('IRODS_PASSWORD')
    if password is None:
        password = getpass.getpass()

    with irods.session.iRODSSession(
        host=url.hostname,
        port=url.port or DEFAULT_PORT,
        user=user,
        password=password,
        zone=zone
    ) as session:
        pwd = session.collections.get(pathlib.PurePosixPath(url.path))
        while True:
            input_args = shlex.split(input(prompt(user, pwd.path)))
            cli_args = cli_parser.parse_args(input_args)
            if cli_args.command == 'ls':
                header = None
                first = True
                targets = []
                for target in cli_args.targets:
                    try:
                        targets.append(session.collections.get(pathlib.PurePosixPath(pwd.path) / target))
                    except irods.exception.CollectionDoesNotExist as ex:
                        print('collection does not exist: {}'.format(target))
                        continue
                if not targets:
                    targets.append(pwd)
                for collection in targets:
                    if len(targets) > 1:
                        header = collection.path
                    ls(session, collection, classify=cli_args.classify, sort=cli_args.sort, header=header, first=first)
                    first = False


def ls (session, collection, classify=False, sort=False, header=None, first=False):
    if header is not None:
        if not first:
            print()
        print('{}:'.format(header))
    for each in iter_any(collection.subcollections, collection.data_objects, sort=sort):
        print(format_any(each, classify=classify))



def iter_any (collections, data_objects, sort=False):
    iter_ = itertools.chain(collections, data_objects)
    if sort:
        iter_ = sorted(iter_, key=lambda something: something.name)
    return iter_


def format_any (something, classify=False):
    if isinstance(something, irods.collection.iRODSCollection):
        return format_collection(something, classify=classify)
    elif isinstance(something, irods.data_object.iRODSDataObject):
        return format_data_object(something)


def format_collection (collection, classify=False):
    if classify:
        return '{}/'.format(collection.name)
    else:
        return collection.name


def format_data_object (data_object):
    return data_object.name


def prompt (user, path):
    return '{}@{}$ '.format(user, path)


if __name__ == '__main__':
    main()
