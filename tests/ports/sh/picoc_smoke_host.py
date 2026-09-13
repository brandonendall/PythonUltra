"""Run the user's six-part smoke test in the pinned interpreter on the host."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
SH = ROOT / "ports/sh"
VENDOR = SH / "vendor/picoc"
with tempfile.TemporaryDirectory() as folder:
    tmp = Path(folder)
    (tmp / "py").mkdir()
    (tmp / "py/mphal.h").write_text(
        '#include <stdio.h>\n#include <stddef.h>\n'
        'static void mp_hal_stdout_tx_strn(const char *s, size_t n) { fwrite(s, 1, n, stdout); }\n')
    (tmp / "runner.c").write_text('''
#include "picoc.h"
int main(int argc, char **argv) {
    Picoc pc;
    PicocInitialize(&pc, 24 * 1024);
    if (!PicocPlatformSetExitPoint(&pc)) {
        PicocPlatformScanFile(&pc, argv[1]);
        PicocCallMain(&pc, 0, NULL);
    }
    int result = pc.PicocExitValue;
    PicocCleanup(&pc);
    return result;
}
''')
    sources = sorted(VENDOR.glob("*.c")) + sorted((VENDOR / "cstdlib").glob("*.c"))
    binary = tmp / "picoc-test"
    subprocess.run(["gcc", "-w", "-DUNIX_HOST", "-DFXCG50", "-I" + str(VENDOR),
                    "-I" + str(tmp), str(tmp / "runner.c"),
                    str(SH / "picoc_platform_fxcg50.c"),
                    *map(str, sources), "-lm", "-o", str(binary)], check=True)
    result = subprocess.run([str(binary), str(ROOT / "tests/ports/sh/pythonultra_picoc_test.c")],
                            capture_output=True, text=True, timeout=30)
    print(result.stdout, end="")
    assert result.returncode == 0, result.stderr
    for index in range(1, 7):
        assert "T%d PASS" % index in result.stdout
    assert "ALL C TESTS PASSED" in result.stdout
print("PicoC six-part host smoke test: PASS (hardware retest still required)")
