# -*- coding: utf-8 -*-

"""btrfs constants and structure definitions
"""

import array
import fcntl
import itertools
import struct

ULLONG_MAX = (1 << 64) - 1
ULONG_MAX = (1 << 32) - 1


def ULL(n):
    if n < 0:
        return n + (1 << 64)
    return n


def UL(n):
    if n < 0:
        return n + (1 << 32)
    return n

# ioctl numbers
IOC_SNAP_CREATE = 0x50009401
IOC_DEV_ADD = 0x5000940a
IOC_DEV_RM = 0x5000940b
IOC_SUBVOL_CREATE = 0x5000940e
IOC_SNAP_DESTROY = 0x5000940f
IOC_TREE_SEARCH = 0xd0009411
IOC_TREE_SEARCH_V2 = 0xc0709411
IOC_DEFAULT_SUBVOL = 0x40089413
IOC_SPACE_INFO = 0xc0109414

# Object IDs
ROOT_TREE_OBJECTID = 1
DEV_ITEMS_OBJECTID = 1
EXTENT_TREE_OBJECTID = 2
CHUNK_TREE_OBJECTID = 3
DEV_TREE_OBJECTID = 4
FS_TREE_OBJECTID = 5
ROOT_TREE_DIR_OBJECTID = 6
CSUM_TREE_OBJECTID = 7
ORPHAN_OBJECTID = ULL(-5)
TREE_LOG_OBJECTID = ULL(-6)
TREE_LOG_FIXUP_OBJECTID = ULL(-7)
TREE_RELOC_OBJECTID = ULL(-8)
DATA_RELOC_TREE_OBJECTID = ULL(-9)
EXTENT_CSUM_OBJECTID = ULL(-10)
FREE_SPACE_OBJECTID = ULL(-11)
MULTIPLE_OBJECTIDS = ULL(-255)
FIRST_FREE_OBJECTID = 256
LAST_FREE_OBJECTID = ULL(-256)
FIRST_CHUNK_TREE_OBJECTID = 256
DEV_ITEMS_OBJECTID = 1
BTREE_INODE_OBJECTID = 1
EMPTY_SUBVOL_DIR_OBJECTID = 2

# Item keys
INODE_ITEM_KEY = 1
INODE_REF_KEY = 12
XATTR_ITEM_KEY = 24
ORPHAN_ITEM_KEY = 48
DIR_LOG_ITEM_KEY = 60
DIR_LOG_INDEX_KEY = 72
DIR_ITEM_KEY = 84
DIR_INDEX_KEY = 96
EXTENT_DATA_KEY = 108
EXTENT_CSUM_KEY = 128
ROOT_ITEM_KEY = 132
ROOT_BACKREF_KEY = 144
ROOT_REF_KEY = 156
EXTENT_ITEM_KEY = 168
TREE_BLOCK_REF_KEY = 176
EXTENT_DATA_REF_KEY = 178
EXTENT_REF_V0_KEY = 180
SHARED_BLOCK_REF_KEY = 182
SHARED_DATA_REF_KEY = 184
BLOCK_GROUP_ITEM_KEY = 192
DEV_EXTENT_KEY = 204
DEV_ITEM_KEY = 216
CHUNK_ITEM_KEY = 228
STRING_ITEM_KEY = 253

# Block group flags
BLOCK_GROUP_DATA = 1 << 0
BLOCK_GROUP_SYSTEM = 1 << 1
BLOCK_GROUP_METADATA = 1 << 2
BLOCK_GROUP_RAID0 = 1 << 3
BLOCK_GROUP_RAID1 = 1 << 4
BLOCK_GROUP_DUP = 1 << 5
BLOCK_GROUP_RAID10 = 1 << 6

# ioctl structures
ioctl_space_args = struct.Struct("=2Q")
ioctl_space_info = struct.Struct("=3Q")
ioctl_search_key = struct.Struct("=Q6QLLL4x32x")
ioctl_search_header = struct.Struct("=3Q2L")  # transid, objectid, offset, type, len
PATH_NAME_MAX = 4087
ioctl_vol_args = struct.Struct("=q4088s")
ioctl_default_subvol = struct.Struct("=Q")

