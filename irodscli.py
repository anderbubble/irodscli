#!/usr/bin/env python3

# TODO
# - format collection and data
# - read path from url


import argparse
import getpass
import irods.session
import os
import pathlib
import urllib.parse


DEFAULT_PORT = 1247


def main ():
    parser = argparse.ArgumentParser()
    parser.add_argument('url')

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

    root = '/{}'.format(zone)
    with irods.session.iRODSSession(
        host=url.hostname,
        port=url.port or DEFAULT_PORT,
        user=user,
        password=password,
        zone=zone
    ) as session:
        workdir = [root, 'home', user]
        coll = session.collections.get('/'.join(workdir))
        print(coll.path)
        for subcoll in coll.subcollections:
            print(subcoll)
        for obj in coll.data_objects:
            print(obj)


if __name__ == '__main__':
    main()
