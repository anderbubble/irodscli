import argparse


def script_parser ():
    script_parser = argparse.ArgumentParser()
    script_parser.add_argument('--url')
    cli_subparsers = _add_cli_subparsers(script_parser)
    return script_parser


def cli_parser ():
    cli_parser = argparse.ArgumentParser(prog=None, exit_on_error=False)
    cli_subparsers = _add_cli_subparsers(cli_parser)
    return cli_parser


def _add_cli_subparsers (parser):
    cli_subparsers = parser.add_subparsers(dest='subcommand_alias')
    _add_ls_parser(cli_subparsers)
    _add_cd_parser(cli_subparsers)
    _add_sysmeta_parser(cli_subparsers)
    _add_put_parser(cli_subparsers)
    _add_get_parser(cli_subparsers)
    _add_chksum_parser(cli_subparsers)
    _add_rm_parser(cli_subparsers)
    _add_exit_parser(cli_subparsers)
    return cli_subparsers


def _add_chksum_parser (subparsers):
    chksum_parser = subparsers.add_parser('chksum', aliases=['ichksum'])
    chksum_parser.add_argument('target')
    chksum_parser.set_defaults(subcommand='chksum')
    return chksum_parser


def _add_rm_parser (subparsers):
    rm_parser = subparsers.add_parser('rm', aliases=['irm'])
    rm_parser.add_argument('target')
    rm_parser.add_argument('--force', action='store_true')
    rm_parser.set_defaults(subcommand='rm', force=False)
    return rm_parser


def _add_ls_parser (subparsers):
    ls_parser = subparsers.add_parser('ls', aliases=['ils'])
    ls_parser.add_argument('targets', nargs='*')
    ls_parser.add_argument('-F', '--classify', action='store_true', default=False)
    ls_parser.add_argument('--sort', action='store_true', default=True)
    ls_parser.add_argument('-f', '--no-sort', action='store_false', dest='sort')
    ls_parser.set_defaults(subcommand='ls')
    return ls_parser


def _add_put_parser (subparsers):
    put_parser = subparsers.add_parser('put', aliases=['iput'])
    put_parser.add_argument('local_path')
    put_parser.add_argument('remote_path')
    put_parser.add_argument('--verbose', action='store_true')
    put_parser.set_defaults(subcommand='put', verbose=False)


def _add_get_parser (subparsers):
    get_parser = subparsers.add_parser('get', aliases=['iget'])
    get_parser.add_argument('remote_path')
    get_parser.add_argument('local_path')
    get_parser.add_argument('--force', action='store_true')
    get_parser.add_argument('--verbose', action='store_true')
    get_parser.set_defaults(subcommand='get', force=False, verbose=False)


def _add_cd_parser (subparsers):
    cd_parser = subparsers.add_parser('cd', aliases=['icd'])
    cd_parser.add_argument('target', nargs='?')
    cd_parser.set_defaults(subcommand='cd')
    return cd_parser


def _add_pwd_parser (subparsers):
    pwd_parser = subparsers.add_parser('pwd', aliases=['ipwd'])
    pwd_parser.set_defaults(subcommand='pwd')
    return pwd_parser


def _add_sysmeta_parser (subparsers):
    sysmeta_parser = subparsers.add_parser('sysmeta', aliases=['isysmeta', 'stat'])
    sysmeta_parser.add_argument('targets', nargs='*')
    sysmeta_parser.set_defaults(subcommand='sysmeta')
    return sysmeta_parser


def _add_exit_parser (subparsers):
    exit_parser = subparsers.add_parser('exit', aliases=['iexit'])
    exit_parser.set_defaults(subcommand='exit')
    return exit_parser
