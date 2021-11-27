import argparse
import getpass
import irods.collection
import irods.data_object
import irods.exception
import irods.session
import os
import pathlib
import shlex
import sys
import urllib.parse

import irodscli.parsers
import irodscli.util


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
            pwd = prevd = startd = session.collections.get(irodscli.util.resolve_path(url.path))
        except irods.exception.CollectionDoesNotExist:
            print('{}: collection does not exist: {}'.format(irodscli.parsers.script_parser.prog, url.path), file=sys.stderr)
            sys.exit(-1)
        if hasattr(script_args, 'subcommand'):
            do_subcommand(session, pwd, script_args)
        else:
            cli_parser = irodscli.parsers.cli_parser()
            while True:
                try:
                    input_args = shlex.split(input(prompt(user, pwd.path)))
                except EOFError:
                    sys.stderr.write(os.linesep)
                    sys.exit()
                try:
                    cli_args = cli_parser.parse_args(input_args)
                except argparse.ArgumentError:
                    print('unknown command: {}'.format(input_args[0]))
                    continue
                except SystemExit:
                    continue
                if not hasattr(cli_args, 'subcommand'):
                    continue
                new_pwd = do_subcommand(session, pwd, cli_args)
                if new_pwd is not None:
                    pwd, prevd = new_pwd, pwd


def do_subcommand (session, pwd, args):
    new_pwd = None

    if args.subcommand == 'ls':
        ls(session, pwd, args.targets, classify=args.classify, sort=args.sort)
    elif args.subcommand == 'cd':
        new_pwd = cd(session, pwd, args.target, startd, prevd)
    elif args.subcommand == 'pwd':
        print(pwd.path)
    elif args.subcommand == 'get':
        get(session, pwd, args.remote_path, args.local_path, force=args.force, verbose=args.force)
    elif args.subcommand == 'put':
        put(session, pwd, args.local_path, args.remote_path, verbose=args.verbose)
    elif args.subcommand == 'sysmeta':
        sysmeta(session, pwd, args.targets)
    elif args.subcommand == 'chksum':
        chksum(session, pwd, args.target)
    elif args.subcommand == 'rm':
        rm(session, pwd, args.target, force=args.force)
    elif args.subcommand == 'mkdir':
        mkdir(session, pwd, args.target, verbose=args.verbose)
    elif args.subcommand == 'rmdir':
        rmdir(session, pwd, args.target, verbose=args.verbose)
    elif args.subcommand == 'exit':
        sys.exit()

    return new_pwd


def mkdir (session, pwd, target, verbose=False):
    collection = session.collections.create(irodscli.util.resolve_path(target, pwd))
    if verbose:
        print(collection.path, file=sys.stderr)


def rmdir (session, pwd, target, force=False, verbose=False):
    collection = irodscli.util.resolve_collection(session, pwd, target)
    try:
        collection.remove(recurse=recursive, force=force)
    except irods.exception.CAT_COLLECTION_NOT_EMPTY:
        print('cannot remove {}: not empty'.format(collection.path))
    if verbose:
        print(collection.path, file=sys.stderr)


def rm (session, pwd, target, force=False):
    irodscli.util.resolve_data_object(session, pwd, target).unlink(force=force)


def chksum (session, pwd, target):
    data_object = irodscli.util.resolve_data_object(session, pwd, target)
    chksum = data_object.chksum()
    print(target, chksum)


def get (session, pwd, remote_path, local_path, force=False, verbose=False):
    options = {}
    if force:
        options[irods.keywords.FORCE_FLAG_KW] = ''
    try:
        data_object = session.data_objects.get(irodscli.util.resolve_path(remote_path, pwd), local_path, **options)
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
    try:
        session.data_objects.put(local_path, irodscli.util.resolve_path(remote_path, pwd))
    except irods.exception.OVERWRITE_WITHOUT_FORCE_FLAG:
        print('{} already exists. Use --force to overwrite.'.format(remote_path), file=sys.stderr)
    else:
        if verbose:
            print('{} -> {}'.format(local_path, remote_path), file=sys.stderr)


def sysmeta (session, pwd, target_paths):
    targets = []
    for path in target_paths:
        targets.append(irodscli.util.resolve_irods(session, pwd, path))
    for target in targets:
        sysmeta_print_any(target)


def cd (session, pwd, target, initial, prevd):
    if target is None:
        return initial
    elif target == '-':
        return prevd
    else:
        try:
            targetd = session.collections.get(irodscli.util.resolve_path(target, pwd))
        except irods.exception.CollectionDoesNotExist:
            print('ccoll: collection does not exist: {}'.format(target), file=sys.stderr)
            return None
        else:
            return targetd


def ls (session, pwd, target_paths, classify=False, sort=False):
    header = None
    first = True
    target_colls = []
    target_objects = []
    target_object_paths = []
    for path in target_paths:
        try:
            target_colls.append(irodscli.util.resolve_collection(session, pwd, path))
        except irods.exception.CollectionDoesNotExist:
            try:
                target_objects.append(irodscli.util.resolve_data_object(session, pwd, path))
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
    for each in irodscli.util.chain(collection.subcollections, collection.data_objects, sort=sort):
        print(format_any(each, classify=classify))


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
    if sys.stdin.isatty():
        return '{}@{}$ '.format(user, path)
    else:
        return ''
