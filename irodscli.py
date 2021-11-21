#!/usr/bin/env python3

# - move listing to a subparser ls command


import argparse
import getpass
import irods.collection
import irods.data_object
import irods.session
import itertools
import os
import pathlib
import urllib.parse


DEFAULT_PORT = 1247


def main ():
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('--classify', action='store_true', default=False)
    parser.add_argument('--sort', action='store_true', default=True)
    parser.add_argument('--no-sort', action='store_false', dest='sort')

    args = parser.parse_args()
    url = urllib.parse.urlparse(args.url)

    zone = pathlib.Path(url.path).parts[1]
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
        coll = session.collections.get(url.path)
        for each in iter_any(coll.subcollections, coll.data_objects, sort=args.sort):
            print(format_any(each, classify=args.classify))

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


if __name__ == '__main__':
    main()
