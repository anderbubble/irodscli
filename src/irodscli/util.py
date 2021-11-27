import irods.collection
import irods.data_object
import irods.exception
import itertools
import pathlib


def resolve_path (path, pwd=None):
    path = pathlib.PurePosixPath(path)
    if pwd:
        if isinstance(pwd, (irods.collection.iRODSCollection, irods.data_object.iRODSDataObject)):
            pwd = pwd.path
        path = pathlib.PurePosixPath(pwd) / path
    resolved_path = pathlib.PurePosixPath(path.parts[0])
    for part in path.parts[1:]:
        if part == '..':
            resolved_path = resolved_path.parent
        else:
            resolved_path = resolved_path / part
    return str(resolved_path)


def resolve_irods (session, pwd, target):
    if isinstance(target, (irods.data_object.iRODSDataObject, irods.collection.iRODSCollection)):
        return target
    try:
        return resolve_collection(session, pwd, target)
    except irods.exception.CollectionDoesNotExist:
        return resolve_data_object(session, pwd, target)


def resolve_collection (session, pwd, target):
    return session.collections.get(resolve_path(target, pwd))


def resolve_data_object (session, pwd, target):
    return session.data_objects.get(resolve_path(target, pwd))


def chain (*args, sort=False):
    iter_ = itertools.chain(*args, data_objects)
    if sort:
        iter_ = sorted(iter_, key=lambda something: something.name)
    return iter_
