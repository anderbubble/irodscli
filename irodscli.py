#!/usr/bin/env python3

# TODO
# - handle ls of data object
# - handle ls of glob
# - rstrip /, restrict to collection
# - implement ls -l
# - readline


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

    cli_parser = argparse.ArgumentParser(prog=None, exit_on_error=False)
    cli_subparsers = cli_parser.add_subparsers(dest='command')

    ls_parser = cli_subparsers.add_parser('ls')
    ls_parser.add_argument('targets', nargs='*', type=pathlib.PurePosixPath)
    ls_parser.add_argument('-F', '--classify', action='store_true', default=False)
    ls_parser.add_argument('--sort', action='store_true', default=True)
    ls_parser.add_argument('-f', '--no-sort', action='store_false', dest='sort')

    cd_parser = cli_subparsers.add_parser('cd')
    cd_parser.add_argument('target', nargs='?')

    pwd_parser = cli_subparsers.add_parser('pwd')

    exit_parser = cli_subparsers.add_parser('exit')

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
        try:
            pwd = previous_collection = initial_collection = session.collections.get(resolve(pathlib.PurePosixPath(url.path)))
        except irods.exception.CollectionDoesNotExist:
            print('{}: collection does not exist: {}'.format(script_parser.prog, url.path), file=sys.stderr)
            sys.exit()
        while True:
            try:
                input_args = shlex.split(input(prompt(user, pwd.path)))
            except EOFError:
                sys.stdout.write(os.linesep)
                sys.exit()
            try:
                cli_args = cli_parser.parse_args(input_args)
            except argparse.ArgumentError:
                print('unknown command: {}'.format(input_args[0]))
                continue
            if cli_args.command == 'ls':
                ls(session, pwd, cli_args.targets, classify=cli_args.classify, sort=cli_args.sort)
            elif cli_args.command == 'cd':
                target_collection = cd(session, pwd, cli_args.target, initial_collection, previous_collection)
                if target_collection is not None:
                    pwd, previous_collection = target_collection, pwd
            elif cli_args.command == 'pwd':
                print(pwd.path)
            elif cli_args.command == 'exit':
                sys.exit()


def cd (session, pwd, target, initial, previous):
    if target is None:
        return initial
    elif target == '-':
        return previous
    else:
        try:
            target_collection = session.collections.get(resolve(pathlib.PurePosixPath(pwd.path) / target))
        except irods.exception.CollectionDoesNotExist:
            print('cd: collection does not exist: {}'.format(target), file=sys.stderr)
            return None
        else:
            return target_collection


def ls (session, pwd, targets, classify=False, sort=False):
    header = None
    first = True
    target_collections = []
    for target in targets:
        try:
            target_collections.append(session.collections.get(resolve(pathlib.PurePosixPath(pwd.path) / target)))
        except irods.exception.CollectionDoesNotExist:
            print('ls: collection does not exist: {}'.format(target), file=sys.stderr)
            continue
    if not targets:
        target_collections.append(pwd)
    for collection in target_collections:
        if len(targets) > 1:
            header = collection.path
        ls_print_collection(session, collection, classify=classify, sort=sort, header=header, first=first)
        first = False


def ls_print_collection (session, collection, classify=False, sort=False, header=None, first=False):
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


def resolve (path):
    resolved_path = pathlib.PurePosixPath(path.parts[0])
    for part in path.parts[1:]:
        if part == '..':
            resolved_path = resolved_path.parent
        else:
            resolved_path = resolved_path / part
    return resolved_path


if __name__ == '__main__':
    main()
