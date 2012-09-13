#!/usr/bin/env python
# coding: utf-8
import sys
import urlparse

import libsmbclient as l

class SambaError(Exception):
    pass

_context = None

def _check_error():
    errno = l.get_errno()
    if errno:
        raise SambaError(l.strerror(errno))

def _hide_auth(smb_url):
    parsed = urlparse.urlparse(smb_url)
    return urlparse.urlunparse((
        parsed.scheme,
        parsed.netloc.split('@')[-1],
        parsed.path,
        parsed.params,
        parsed.query,
        parsed.fragment,
    ))

def set_auth_func(auth_func):
    global _context
    l.smbc_init(l.AUTHFUNC(l.py_auth_func), 1)
    _context = l.smbc_new_context()
    l.smbc_init_context(_context)


def _smbobj_from_dirent(base_url, dirent):
    t = dirent.contents.smbc_type
    if t == l.FILE_SHARE:
        cls = FileShareObj
    elif t == l.DIR:
        cls = DirObj
    elif t == l.FILE:
        cls = FileObj
    else:
        cls = SmbObj
    return cls(
        base_url, t,
        dirent.contents.comment,
        dirent.contents.name
    )

class SmbObj(object):
    __slots__ = ('type', 'comment', 'name', 'base_url')
    def __init__(self, base_url, type_, comment, name):
        self.base_url = base_url
        self.type = type_
        self.comment = comment
        self.name = name

    def __repr__(self):
        if type(self) is SmbObj:
            cls = 'SmbObj %s' % l.TYPE_STRINGS[self.type]
        else:
            cls = type(self).__name__
        return '<%s on %s: %s>' % (
            cls,
            _hide_auth(self.base_url),
            self.name
        )

    @property
    def url(self):
        return self.base_url + self.name

class FileShareObj(SmbObj):
    pass


class DirObj(SmbObj):
    pass


class _smbfile(object):

    __slots__ = ('fd')

    def __init__(self, fd):
        self.fd = fd

    def fileno(self):
        return self.fd

    def read(self, count=4096 * 1024):
        t = l.create_string_buffer(count)
        import time
        before = time.time()
        bytes_written = l.smbc_read(self.fd, t, count)
        print >> sys.stderr, time.time() - before, bytes_written
        if bytes_written < 0:
            _check_error()
        return t.value


class FileObj(SmbObj):
    def open(self, mode='r'):
        modes = {
            'r': l.O_RDONLY,
            'w': l.O_WRONLY,
            'rw': l.O_RDWR,
        }
        print self.url
        fd = l.smbc_open(self.url, modes[mode], 0644)
        if fd < 0:
            _check_error()
        return _smbfile(fd)


def listdir(smb_url):
    dir_ = l.smbc_opendir(smb_url)
    if dir_ < 0:
        _check_error()
    while True:
        dirent = l.smbc_readdir(dir_)
        if not dirent:
            _check_error()
            break
        obj_ = _smbobj_from_dirent(smb_url, dirent)
        if obj_.type == l.DIR and obj_.name in ('.', '..'):
            continue
        yield obj_
            

# set_auth_func(l.py_auth_func)

if __name__ == '__main__':
    l.smbc_init(l.auth_func, 1)
    l.smbc_init_context(l.smbc_new_context())
    for i in listdir(sys.argv[1]):
        if isinstance(i, FileObj):
            f = i.open()
            import shutil
            import sys
            shutil.copyfileobj(f, sys.stdout)
