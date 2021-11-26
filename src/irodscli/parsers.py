import argparse


def script_parser ():
    parser = argparse.ArgumentParser(parents=[cli_parser()])
    parser.add_argument('--url')
    return parser


def cli_parser ():
    parser = argparse.ArgumentParser(prog=None, exit_on_error=False, add_help=False)
    subparsers = parser.add_subparsers(dest='subcommand_alias')

    chksum = subparsers.add_parser('chksum', aliases=['ichksum'])
    chksum.add_argument('target')
    chksum.set_defaults(subcommand='chksum')

    rm = subparsers.add_parser('rm', aliases=['irm'])
    rm.add_argument('target')
    rm.add_argument('--force', action='store_true')
    rm.set_defaults(subcommand='rm', force=False)

    ls = subparsers.add_parser('ls', aliases=['ils'])
    ls.add_argument('targets', nargs='*')
    ls.add_argument('-F', '--classify', action='store_true', default=False)
    ls.add_argument('--sort', action='store_true', default=True)
    ls.add_argument('-f', '--no-sort', action='store_false', dest='sort')
    ls.set_defaults(subcommand='ls')

    put = subparsers.add_parser('put', aliases=['iput'])
    put.add_argument('local_path')
    put.add_argument('remote_path')
    put.add_argument('--verbose', action='store_true')
    put.set_defaults(subcommand='put', verbose=False)

    get = subparsers.add_parser('get', aliases=['iget'])
    get.add_argument('remote_path')
    get.add_argument('local_path')
    get.add_argument('--force', action='store_true')
    get.add_argument('--verbose', action='store_true')
    get.set_defaults(subcommand='get', force=False, verbose=False)

    cd = subparsers.add_parser('cd', aliases=['icd'])
    cd.add_argument('target', nargs='?')
    cd.set_defaults(subcommand='cd')

    pwd = subparsers.add_parser('pwd', aliases=['ipwd'])
    pwd.set_defaults(subcommand='pwd')

    sysmeta = subparsers.add_parser('sysmeta', aliases=['isysmeta', 'stat'])
    sysmeta.add_argument('targets', nargs='*')
    sysmeta.set_defaults(subcommand='sysmeta')

    exit = subparsers.add_parser('exit', aliases=['iexit'])
    exit.set_defaults(subcommand='exit')

    mkdir = subparsers.add_parser('mkdir', aliases=['imkdir'])
    mkdir.add_argument('target')
    mkdir.add_argument('--verbose', action='store_true')
    mkdir.set_defaults(subcommand='mkdir', verbose=False)

    rmdir = subparsers.add_parser('rmdir', aliases=['irmdir'])
    rmdir.add_argument('target')
    rmdir.add_argument('--verbose', action='store_true')
    rmdir.add_argument('--recursive', action='store_true')
    rmdir.add_argument('--force', action='store_true')
    rmdir.set_defaults(subcommand='rmdir', verbose=False, recursive=False, force=False)

    return parser
