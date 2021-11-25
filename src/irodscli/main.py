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

import irodscli.parsers


DEFAULT_PORT = 1247
REPLICA_STATUS = {'0': 'stale', '1': 'good', '2': 'intermediate'}


def main ():
    script_args = irodscli.parsers.script_parser().parse_args()
    url = script_args.url
    if url is None:
        try:
            url = os.environ['IRODS_URL']
        except KeyError:
            print('--url or IRODS_URL required', file=sys.stderr)
            sys.exit(-1)
    url = urllib.parse.urlparse(url)

    zone = pathlib.PurePosixPath(url.path).parts[1]

    user = url.username
    if user is None:
        user = getpass.getuser()

    password = url.password
    if password is None:
        password = os.environ.get('IRODS_PASSWORD') or None
    if password is None:
        try:
            password = getpass.getpass()
        except KeyboardInterrupt:
            sys.stderr.write(os.linesep)
            sys.exit(-1)

    with irods.session.iRODSSession(
        host=url.hostname,
        port=url.port or DEFAULT_PORT,
        user=user,
        password=password,
        zone=zone
    ) as session:
        try:
            pwd = prevd = startd = session.collections.get(str(resolve(pathlib.PurePosixPath(url.path))))
        except irods.exception.CollectionDoesNotExist:
            print('{}: collection does not exist: {}'.format(script_parser.prog, url.path), file=sys.stderr)
            sys.exit(-1)
        while True:
            if hasattr(script_args, 'subcommand'):
                cli_args = script_args
            else:
                try:
                    input_args = shlex.split(input(prompt(user, pwd.path)))
                except EOFError:
                    sys.stderr.write(os.linesep)
                    sys.exit()
                try:
                    cli_args = irodscli.parsers.cli_parser().parse_args(input_args)
                except argparse.ArgumentError:
                    print('unknown command: {}'.format(input_args[0]))
                    continue
                if not hasattr(cli_args, 'subcommand'):
                    continue
            if cli_args.subcommand == 'ls':
                ls(session, pwd, cli_args.targets, classify=cli_args.classify, sort=cli_args.sort)
            elif cli_args.subcommand == 'cd':
                targetd = cd(session, pwd, cli_args.target, startd, prevd)
                if targetd is not None:
                    pwd, prevd = targetd, pwd
            elif cli_args.subcommand == 'pwd':
                print(pwd.path)
            elif cli_args.subcommand == 'get':
                get(session, pwd, cli_args.remote_path, cli_args.local_path, force=cli_args.force, verbose=cli_args.force)
            elif cli_args.subcommand == 'put':
                put(session, pwd, cli_args.local_path, cli_args.remote_path, verbose=cli_args.verbose)
            elif cli_args.subcommand == 'exit':
                sys.exit()
            elif cli_args.subcommand == 'sysmeta':
                sysmeta(session, pwd, cli_args.targets)
            if hasattr(script_args, 'subcommand'):
                break


def get (session, pwd, remote_path, local_path, force=False, verbose=False):
    options = {}
    if force:
        options[irods.keywords.FORCE_FLAG_KW] = ''
    full_remote_path = str(pathlib.PurePosixPath(pwd.path) / remote_path)
    try:
        data_object = session.data_objects.get(full_remote_path, local_path, **options)
    except irods.exception.OVERWRITE_WITHOUT_FORCE_FLAG:
        print('{} already exists. Use --force to overwrite.'.format(local_path), file=sys.stderr)
    else:
        if verbose:
            print('{} -> {}'.format(data_object.path, remote_path), file=sys.stderr)


def put (session, pwd, local_path, remote_path, force=False, verbose=False):
    options = {}
    # BUG: python-irodsclient will overwrite without force
    if force:
        options[irods.keywords.FORCE_FLAG_KW] = ''
    full_remote_path = str(pathlib.PurePosixPath(pwd.path) / remote_path)
    try:
        session.data_objects.put(local_path, full_remote_path)
    except irods.exception.OVERWRITE_WITHOUT_FORCE_FLAG:
        print('{} already exists. Use --force to overwrite.'.format(remote_path), file=sys.stderr)
    else:
        if verbose:
            print('{} -> {}'.format(local_path, remote_path), file=sys.stderr)


def sysmeta (session, pwd, target_paths):
    targets = []
    for path in target_paths:
        targets.append(path_to_collection_or_object(session, pwd, path))
    for target in targets:
        sysmeta_print_any(target)


def cd (session, pwd, target, initial, prevd):
    if target is None:
        return initial
    elif target == '-':
        return prevd
    else:
        try:
            targetd = session.collections.get(str(resolve(pathlib.PurePosixPath(pwd.path) / target)))
        except irods.exception.CollectionDoesNotExist:
            print('ccoll: collection does not exist: {}'.format(target), file=sys.stderr)
            return None
        else:
            return targetd


def path_to_collection_or_object (session, pwd, path):
    if isinstance(path, (irods.data_object.iRODSDataObject, irods.collection.iRODSCollection)):
        return path
    try:
        return path_to_collection(session, pwd, path)
    except irods.exception.CollectionDoesNotExist:
        return path_to_data_object(session, pwd, path)


def path_to_collection (session, pwd, path):
    return session.collections.get(str(resolve(pathlib.PurePosixPath(pwd.path) / path)))


def path_to_data_object (session, pwd, path):
    return session.data_objects.get(str(resolve(pathlib.PurePosixPath(pwd.path) / path)))


def ls (session, pwd, target_paths, classify=False, sort=False):
    header = None
    first = True
    target_colls = []
    target_objects = []
    target_object_paths = []
    for path in target_paths:
        try:
            target_colls.append(path_to_collection(session, pwd, path))
        except irods.exception.CollectionDoesNotExist:
            try:
                target_objects.append(path_to_data_object(session, pwd, path))
            except irods.exception.DataObjectDoesNotExist:
                print('list: collection or data object does not exist: {}'.format(path), file=sys.stderr)
                continue
            else:
                target_object_paths.append(path)
    if not target_paths:
        target_colls.append(pwd)
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
    print('subcollections: {}'.format(len(collection.subcollections)))


def sysmeta_print_data_object (data_object):
    print('path:', data_object.path)
    print('name:', data_object.name)
    print('id:', data_object.id)
    print('owner: {}@{}'.format(data_object.owner_name, data_object.owner_zone))
    print('size:', data_object.size)
    print('checksum:', data_object.checksum)
    print('collection:', data_object.collection_id)
    print('comments:', data_object.comments)
    print('create:', data_object.create_time)
    print('modify:', data_object.modify_time)
    print('expiry:', data_object.expiry)
    print('replica:', data_object.replica_number)
    print('replica status: {} ({})'.format(data_object.replica_status, REPLICA_STATUS.get(data_object.replica_status, '?')))
    print('replicas:', len(data_object.replicas))
    print('resource hierarchy:', data_object.resc_hier)
    print('resource: {} ({})'.format(data_object.resc_id, data_object.resource_name))
    print('status:', data_object.status)
    print('type:', data_object.type)
    print('version:', data_object.version)


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
