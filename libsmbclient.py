#!/usr/bin/env python2

import getpass

from ctypes import *
from ctypes.util import find_library

import sys

smbclient = CDLL(find_library('smbclient'), use_errno=True)
libc = CDLL(find_library('c'), use_errno=True)

## Libc
perror = libc.perror
perror.argtypes = [c_char_p]
perror.restype = None

strerror = libc.strerror
strerror.argtypes = [c_int]
strerror.restype = c_char_p

strcpy = libc.strcpy
strcpy.argtypes = [c_char_p, c_char_p]
strcpy.restype = c_char_p


## SMBCLIENT
s = smbclient

# Errors
EACCES = 4
EINVAL = 14
ENOENT = 22
ENOMEM = 25
ENOTDIR = 28
EPERM = 32
ENODEV = 21

class SMBCCTX(Structure):
    _fields_ = []

SMBCCTX_p = POINTER(SMBCCTX)

smbc_new_context = s.smbc_new_context
smbc_new_context.argtypes = None
smbc_new_context.restype = SMBCCTX_p

smbc_init_context = s.smbc_init_context
smbc_init_context.argeypes = [SMBCCTX_p]
smbc_init_context.restype = SMBCCTX_p

c_char_pp = POINTER(c_char_p)

AUTHFUNC = CFUNCTYPE(None, c_char_p, c_char_p,
                     POINTER(c_char), c_int,
                     POINTER(c_char), c_int,
                     POINTER(c_char), c_int,
                     )

smbc_init = s.smbc_init
smbc_init.argtypes = [AUTHFUNC, c_int]
smbc_init.restype = c_int


def py_auth_func(source, share, workgroup_p, workgroup_p_len,
                 user_p, user_p_len, password_p, password_p_len):
    strcpy(user_p, raw_input('Username: ')[:user_p_len])
    strcpy(password_p, getpass.getpass('Password: ')[:user_p_len])
    return

auth_func = AUTHFUNC(py_auth_func)

mode_t = c_uint32

# flags
O_RDONLY = 00
O_WRONLY = 01
O_RDWR = 02

smbc_bool = c_int

smbc_open = s.smbc_open
smbc_open.argtypes = [c_char_p, c_int, mode_t]
smbc_open.restype = c_int

smbc_read = s.smbc_read
smbc_read.argtypes = [c_int, c_void_p, c_size_t]
smbc_read.restype = c_ssize_t

smbc_opendir = s.smbc_opendir
smbc_opendir.argtypes = [c_char_p]
smbc_opendir.restype = c_int

WORKGROUP = 1
SERVER = 2
FILE_SHARE = 3
PRINTER_SHARE = 4
COMMS_SHARE = 5
IPC_SHARE = 6
DIR = 7
FILE = 8
LINK = 9

TYPE_STRINGS = {
    WORKGROUP: 'workgroup',
    SERVER: 'server',
    FILE_SHARE: 'file_share',
    PRINTER_SHARE: 'printer_share',
    COMMS_SHARE: 'comms_share',
    IPC_SHARE: 'ipc_share',
    DIR: 'dir',
    FILE: 'file',
    LINK: 'link'
}

class smbc_dirent(Structure):
    _fields_ = [
        ('smbc_type', c_uint),
        ('dirlen', c_uint),
        ('commentlen', c_uint),
        ('comment', c_char_p),
        ('namelen', c_uint),
        # This one is wrong, but it works somewhy
	# char name[1];
        ('name', c_char * 128)
    ]

smbc_dirent_p = POINTER(smbc_dirent)

smbc_readdir = s.smbc_readdir
smbc_readdir.argtypes = [c_uint]
smbc_readdir.restype = smbc_dirent_p

smbc_getdents = s.smbc_getdents
smbc_getdents.argtypes = [c_uint, smbc_dirent_p, c_int]

smbc_set_credentials = s.smbc_set_credentials
smbc_set_credentials.argtypes = [c_char_p, c_char_p, c_char_p,
                                 smbc_bool, c_char_p]
smbc_set_credentials.restype = None


if __name__ == '__main__':

    smbc_init(auth_func, 0)
    context = smbc_new_context()
    smbc_init_context(context)
    dir_ = smbc_opendir(sys.argv[1])
    if dir_ < 0:
        perror('Error connecting')
        sys.exit(0)
    while True:
        dirent = smbc_readdir(dir_)
        if not dirent:
            break
        print 'Type', TYPE_STRINGS[dirent.contents.smbc_type]
        print 'Comment', dirent.contents.comment
        print 'Name', dirent.contents.name
        
