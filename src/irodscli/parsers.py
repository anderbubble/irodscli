import argparse


def script_parser ():
    script_parser = argparse.ArgumentParser(parents=[cli_parser()])
    script_parser.add_argument('--url')
    return script_parser


def cli_parser ():
    cli_parser = argparse.ArgumentParser(prog=None, exit_on_error=False, add_help=False)
    cli_subparsers = cli_parser.add_subparsers(dest='subcommand_alias')

    chksum_parser = cli_subparsers.add_parser('chksum', aliases=['ichksum'])
    chksum_parser.add_argument('target')
    chksum_parser.set_defaults(subcommand='chksum')

    rm_parser = cli_subparsers.add_parser('rm', aliases=['irm'])
    rm_parser.add_argument('target')
    rm_parser.add_argument('--force', action='store_true')
    rm_parser.set_defaults(subcommand='rm', force=False)

    ls_parser = cli_subparsers.add_parser('ls', aliases=['ils'])
    ls_parser.add_argument('targets', nargs='*')
    ls_parser.add_argument('-F', '--classify', action='store_true', default=False)
    ls_parser.add_argument('--sort', action='store_true', default=True)
    ls_parser.add_argument('-f', '--no-sort', action='store_false', dest='sort')
    ls_parser.set_defaults(subcommand='ls')

    put_parser = cli_subparsers.add_parser('put', aliases=['iput'])
    put_parser.add_argument('local_path')
    put_parser.add_argument('remote_path')
    put_parser.add_argument('--verbose', action='store_true')
    put_parser.set_defaults(subcommand='put', verbose=False)

    get_parser = cli_subparsers.add_parser('get', aliases=['iget'])
    get_parser.add_argument('remote_path')
    get_parser.add_argument('local_path')
    get_parser.add_argument('--force', action='store_true')
    get_parser.add_argument('--verbose', action='store_true')
    get_parser.set_defaults(subcommand='get', force=False, verbose=False)

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

    mkdir_parser = cli_subparsers.add_parser('mkdir', aliases=['imkdir'])
    mkdir_parser.add_argument('target')
    mkdir_parser.add_argument('--verbose', action='store_true')
    mkdir_parser.set_defaults(subcommand='mkdir', verbose=False)

    rmdir_parser = cli_subparsers.add_parser('rmdir', aliases=['irmdir'])
    rmdir_parser.add_argument('target')
    rmdir_parser.add_argument('--verbose', action='store_true')
    rmdir_parser.add_argument('--recursive', action='store_true')
    rmdir_parser.add_argument('--force', action='store_true')
    rmdir_parser.set_defaults(subcommand='rmdir', verbose=False, recursive=False, force=False)

    return cli_parser
