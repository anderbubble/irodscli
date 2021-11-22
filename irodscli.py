#!/usr/bin/env python3


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

    list_parser = cli_subparsers.add_parser('list', aliases=['ls', 'dir', 'coll'])
    list_parser.add_argument('targets', nargs='*', type=pathlib.PurePosixPath)
    list_parser.add_argument('-F', '--classify', action='store_true', default=False)
    list_parser.add_argument('--sort', action='store_true', default=True)
    list_parser.add_argument('-f', '--no-sort', action='store_false', dest='sort')
    list_parser.set_defaults(canonical_command='list')

    ccoll_parser = cli_subparsers.add_parser('ccoll', aliases=['cd'])
    ccoll_parser.add_argument('target', nargs='?')
    ccoll_parser.set_defaults(canonical_command='ccoll')

    pwcoll_parser = cli_subparsers.add_parser('pwcoll', aliases=['pwd'])
    pwcoll_parser.set_defaults(canonical_command='pwcoll')

    exit_parser = cli_subparsers.add_parser('exit')
    exit_parser.set_defaults(canonical_command='exit')

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
            pwcoll = previous_collection = initial_collection = session.collections.get(resolve(pathlib.PurePosixPath(url.path)))
        except irods.exception.CollectionDoesNotExist:
            print('{}: collection does not exist: {}'.format(script_parser.prog, url.path), file=sys.stderr)
            sys.exit()
        while True:
            try:
                input_args = shlex.split(input(prompt(user, pwcoll.path)))
            except EOFError:
                sys.stdout.write(os.linesep)
                sys.exit()
            try:
                cli_args = cli_parser.parse_args(input_args)
            except argparse.ArgumentError:
                print('unknown command: {}'.format(input_args[0]))
                continue
            if cli_args.canonical_command == 'list':
                list_(session, pwcoll, cli_args.targets, classify=cli_args.classify, sort=cli_args.sort)
            elif cli_args.canonical_command == 'ccoll':
                target_collection = ccoll(session, pwcoll, cli_args.target, initial_collection, previous_collection)
                if target_collection is not None:
                    pwcoll, previous_collection = target_collection, pwcoll
            elif cli_args.canonical_command == 'pwcoll':
                print(pwcoll.path)
            elif cli_args.canonical_command == 'exit':
                sys.exit()


def ccoll (session, pwcoll, target, initial, previous):
    if target is None:
        return initial
    elif target == '-':
        return previous
    else:
        try:
            target_collection = session.collections.get(resolve(pathlib.PurePosixPath(pwcoll.path) / target))
        except irods.exception.CollectionDoesNotExist:
            print('ccoll: collection does not exist: {}'.format(target), file=sys.stderr)
            return None
        else:
            return target_collection


def list_ (session, pwcoll, targets, classify=False, sort=False):
    header = None
    first = True
    target_collections = []
    for target in targets:
        try:
            target_collections.append(session.collections.get(resolve(pathlib.PurePosixPath(pwcoll.path) / target)))
        except irods.exception.CollectionDoesNotExist:
            print('list: collection does not exist: {}'.format(target), file=sys.stderr)
            continue
    if not targets:
        target_collections.append(pwcoll)
    for collection in target_collections:
        if len(targets) > 1:
            header = collection.path
        list_print_collection(session, collection, classify=classify, sort=sort, header=header, first=first)
        first = False


def list_print_collection (session, collection, classify=False, sort=False, header=None, first=False):
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
