"""Round-trip and cleanup regressions for PythonUltra calculator ZIP files."""

import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import zipfile as standard_zipfile
import zlib

ROOT = Path(__file__).resolve().parents[3]
ZIP_PATH = ROOT / "ports" / "sh" / "modules" / "zipfile" / "__init__.py"
FDFILE_PATH = ROOT / "ports" / "sh" / "fdfile.c"


class HostDeflateIO:
    """Small host adapter for MicroPython's deflate.DeflateIO API."""
    def __init__(self, stream, format_value, window, close_stream):
        del format_value, window, close_stream
        self.stream = stream
        self.writer = bool(getattr(stream, "writable", lambda: False)())
        self.compressor = zlib.compressobj(level=8, wbits=-15) if self.writer else None
        self.data = None
        self.position = 0

    def write(self, data):
        encoded = self.compressor.compress(data)
        if encoded:
            self.stream.write(encoded)
        return len(data)

    def read(self, size=-1):
        if self.data is None:
            decoder = zlib.decompressobj(wbits=-15)
            self.data = decoder.decompress(self.stream.read()) + decoder.flush()
        if size is None or size < 0:
            result = self.data[self.position:]
            self.position = len(self.data)
            return result
        result = self.data[self.position:self.position + size]
        self.position += len(result)
        return result

    def close(self):
        if self.writer and self.compressor is not None:
            encoded = self.compressor.flush()
            if encoded:
                self.stream.write(encoded)
            self.compressor = None


fake_deflate = types.ModuleType("deflate")
fake_deflate.RAW = 0
fake_deflate.DeflateIO = HostDeflateIO
sys.modules["deflate"] = fake_deflate

spec = importlib.util.spec_from_file_location("pythonultra_zipfile_test", ZIP_PATH)
calculator_zipfile = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calculator_zipfile)


with tempfile.TemporaryDirectory() as temp_root:
    root = Path(temp_root)
    source = root / "project"
    nested = source / "assets"
    nested.mkdir(parents=True)
    (source / "main.py").write_text("print('PythonUltra')\n", encoding="utf-8")
    (nested / "sprite.bin").write_bytes(bytes(range(256)) * 5)
    (nested / "empty.txt").write_bytes(b"")

    archive = root / "project.zip"
    assert calculator_zipfile.compress(str(source), str(archive)) == str(archive)
    assert archive.stat().st_size > 22

    # Archives created by PythonUltra must also be standard desktop ZIPs.
    with standard_zipfile.ZipFile(archive, "r") as check:
        names = check.namelist()
        assert "project/main.py" in names
        assert "project/assets/sprite.bin" in names
        assert check.read("project/main.py") == b"print('PythonUltra')\n"
        assert check.read("project/assets/sprite.bin") == bytes(range(256)) * 5

    assert "project/main.py" in calculator_zipfile.namelist(str(archive))
    destination = root / "roundtrip"
    assert calculator_zipfile.extract(str(archive), str(destination)) == str(destination)
    assert (destination / "project" / "main.py").read_text(encoding="utf-8") == "print('PythonUltra')\n"
    assert (destination / "project" / "assets" / "sprite.bin").read_bytes() == bytes(range(256)) * 5
    assert (destination / "project" / "assets" / "empty.txt").read_bytes() == b""

    # A failed extraction removes only paths created by that attempt.
    truncated = root / "truncated.zip"
    truncated.write_bytes(archive.read_bytes()[:-10])
    failed_destination = root / "failed"
    try:
        calculator_zipfile.extract(str(truncated), str(failed_destination))
        raise AssertionError("truncated archive unexpectedly extracted")
    except ValueError:
        pass
    assert not failed_destination.exists()

    existing_destination = root / "existing"
    existing_destination.mkdir()
    keep = existing_destination / "keep.txt"
    keep.write_text("keep", encoding="utf-8")
    try:
        calculator_zipfile.extract(str(truncated), str(existing_destination))
        raise AssertionError("truncated archive unexpectedly extracted")
    except ValueError:
        pass
    assert keep.read_text(encoding="utf-8") == "keep"

    # Do not truncate existing archives or let a ZIP include itself.
    before = archive.read_bytes()
    for bad_target in (archive, nested / "inside.zip"):
        try:
            calculator_zipfile.compress(str(source), str(bad_target))
            raise AssertionError("unsafe output path accepted")
        except ValueError:
            pass
    assert archive.read_bytes() == before
    assert not (nested / "inside.zip").exists()

    # Bad CRC after an earlier successful entry rolls back new output only.
    bad_crc = root / "bad-crc.zip"
    with standard_zipfile.ZipFile(bad_crc, "w", compression=standard_zipfile.ZIP_STORED) as out:
        out.writestr("good.txt", b"good")
        out.writestr("bad.txt", b"PAYLOAD")
    data = bad_crc.read_bytes().replace(b"PAYLOAD", b"DAMAGED", 1)
    bad_crc.write_bytes(data)
    try:
        calculator_zipfile.extract(str(bad_crc), str(existing_destination))
        raise AssertionError("bad CRC accepted")
    except ValueError:
        pass
    assert sorted(p.name for p in existing_destination.iterdir()) == ["keep.txt"]

# The calculator fd stream must implement the positioning ZIP depends on.
fdfile = FDFILE_PATH.read_text(encoding="utf-8")
assert "request == MP_STREAM_SEEK" in fdfile
assert "GINT_CALL(fdfile_world_seek" in fdfile
assert "call->result = lseek(" in fdfile
assert "seek->offset = call.result" in fdfile
assert "request == MP_STREAM_FLUSH" in fdfile
assert "FIXME: implement seek/flush" not in fdfile

print("PythonUltra ZIP round-trip regression checks passed")
