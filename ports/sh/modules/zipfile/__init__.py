"""Calculator-sized ZIP support for PythonUltra.

Supports standard ZIP archives using stored or DEFLATE-compressed entries.
ZIP64, encrypted entries and multi-disk archives are intentionally unsupported.
"""

import binascii
import deflate
import os
import struct
import errno

__version__ = "0.1.0-cg50"

_LOCAL = 0x04034B50
_CENTRAL = 0x02014B50
_EOCD = 0x06054B50
_DESCRIPTOR = 0x08074B50


def _basename(path):
    value = path.rstrip("/")
    return value.split("/")[-1] if value else "archive"


def _parent(path):
    parts = path.rstrip("/").split("/")
    value = "/".join(parts[:-1])
    return value if value else "/"


def _join(folder, name):
    if folder == "/":
        return "/" + name
    return folder.rstrip("/") + "/" + name


def _is_dir(path):
    try:
        return bool(os.stat(path)[0] & 0x4000)
    except OSError:
        return False


def _exists(path):
    try:
        os.stat(path)
        return True
    except OSError as exc:
        if exc.args and exc.args[0] == errno.ENOENT:
            return False
        raise


def _absolute(path):
    if not path.startswith("/"):
        path = os.getcwd().rstrip("/") + "/" + path
    parts = []
    for part in path.split("/"):
        if part == "..":
            if parts: parts.pop()
        elif part and part != ".":
            parts.append(part)
    return "/" + "/".join(parts)


def _size(path):
    return os.stat(path)[6]


def _mkdirs(path, created=None):
    if not path or path == "/":
        return
    current = "" if path.startswith("/") else None
    for part in path.split("/"):
        if not part:
            continue
        if current is None:
            current = part
        elif current == "":
            current = "/" + part
        else:
            current += "/" + part
        try:
            os.mkdir(current)
            if created is not None:
                created.append(current)
        except OSError:
            if not _is_dir(current):
                raise


def _cleanup(files, folders):
    """Remove only output paths created by the failed operation."""
    for path in reversed(files):
        try:
            os.remove(path)
        except OSError:
            pass
    for path in reversed(folders):
        try:
            os.rmdir(path)
        except OSError:
            pass


def _safe_name(name):
    name = name.replace("\\", "/")
    while name.startswith("/"):
        name = name[1:]
    parts = []
    for part in name.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            raise ValueError("unsafe ZIP path")
        parts.append(part)
    return "/".join(parts)


def _walk(path, arcname=None):
    if arcname is None:
        arcname = _basename(path)
    if _is_dir(path):
        root = arcname.rstrip("/") + "/"
        yield path, root, True
        for name in sorted(os.listdir(path)):
            child = _join(path, name)
            child_arc = root + name
            for item in _walk(child, child_arc):
                yield item
    else:
        yield path, arcname, False


def _write_entry(out, path, name, is_dir):
    name_bytes = name.encode("utf-8")
    local_offset = out.tell()
    if is_dir:
        flags = 0x0800
        method = 0
        crc = csize = usize = 0
        out.write(struct.pack("<IHHHHHIIIHH", _LOCAL, 20, flags, method, 0, 0,
                              crc, csize, usize, len(name_bytes), 0))
        out.write(name_bytes)
        return (name_bytes, flags, method, crc, csize, usize, local_offset, True)

    flags = 0x0808  # UTF-8 + data descriptor.
    method = 8
    out.write(struct.pack("<IHHHHHIIIHH", _LOCAL, 20, flags, method, 0, 0,
                          0, 0, 0, len(name_bytes), 0))
    out.write(name_bytes)
    data_start = out.tell()
    crc = 0
    usize = 0
    with open(path, "rb") as src:
        stream = deflate.DeflateIO(out, deflate.RAW, 8, False)
        while True:
            block = src.read(1024)
            if not block:
                break
            usize += len(block)
            crc = binascii.crc32(block, crc) & 0xffffffff
            stream.write(block)
        stream.close()
    csize = out.tell() - data_start
    out.write(struct.pack("<IIII", _DESCRIPTOR, crc, csize, usize))
    return (name_bytes, flags, method, crc, csize, usize, local_offset, False)