# Internal data structures
disk_key = struct.Struct("<QBQ")  # objectid, type, offset
dev_item = struct.Struct("<3Q3L3QL2B16s16s")
dev_extent = struct.Struct("<4Q16s")
chunk = struct.Struct("<4Q3L2H")
stripe = struct.Struct("<2Q16s")
block_group_item = struct.Struct("<3Q")
root_ref = struct.Struct("<2QH")
inode_ref = struct.Struct("<QH")
dir_item = struct.Struct("<QBQQHHB")


def format_uuid(id):
    return "{0:02x}{1:02x}{2:02x}{3:02x}-{4:02x}{5:02x}-{6:02x}{7:02x}-" \
           "{8:02x}{9:02x}-{10:02x}{11:02x}{12:02x}{13:02x}{14:02x}{15:02x}" \
           .format(*struct.unpack("16B", id))


def replication_type(bgid):
    if bgid & BLOCK_GROUP_RAID0:
        return "RAID0"
    elif bgid & BLOCK_GROUP_RAID1:
        return "RAID1"
    elif bgid & BLOCK_GROUP_RAID10:
        return "RAID10"
    elif bgid & BLOCK_GROUP_DUP:
        return "DUP"
    else:
        return "Single"


def usage_type(bgid):
    if (bgid & BLOCK_GROUP_DATA) and (bgid & BLOCK_GROUP_METADATA):
        return "mixed"
    elif bgid & BLOCK_GROUP_DATA:
        return "data"
    elif bgid & BLOCK_GROUP_METADATA:
        return "meta"
    elif bgid & BLOCK_GROUP_SYSTEM:
        return "sys"
    else:
        return ""


EXTENT_FLAG_DATA = 1 << 0
EXTENT_FLAG_TREE_BLOCK = 1 << 1
BLOCK_FLAG_FULL_BACKREF = 1 << 1

extent_item = struct.Struct("<3Q")  # refs, generation, flags
extent_inline_ref = struct.Struct("<BQ")  # type, offset
extent_data_ref = struct.Struct("<3QL")  # root, objectid, offset, count
shared_data_ref = struct.Struct("<L")  # count


def extent_flags_to_str(flags):
    ret = []
    if flags & EXTENT_FLAG_DATA:
        ret.append("DATA")
    if flags & EXTENT_FLAG_TREE_BLOCK:
        ret.append("TREE_BLOCK")
    if flags & BLOCK_FLAG_FULL_BACKREF:
        ret.append("FULL_BACKREF")
    return '|'.join(ret)


def sized_array(count=4096):
    return array.array("B", itertools.repeat(0, count))


def search(fd,
           tree,
           objid=(0, ULLONG_MAX),
           key_type=(0, ULONG_MAX),
           offset=(0, ULLONG_MAX),
           transid=(0, ULLONG_MAX),
           number=ULONG_MAX,
           structure=None,
           buf=None):
    try:
        min_objid, max_objid = objid
    except TypeError:
        min_objid = max_objid = objid
    try:
        min_type, max_type = key_type
    except TypeError:
        min_type = max_type = key_type
    try:
        min_offset, max_offset = offset
    except TypeError:
        min_offset = max_offset = offset
    try:
        min_transid, max_transid = transid
    except TypeError:
        min_transid = max_transid = transid

    if buf is None:
        buf = sized_array()
    ioctl_search_key.pack_into(
        buf, 0,
        tree,
        min_objid, max_objid,
        min_offset, max_offset,
        min_transid, max_transid,
        min_type, max_type,
        number
        )

    fcntl.ioctl(fd, IOC_TREE_SEARCH, buf)
    results = ioctl_search_key.unpack_from(buf, 0)
    num_items = results[9]
    pos = ioctl_search_key.size
    ret = []
    while num_items > 0:
        num_items -= 1
        header = ioctl_search_header.unpack_from(buf, pos)
        pos += ioctl_search_header.size
        raw_data = buf[pos:pos+header[4]]
        data = None
        if structure is not None:
            data = structure.unpack_from(buf, pos)
        ret.append((header, raw_data, data))
        pos += header[4]

    return ret
