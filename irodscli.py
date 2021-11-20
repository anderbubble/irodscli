#!/usr/bin/env python3

# TODO
# - combine host, zone, user, port, and path to a url


import argparse
import getpass
import irods.session
import os
#import urlparse


def main ():
    parser = argparse.ArgumentParser()
    parser.add_argument('host')
    parser.add_argument('zone')
    parser.add_argument('--port', default=1247)
    parser.add_argument('--user', default=getpass.getuser())
    args = parser.parse_args()
    password = os.environ.get('IRODS_PASSWORD')
    if password is None:
        password = getpass.getpass()
    root = '/{}'.format(args.zone)
    with irods.session.iRODSSession(
        host=args.host,
        port=args.port,
        user=args.user,
        password=password,
        zone=args.zone
    ) as session:
        workdir = [root, 'home', args.user]
        coll = session.collections.get('/'.join(workdir))
        print(coll.path)
        for subcoll in coll.subcollections:
            print(subcoll)
        for obj in coll.data_objects:
            print(obj)


if __name__ == '__main__':
    main()
