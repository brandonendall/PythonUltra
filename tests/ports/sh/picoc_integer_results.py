"""Run the actual PicoC integer-push function with big-endian scalar storage.

GCC's scalar_storage_order attribute models the union layout on the CG50;
this is a host regression for result storage, not calculator emulation.
"""
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
source_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "ports/sh/vendor/picoc/expression.c"
source = source_path.read_text()
function = source[source.index("\nvoid ExpressionPushInt("):source.index("\nvoid ExpressionPushFP(")]
prefix = r'''
#include <assert.h>
#include <stddef.h>
#include <stdbool.h>
#include <stdint.h>
union __attribute__((scalar_storage_order("big-endian"))) AnyValue {
    int32_t Integer; uint32_t UnsignedInteger;
    int32_t LongInteger; uint32_t UnsignedLongInteger;
    int16_t ShortInteger; uint16_t UnsignedShortInteger;
    char Character; unsigned char UnsignedCharacter;
};
struct Value { union AnyValue *Val; };
struct Picoc { int IntType; };
struct ParseState { struct Picoc *pc; };
struct ExpressionStack { int unused; };
static union AnyValue storage;
static struct Value value = { &storage };
static struct Value *VariableAllocValueFromType(struct Picoc *pc,
    struct ParseState *p, int *type, bool a, void *b, bool c) { return &value; }
static void ExpressionStackPushValueNode(struct ParseState *p,
    struct ExpressionStack **s, struct Value *v) {}
'''
suffix = r'''
int main(void) {
    struct Picoc pc; struct ParseState p = { &pc };
    struct ExpressionStack *stack = NULL;
    long cases[] = {0, 12, 15, 30, 42, 60, 255, 256, 65536, -1, -12345};
    for(unsigned i = 0; i < sizeof(cases)/sizeof(cases[0]); ++i) {
        ExpressionPushInt(&p, &stack, cases[i]);
        assert(storage.Integer == cases[i]);
    }
    return 0;
}
'''
with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / "integer.c"
    path.write_text(prefix + function + suffix)
    binary = Path(folder) / "integer"
    subprocess.run(["gcc", "-std=c99", "-Werror=scalar-storage-order",
                    str(path), "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
print("PicoC big-endian integer-result regression: PASS")
