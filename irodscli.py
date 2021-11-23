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
    cli_subparsers = cli_parser.add_subparsers(dest='subcommand_alias')

    ls_parser = cli_subparsers.add_parser('ls', aliases=['ils'])
    ls_parser.add_argument('targets', nargs='*')
    ls_parser.add_argument('-F', '--classify', action='store_true', default=False)
    ls_parser.add_argument('--sort', action='store_true', default=True)
    ls_parser.add_argument('-f', '--no-sort', action='store_false', dest='sort')
    ls_parser.set_defaults(subcommand='ls')

    cd_parser = cli_subparsers.add_parser('cd', aliases=['icd'])
    cd_parser.add_argument('target', nargs='?')
    cd_parser.set_defaults(subcommand='cd')

    pwd_parser = cli_subparsers.add_parser('pwd', aliases=['ipwd'])
    pwd_parser.set_defaults(subcommand='pwd')

    sysmeta_parser = cli_subparsers.add_parser('sysmeta', aliases=['isysmeta', 'stat'])
    sysmeta_parser.add_argument('targets', nargs='*')
    sysmeta_parser.set_defaults(subcommand='sysmeta')

    exit_parser = cli_subparsers.add_parser('exit', aliases=['iexit'])
    exit_parser.set_defaults(subcommand='exit')

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
            pwcoll = previous_collection = initial_collection = session.collections.get(str(resolve(pathlib.PurePosixPath(url.path))))
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
            if cli_args.subcommand == 'ls':
                ls(session, pwcoll, cli_args.targets, classify=cli_args.classify, sort=cli_args.sort)
            elif cli_args.subcommand == 'cd':
                target_collection = cd(session, pwcoll, cli_args.target, initial_collection, previous_collection)
                if target_collection is not None:
                    pwcoll, previous_collection = target_collection, pwcoll
            elif cli_args.subcommand == 'pwd':
                print(pwcoll.path)
            elif cli_args.subcommand == 'exit':
                sys.exit()
            elif cli_args.subcommand == 'sysmeta':
                sysmeta(session, pwcoll, cli_args.targets)


def sysmeta (session, pwcoll, target_paths):
    targets = []
    for path in target_paths:
        targets.append(path_to_collection_or_object(session, pwcoll, path))
    for target in targets:
        sysmeta_print_any(target)


def cd (session, pwcoll, target, initial, previous):
    if target is None:
        return initial
    elif target == '-':
        return previous
    else:
        try:
            target_collection = session.collections.get(str(resolve(pathlib.PurePosixPath(pwcoll.path) / target)))
        except irods.exception.CollectionDoesNotExist:
            print('ccoll: collection does not exist: {}'.format(target), file=sys.stderr)
            return None
        else:
            return target_collection


def path_to_collection_or_object (session, pwcoll, path):
    try:
        return path_to_collection(session, pwcoll, path)
    except irods.exception.CollectionDoesNotExist:
        return path_to_data_object(session, pwcoll, path)


def path_to_collection (session, pwcoll, path):
    return session.collections.get(str(resolve(pathlib.PurePosixPath(pwcoll.path) / path)))


def path_to_data_object (session, pwcoll, path):
    return session.data_objects.get(str(resolve(pathlib.PurePosixPath(pwcoll.path) / path)))


def ls (session, pwcoll, target_paths, classify=False, sort=False):
    header = None
    first = True
    target_colls = []
    target_objects = []
    target_object_paths = []
    for path in target_paths:
        try:
            target_colls.append(path_to_collection(session, pwcoll, path))
        except irods.exception.CollectionDoesNotExist:
            try:
                target_objects.append(path_to_data_object(session, pwcoll, path))
            except irods.exception.DataObjectDoesNotExist:
                print('list: collection or data object does not exist: {}'.format(path), file=sys.stderr)
                continue
            else:
                target_object_paths.append(path)
    if not target_paths:
        target_colls.append(pwcoll)
    for data_object, data_object_path in zip(target_objects, target_object_paths):
        print(data_object_path)
    for coll in target_colls:
        if len(target_paths) > 1:
            header = coll.path
        ls_print_collection(session, coll, classify=classify, sort=sort, header=header, first=first)
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


def sysmeta_print_any (something, classify=False):
    if isinstance(something, irods.collection.iRODSCollection):
        sysmeta_print_collection(something)
    elif isinstance(something, irods.data_object.iRODSDataObject):
        return sysmeta_print_data_object(something)


def sysmeta_print_collection (collection):
    print('id: {}'.format(collection.id))
    print('name: {}'.format(collection.name))
    print('path: {}'.format(collection.path))


def sysmeta_print_data_object (data_object):
    print('id: {}'.format(data_object.id))
    print(dir(data_object))


def format_collection (collection, classify=False):
    if classify:
        return '{}/'.format(collection.name)
    else:
        return collection.name


def format_data_object (data_object):
    return data_object.name


def prompt (user, path):
    if sys.stdin.isatty():
        return '{}@{}$ '.format(user, path)
    else:
        return ''


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