def compress(source, archive=None):
    """Compress one file or a whole folder to a standard .zip archive."""
    if archive is None:
        archive = source.rstrip("/") + ".zip"
    source = _absolute(source)
    archive = _absolute(archive)
    if _exists(archive):
        raise ValueError("ZIP target exists")
    if _is_dir(source) and archive.startswith(source.rstrip("/") + "/"):
        raise ValueError("ZIP must be outside source folder")
    records = []
    created = False
    try:
        with open(archive, "wb") as out:
            created = True
            for path, name, is_dir in _walk(source):
                records.append(_write_entry(out, path, name, is_dir))

            central_offset = out.tell()
            for name, flags, method, crc, csize, usize, local_offset, is_dir in records:
                external = 0x10 if is_dir else 0
                out.write(struct.pack("<IHHHHHHIIIHHHHHII",
                                      _CENTRAL, 20, 20, flags, method, 0, 0,
                                      crc, csize, usize, len(name), 0, 0,
                                      0, 0, external, local_offset))
                out.write(name)
            central_size = out.tell() - central_offset
            count = len(records)
            out.write(struct.pack("<IHHHHIIH", _EOCD, 0, 0, count, count,
                                  central_size, central_offset, 0))
    except Exception:
        if created:
            try:
                os.remove(archive)
            except OSError:
                pass
        raise
    return archive


def _find_eocd(f, total_size):
    signature = b"PK\x05\x06"
    limit = max(0, total_size - 65557)
    pos = total_size
    carry = b""
    while pos > limit:
        start = max(limit, pos - 2048)
        f.seek(start)
        data = f.read(pos - start) + carry
        idx = data.rfind(signature)
        if idx >= 0:
            return start + idx
        carry = data[:3]
        pos = start
    raise ValueError("ZIP end record not found")


def _entries(archive):
    size = _size(archive)
    result = []
    with open(archive, "rb") as f:
        eocd = _find_eocd(f, size)
        f.seek(eocd)
        raw = f.read(22)
        if len(raw) != 22:
            raise ValueError("truncated ZIP")
        sig, disk, disk_cd, count_disk, count, cd_size, cd_offset, comment = struct.unpack("<IHHHHIIH", raw)
        if sig != _EOCD or disk or disk_cd or count_disk != count:
            raise ValueError("unsupported multi-disk ZIP")
        f.seek(cd_offset)
        for _ in range(count):
            fixed = f.read(46)
            if len(fixed) != 46:
                raise ValueError("truncated central directory")
            values = struct.unpack("<IHHHHHHIIIHHHHHII", fixed)
            if values[0] != _CENTRAL:
                raise ValueError("bad central directory")
            flags = values[3]
            method = values[4]
            crc = values[7]
            csize = values[8]
            usize = values[9]
            name_len = values[10]
            extra_len = values[11]
            comment_len = values[12]
            local_offset = values[16]
            name_bytes = f.read(name_len)
            f.seek(extra_len + comment_len, 1)
            try:
                name = name_bytes.decode("utf-8")
            except Exception:
                name = name_bytes.decode("latin-1")
            result.append((name, flags, method, crc, csize, usize, local_offset))
    return result


def namelist(archive):
    return tuple(item[0] for item in _entries(archive))


def extract(archive, destination=None):
    """Extract a ZIP archive. Returns the destination folder."""
    if destination is None:
        base = archive[:-4] if archive.lower().endswith(".zip") else archive + "_files"
        destination = base
    created_files = []
    created_folders = []
    try:
        entries = _entries(archive)
        _mkdirs(destination, created_folders)
        with open(archive, "rb") as src:
            for name, flags, method, crc_expected, csize, usize, local_offset in entries:
                if flags & 1:
                    raise ValueError("encrypted ZIP entries unsupported")
                clean = _safe_name(name)
                if not clean:
                    continue
                target = _join(destination, clean)
                if name.endswith("/"):
                    _mkdirs(target, created_folders)
                    continue
                _mkdirs(_parent(target), created_folders)
                if _is_dir(target) or _exists(target):
                    raise ValueError("ZIP target exists: " + clean)
                src.seek(local_offset)
                header = src.read(30)
                if len(header) != 30:
                    raise ValueError("truncated local header")
                values = struct.unpack("<IHHHHHIIIHH", header)
                if values[0] != _LOCAL:
                    raise ValueError("bad local header")
                name_len = values[9]
                extra_len = values[10]
                src.seek(name_len + extra_len, 1)
                crc = 0
                written = 0
                with open(target, "wb") as out:
                    created_files.append(target)
                    if method == 0:
                        remaining = csize
                        while remaining:
                            block = src.read(min(1024, remaining))
                            if not block:
                                raise ValueError("truncated stored entry")
                            remaining -= len(block)
                            written += len(block)
                            crc = binascii.crc32(block, crc) & 0xffffffff
                            out.write(block)
                    elif method == 8:
                        stream = deflate.DeflateIO(src, deflate.RAW, 15, False)
                        while True:
                            block = stream.read(1024)
                            if not block:
                                break
                            written += len(block)
                            crc = binascii.crc32(block, crc) & 0xffffffff
                            out.write(block)
                        stream.close()
                    else:
                        raise ValueError("unsupported ZIP method " + str(method))
                if written != usize or crc != crc_expected:
                    raise ValueError("ZIP CRC/size mismatch: " + clean)
    except Exception:
        _cleanup(created_files, created_folders)
        raise
    return destination
