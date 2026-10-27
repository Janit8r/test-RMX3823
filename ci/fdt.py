"""Minimal flattened device tree (FDT/DTB) reader.

Supports the two inputs this project needs:
  * a .dtb file pulled from /sys/firmware/fdt or extracted from vendor_boot
  * a directory tree pulled from /proc/device-tree (binary property files)

No external dependencies; Python 3.8+.
"""

import os
import struct

FDT_MAGIC = 0xD00DFEED
BEGIN_NODE, END_NODE, PROP, NOP, END = 1, 2, 3, 4, 9


class Node:
    __slots__ = ("name", "props", "children", "parent")

    def __init__(self, name, parent=None):
        self.name = name
        self.props = {}
        self.children = []
        self.parent = parent

    # ---- property helpers -------------------------------------------------
    def raw(self, key):
        return self.props.get(key)

    def text(self, key, default=None):
        v = self.props.get(key)
        if v is None:
            return default
        return v.split(b"\0")[0].decode("utf-8", "replace")

    def texts(self, key):
        v = self.props.get(key)
        if v is None:
            return []
        return [s.decode("utf-8", "replace") for s in v.split(b"\0") if s]

    def u32(self, key, default=None):
        v = self.props.get(key)
        if v is None or len(v) < 4:
            return default
        return struct.unpack(">I", v[:4])[0]

    def cells(self, key):
        v = self.props.get(key)
        if v is None:
            return []
        n = len(v) // 4
        return list(struct.unpack(">%dI" % n, v[: n * 4]))

    def u64s(self, key):
        v = self.props.get(key)
        if v is None:
            return []
        n = len(v) // 8
        return list(struct.unpack(">%dQ" % n, v[: n * 8]))

    def has(self, key):
        return key in self.props

    # ---- navigation -------------------------------------------------------
    def path(self):
        parts = []
        n = self
        while n is not None:
            if n.name:
                parts.append(n.name)
            n = n.parent
        return "/" + "/".join(reversed(parts)) if parts else "/"

    def walk(self):
        yield self.path(), self
        for c in self.children:
            yield from c.walk()

    def find(self, path):
        for p, n in self.walk():
            if p == path:
                return n
        return None


def _align4(n):
    return (n + 3) & ~3


def parse_dtb(data):
    if len(data) < 40:
        raise ValueError("file too small for an FDT header")
    (magic, totalsize, off_struct, off_strings, off_rsvmap, version,
     last_comp, boot_cpuid, size_strings, size_struct) = struct.unpack(">10I", data[:40])
    if magic != FDT_MAGIC:
        raise ValueError("bad FDT magic 0x%08X (expected 0x%08X)" % (magic, FDT_MAGIC))

    strings = data[off_strings:off_strings + size_strings]
    struct_blk = data[off_struct:off_struct + size_struct]

    def be32(off):
        return struct.unpack(">I", struct_blk[off:off + 4])[0]

    root = None
    stack = []
    pos = 0
    while pos + 4 <= len(struct_blk):
        tok = be32(pos)
        pos += 4
        if tok == BEGIN_NODE:
            end = struct_blk.index(b"\0", pos)
            name = struct_blk[pos:end].decode("utf-8", "replace")
            pos = _align4(end + 1)
            parent = stack[-1] if stack else None
            node = Node(name, parent)
            if parent is None:
                root = node
            else:
                parent.children.append(node)
            stack.append(node)
        elif tok == END_NODE:
            if stack:
                stack.pop()
        elif tok == PROP:
            length = be32(pos)
            nameoff = be32(pos + 4)
            pos += 8
            val = struct_blk[pos:pos + length]
            pos = _align4(pos + length)
            nend = strings.index(b"\0", nameoff)
            pname = strings[nameoff:nend].decode("utf-8", "replace")
            if stack:
                stack[-1].props[pname] = bytes(val)
        elif tok == NOP:
            continue
        elif tok == END:
            break
    if root is None:
        raise ValueError("no root node in FDT")
    return root


def _read_dir(path, parent=None):
    name = os.path.basename(path.rstrip(os.sep)) or "/"
    node = Node(name, parent)
    try:
        entries = sorted(os.listdir(path))
    except OSError:
        return node
    for entry in entries:
        full = os.path.join(path, entry)
        if os.path.isdir(full):
            node.children.append(_read_dir(full, node))
        elif entry == "name":
            with open(full, "rb") as fh:
                node.name = fh.read().split(b"\0")[0].decode("utf-8", "replace")
        else:
            try:
                with open(full, "rb") as fh:
                    node.props[entry] = fh.read()
            except OSError:
                pass
    return node


def load(path):
    """Load a .dtb file or a /proc/device-tree style directory."""
    if os.path.isdir(path):
        return _read_dir(path)
    with open(path, "rb") as fh:
        return parse_dtb(fh.read())


# ---- register decoding ----------------------------------------------------
def addr_cells(node):
    """Effective address-cell width of a node's children."""
    n = node
    while n is not None:
        v = n.u32("#address-cells")
        if v is not None:
            return v
        n = n.parent
    return 2


def size_cells(node):
    n = node
    while n is not None:
        v = n.u32("#size-cells")
        if v is not None:
            return v
        n = n.parent
    return 2


def reg_ranges(node):
    """Decode a node's reg property using its parent's cell widths."""
    ac = addr_cells(node.parent) if node.parent else 2
    sc = size_cells(node.parent) if node.parent else 2
    cells = node.cells("reg")
    out = []
    step = ac + sc
    for i in range(0, len(cells) - step + 1, step):
        addr = 0
        for c in cells[i:i + ac]:
            addr = (addr << 32) | c
        size = 0
        for c in cells[i + ac:i + step]:
            size = (size << 32) | c
        out.append((addr, size))
    return out
