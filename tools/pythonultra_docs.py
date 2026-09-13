#!/usr/bin/env python3
"""Build the source-audited, plain-text PythonUltra module reference.

Run after the calculator's serial runtime preparation stage. No target module
is imported on the host. Public Python signatures come from ASTs; native
exports are preprocessed with this port's actual MicroPython configuration.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import textwrap
import zipfile

from pythonultra_doc_content import OVERVIEWS, EXAMPLES, DESCRIPTIONS, NATIVE, METHODS

ROOT = Path(__file__).resolve().parents[1]
NATIVE_SOURCES = {
    'builtins': 'py/modbuiltins.c', 'sys': 'py/modsys.c',
    'micropython': 'py/modmicropython.c', 'gc': 'py/modgc.c',
    'math': 'py/modmath.c', 'cmath': 'py/modcmath.c',
    'array': 'py/modarray.c', 'collections': 'py/modcollections.c',
    'io': 'py/modio.c', 'json': 'extmod/modjson.c',
    'struct': 'py/modstruct.c', 'random': 'extmod/modrandom.c',
    'binascii': 'extmod/modbinascii.c', 'errno': 'py/moderrno.c',
    'deflate': 'extmod/moddeflate.c', 'time': 'extmod/modtime.c',
    'gint': 'ports/sh/modgint.c', 'os': 'ports/sh/modos.c',
    'ctypes': 'ports/sh/modctypes.c', 'checksum': 'ports/sh/modchecksum.c',
    'casioplot': 'ports/sh/modcasioplot.c',
    'kandinsky': 'ports/sh/numworks/modkandinsky.c',
    'ion': 'ports/sh/numworks/modion.c',
}


def clean_rst(text):
    text = re.sub(r':\w+:`([^`]+)`', r'\1', text)
    text = text.replace('``', '').replace('**', '')
    return text.strip()


def upstream_entries(root):
    entries = {}
    for path in (root / 'docs/library').glob('*.rst'):
        module = path.stem
        text = path.read_text()
        matches = list(re.finditer(r'^\.\. (?:function|method|class|data|attribute|exception):: (.+)', text, re.M))
        for index, match in enumerate(matches):
            signature = match[1]
            name = signature.split('(')[0].strip().split(' ')[0]
            # Stop at the next unindented section, retaining code examples.
            remainder = text[match.end():matches[index + 1].start() if index + 1 < len(matches) else len(text)]
            body = []
            for line in remainder.splitlines():
                if line and not line.startswith(' '):
                    break
                body.append(line[3:] if line.startswith('   ') else line)
            description = clean_rst('\n'.join(body))
            if description:
                entries[(module, name.removeprefix(module + '.'))] = (signature, description)
    return entries


def preprocess(root, source, temporary):
    # Keep configuration directives while removing platform-only declarations
    # and includes. The unmodified py/mpconfig.h supplies feature defaults.
    port = (root / 'ports/sh/mpconfigport.h').read_text()
    directives = []
    continuing = False
    for line in port.splitlines():
        take = continuing or line.lstrip().startswith(('#define ', '#if ', '#ifdef ', '#ifndef ', '#else', '#elif ', '#endif', '#undef '))
        if take:
            directives.append(line)
        continuing = take and line.rstrip().endswith('\\')
    (temporary / 'mpconfigport.h').write_text('\n'.join(directives) + '\n')
    text = (root / source).read_text()
    if source == 'extmod/modtime.c':
        text = text.replace('#include MICROPY_PY_TIME_INCLUDEFILE', (root / 'ports/sh/modtime.c').read_text())
    text = re.sub(r'^\s*#\s*include[^\n]*', '', text, flags=re.M)
    text = '#include "py/mpconfig.h"\n' + text
    proc = subprocess.run(['cc', '-E', '-P', '-x', 'c', '-I' + str(temporary),
        '-I' + str(root), '-DFXCG50=1', '-DGINT_RENDER_RGB=1',
        '-DGINT_RENDER_MONO=0', '-DGINT_HW_CP=0', '-'],
        input=text, text=True, capture_output=True, check=True)
    return proc.stdout


def native_exports(root):
    result = {}
    with tempfile.TemporaryDirectory() as directory:
        for module, source in NATIVE_SOURCES.items():
            text = preprocess(root, source, Path(directory))
            tables = re.findall(r'(\w+(?:globals|module)_table|\w+globals_table)\s*\[\]\s*=\s*\{(.*?)\n\};', text, re.S)
            exports = {}
            for _, table in tables:
                for match in re.finditer(r'\{\s*(?:MP_ROM_QSTR|MP_OBJ_NEW_QSTR)\(MP_QSTR_(\w+)\),\s*(.*?)\s*\}', table):
                    if not match[1].startswith('_'):
                        exports[match[1]] = match[2]
            # sys exposes some attributes via an attribute callback.
            if module == 'sys':
                for attr in ('path', 'argv', 'modules'):
                    exports.setdefault(attr, 'runtime attribute')
            if not exports:
                raise ValueError('No native exports found: ' + module)
            result[module] = (source, exports, text)
        specs = {
            'builtins.list': ('py/objlist.c', 'list_locals_dict_table'),
            'builtins.dict': ('py/objdict.c', 'dict_locals_dict_table'),
            'builtins.set': ('py/objset.c', 'set_locals_dict_table'),
            'builtins.frozenset': ('py/objset.c', 'frozenset_locals_dict_table'),
            'builtins.tuple': ('py/objtuple.c', 'tuple_locals_dict_table'),
            'io.BytesIO': ('py/objstringio.c', 'stringio_locals_dict_table'),
            'io.StringIO': ('py/objstringio.c', 'stringio_locals_dict_table'),
            'io.file': ('ports/sh/fdfile.c', '.*locals_dict_table'),
            'deflate.DeflateIO': ('extmod/moddeflate.c', 'deflateio_locals_dict_table'),
        }
        for public, (source, table_name) in specs.items():
            text = preprocess(root, source, Path(directory))
            table = re.search(r'\b' + table_name + r'\s*\[\]\s*=\s*\{(.*?)\n\};', text, re.S)
            if not table:
                raise ValueError('No class method table: ' + public)
            module, cls = public.split('.', 1)
            for name in re.findall(r'MP_ROM_QSTR\(MP_QSTR_(\w+)\)', table[1]):
                if not name.startswith('_'):
                    result[module][1][cls + '.' + name] = 'method'
        # str/bytes/bytearray share a sliced native table. Restrict each slice
        # to the applicable protocol and to entries surviving preprocessing.
        text = preprocess(root, 'py/objstr.c', Path(directory))
        table = re.search(r'array_bytearray_str_bytes_locals_table\[\].*?=\s*\{(.*?)\n\};', text, re.S)[1]
        enabled = set(re.findall(r'MP_ROM_QSTR\(MP_QSTR_(\w+)\)', table))
        common = set('find rfind index rindex join split splitlines rsplit startswith endswith strip lstrip rstrip replace count partition rpartition center lower upper isspace isalpha isdigit isupper islower'.split())
        for cls, names in [('str', common | {'format', 'encode'}), ('bytes', common | {'decode', 'hex', 'fromhex'}), ('bytearray', common | {'decode', 'hex', 'fromhex', 'append', 'extend'})]:
            for name in names & enabled:
                result['builtins'][1][cls + '.' + name] = 'method'
        for name in ('append', 'extend'):
            if name in enabled:
                result['array'][1]['array.' + name] = 'method'
    return result


def node_signature(node, owner=''):
    if isinstance(node, ast.ClassDef):
        init = next((n for n in node.body if isinstance(n, ast.FunctionDef) and n.name == '__init__'), None)
        return node.name + '(' + (arguments(init) if init else '') + ')'
    return owner + node.name + '(' + arguments(node) + ')'


def arguments(node):
    args = ast.unparse(node.args)
    return re.sub(r'^(?:self|cls)(?:, )?', '', args)


def python_inventory(root):
    modules = {}
    manifest = ast.parse((root / 'ports/sh/manifest.py').read_text())
    packages = [n.value.args[1].value for n in manifest.body if isinstance(n, ast.Expr)
                and isinstance(n.value, ast.Call) and getattr(n.value.func, 'id', '') == 'freeze']
    for package in packages:
        for path in sorted((root / 'ports/sh/modules' / package).rglob('*.py')):
            if path.name.startswith('_') and path.name != '__init__.py':
                continue
            relative = path.relative_to(root / 'ports/sh/modules').with_suffix('')
            module = '.'.join(relative.parts).removesuffix('.__init__')
            tree = ast.parse(path.read_text())
            nodes, aliases, constants = {}, {}, {}
            classes = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}
            def add_class(cls, public):
                if public.startswith('_'):
                    return
                nodes[public] = cls
                for base in cls.bases:
                    if isinstance(base, ast.Name) and base.id in classes:
                        add_members(classes[base.id], public)
                add_members(cls, public)
            def add_members(cls, public):
                for member in cls.body:
                    if isinstance(member, ast.FunctionDef) and not member.name.startswith('_'):
                        nodes[public + '.' + member.name] = member
                    elif isinstance(member, ast.Assign):
                        for target in member.targets:
                            if isinstance(target, ast.Name) and not target.id.startswith('_'):
                                aliases[public + '.' + target.id] = ast.unparse(member.value)
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                    nodes[node.name] = node
                elif isinstance(node, ast.ClassDef):
                    add_class(node, node.name)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if not isinstance(target, ast.Name) or target.id.startswith('_'):
                            continue
                        value = node.value
                        if isinstance(value, ast.Call) and getattr(value.func, 'id', '') in classes:
                            add_members(classes[value.func.id], target.id)
                        elif isinstance(value, (ast.Name, ast.Attribute)):
                            aliases[target.id] = ast.unparse(value)
                        else:
                            constants[target.id] = ast.unparse(value)
                elif isinstance(node, ast.ImportFrom):
                    for item in node.names:
                        public = item.asname or item.name
                        if not public.startswith('_') and item.name != '*':
                            aliases[public] = node.module + '.' + item.name
            modules[module] = {'source':str(path.relative_to(root)), 'tree':tree,
                               'nodes':nodes, 'aliases':aliases, 'constants':constants,
                               'doc':ast.get_docstring(tree) or ''}
    return modules


def description(module, name, node):
    doc = ast.get_docstring(node) or ''
    key = module + '.' + name
    detail = DESCRIPTIONS.get(key, DESCRIPTIONS.get(name, DESCRIPTIONS.get(name.split('.')[-1], '')))
    return '\n\n'.join(dict.fromkeys(part for part in (detail, doc) if part))


def runtime_table(root, docs, inventory, destination):
    """Emit immutable strings and raw attribute paths; no module imports."""
    entries = dict(docs)
    for module, names in inventory.items():
        overview = OVERVIEWS.get(module, OVERVIEWS.get(module.split('.')[0], ''))
        sample = EXAMPLES.get(module, EXAMPLES.get(module.split('.')[0], ''))
        signatures = sorted(set(docs[module + '.' + name].splitlines()[0]
            for name in names if module + '.' + name in docs
            and '(' in docs[module + '.' + name].splitlines()[0]))
        entries[module] = (module + '\n' + overview + '\n\nExample:\n' + sample
            + '\n\nMembers (help(module.member) for details):\n'
            + '\n'.join(signatures))
    # The reference's common file protocol is implemented by both native types.
    for key, text in list(entries.items()):
        if key.startswith('io.file.'):
            entries[key.replace('io.file.', 'io.FileIO.')] = text
            entries[key.replace('io.file.', 'io.TextIOWrapper.')] = text
    strings, records = {}, []
    for key, text in sorted(entries.items()):
        parts = key.split('.')
        if len(parts) > 5 or not all(part.isidentifier() for part in parts):
            raise ValueError('Unsupported runtime documentation path: ' + key)
        # Constants stay in the offline reference. Never give small integers
        # or interned strings misleading docs by matching a shared value.
        module = max((m for m in inventory if key == m or key.startswith(m + '.')),
                     key=len)
        if key != module and '(' not in text.splitlines()[0] and '[property;' not in text:
            continue
        if text not in strings:
            strings[text] = len(strings)
        path = ', '.join('MP_QSTR_' + part for part in parts[1:]) or 'MP_QSTRnull'
        records.append('    { MP_QSTR_' + parts[0] + ', { ' + path
                       + ' }, &mp_doc_text_' + str(strings[text]) + ' },')
    lines = ['/* Generated by tools/pythonultra_docs.py; do not edit. */']
    for text, number in strings.items():
        literal = json.dumps(text, ensure_ascii=True)
        # C universal escapes cannot represent every control character.
        literal = re.sub(r'\\u00([0-1][0-9a-f]|7f)',
                         lambda m: '\\' + format(int(m[1], 16), '03o'), literal)
        lines.append('static const MP_DEFINE_STR_OBJ(mp_doc_text_' + str(number) + ', ' + literal + ');')
    lines += ['static const mp_doc_entry_t mp_doc_entries[] = {', *records, '};', '']
    destination.parent.mkdir(parents=True, exist_ok=True)
    content = '\n'.join(lines)
    if not destination.exists() or destination.read_text() != content:
        destination.write_text(content)


def build(root, output, allow_missing=False, revision=None, runtime_header=None):
    upstream = upstream_entries(root)
    python = python_inventory(root)
    native = native_exports(root)
    output.mkdir(parents=True, exist_ok=True)
    missing = []
    inventory = {}
    docs = {}
    source_sha = revision or subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    for module in sorted(set(python) | set(native)):
        overview = OVERVIEWS.get(module, OVERVIEWS.get(module.split('.')[0], ''))
        sample = EXAMPLES.get(module, EXAMPLES.get(module.split('.')[0], ''))
        sections = [module + ' — PythonUltra fx-CG50 module reference',
                    'Source snapshot: ' + source_sha,
                    'PURPOSE / CALCULATOR LIMITS\n' + overview,
                    'QUICK EXAMPLE\n' + sample, 'FUNCTIONS, METHODS AND ATTRIBUTES']
        names = []
        if module in python:
            data = python[module]
            sections.insert(3, 'IMPLEMENTATION\n' + data['doc'])
            for name, node in sorted(data['nodes'].items()):
                names.append(name)
                signature = node_signature(node, name.rsplit('.', 1)[0] + '.' if '.' in name else '')
                # The public name may differ from the internal class name.
                if isinstance(node, ast.ClassDef):
                    signature = name + signature[signature.index('('):]
                prop = isinstance(node, ast.FunctionDef) and any(
                    ast.unparse(d) == 'property' or ast.unparse(d).endswith('.setter') for d in node.decorator_list)
                if prop:
                    signature = name + '  [property; read or assign as shown below]'
                detail = description(module, name, node)
                if not detail:
                    missing.append(module + '.' + name)
                code = ast.get_source_segment((root / data['source']).read_text(), node)
                # Keep exact behavior reviewable. Constructors and functions
                # include their implementation; class listings link methods.
                if isinstance(node, ast.ClassDef):
                    init = next((n for n in node.body if isinstance(n, ast.FunctionDef) and n.name == '__init__'), None)
                    code = ast.unparse(init) if init else 'Inherited constructor; see base methods.'
                sections.append(signature + '\n' + detail + '\n\nImplementation detail:\n' + textwrap.indent(code, '    '))
                docs[module + '.' + name] = signature + '\n' + detail
            if data['aliases']:
                sections.append('ALIASES / RE-EXPORTED MEMBERS\n' + '\n'.join(k + ' = ' + v for k, v in sorted(data['aliases'].items())))
                names += list(data['aliases'])
            if data['constants']:
                sections.append('CONSTANTS / INITIAL VALUES\n' + '\n'.join(k + ' = ' + v for k, v in sorted(data['constants'].items())))
                names += list(data['constants'])
                for name, value in data['constants'].items():
                    docs[module + '.' + name] = name + ' = ' + value
            sections.append('Source: ' + data['source'])
        else:
            source, exports, ctext = native[module]
            for name, value in sorted(exports.items()):
                names.append(name)
                entry = NATIVE.get(module + '.' + name) or upstream.get((module, name))
                if not entry and value == 'method':
                    method = name.split('.')[-1]
                    entry = METHODS.get(name) or METHODS.get(method)
                    if entry:
                        entry = (name.rsplit('.', 1)[0] + '.' + entry[0], entry[1])
                if entry:
                    signature, detail = entry
                elif name[0].isupper() and ('INT' in value or module in ('errno', 'ion', 'gint')):
                    signature, detail = name, 'Named constant exported by this build. Pass the named constant instead of guessing its numeric value.'
                elif 'mp_type_' in value and name.endswith(('Error', 'Exception')):
                    signature, detail = name + '(*args)', 'Exception type; catch with except ' + name + ' as error. error.args stores constructor arguments.'
                elif name in ('True', 'False', 'None', 'Ellipsis', 'NotImplemented'):
                    signature, detail = name, 'Python built-in singleton value.'
                else:
                    signature, detail = name, ''
                    missing.append(module + '.' + name)
                sections.append(signature + '\n' + detail)
                docs[module + '.' + name] = signature + '\n' + detail
            sections.append('Source: ' + source)
        inventory[module] = sorted(set(names))
        (output / (module + '.txt')).write_text('\n\n'.join(sections) + '\n', encoding='utf-8')
    # Re-exported pygame modules must have full member descriptions, not only
    # an alias table requiring desktop documentation.
    # Resolve aliases repeatedly (for example time.wait -> delay and Clock
    # -> pygame.Clock), retaining constructor methods in submodule references.
    for _ in range(4):
        for module, data in python.items():
            for name, target in data['aliases'].items():
                prefix = module.rsplit('.', 1)[0] if '.' in module else module
                target = re.sub(r'^_(display|draw|event|key|time|font|image|transform|sprite)\.', r'\1.', target)
                candidates = [target, prefix + '.' + target, module + '.' + target,
                              prefix + '.' + target.split('.')[-1], 'builtins.' + target,
                              target.replace('_math.', 'math.').replace('_g.', 'gint.')]
                # Aliases inside helper classes are relative to that class.
                if '.' in name:
                    candidates.insert(0, module + '.' + name.rsplit('.', 1)[0] + '.' + target)
                for key in candidates:
                    if key in docs:
                        docs[module + '.' + name] = docs[key]
                        for child in list(docs):
                            if child.startswith(key + '.'):
                                docs[module + '.' + name + child[len(key):]] = docs[child]
                        break
    for module, data in python.items():
        additions = []
        for name in data['aliases']:
            key = module + '.' + name
            if key in docs:
                additions.append(name + '\n' + docs[key])
                additions += [child.removeprefix(module + '.') + '\n' + docs[child]
                              for child in sorted(docs) if child.startswith(key + '.')]
            else:
                target = data['aliases'][name]
                if name.startswith('K_'):
                    additions.append(name + ' = ' + target + '\nPhysical-key alias used by this calculator Pygame mapping.')
                elif name.startswith('version.'):
                    additions.append(name + ' = ' + target + '\nCompatibility-layer version metadata, not the MicroPython version.')
                else:
                    missing.append(key + ' [unresolved alias]')
        if module == 'pygame.locals':
            additions.append('Re-exports the public names from pygame. See pygame.txt for all constants, classes and operations.')
        if additions:
            with (output / (module + '.txt')).open('a') as f:
                f.write('\nRESOLVED ALIAS DETAILS\n\n' + '\n\n'.join(additions) + '\n')
    (output / 'API-INVENTORY.json').write_text(json.dumps(inventory, indent=2) + '\n')
    (output / 'documentation-index.json').write_text(json.dumps(docs, indent=2) + '\n')
    (output / 'MISSING.json').write_text(json.dumps(sorted(set(missing)), indent=2) + '\n')
    if missing and not allow_missing:
        raise SystemExit('Missing descriptions (see MISSING.json): ' + str(len(set(missing))))
    if runtime_header is not None:
        runtime_table(root, docs, inventory, runtime_header)
    readme = '''PYTHONULTRA MODULE DOCUMENTATION

One text file per bundled public module and frozen submodule. Read the purpose
and calculator limits first, then the example and member reference. Python
functions include exact implementation details to make edge cases reviewable.
Private helpers are not a promised public API. Inherited methods are included.

This is a calculator compatibility build, not desktop NumPy/Pygame/ctypes.
Sound, networking, PicoC, datetime, pathlib and csv are not integrated. Turtle
and matplotl source files are not frozen in the current fx-CG50 manifest.

MicroPython source version: 1.25.0-preview. The leading 3.4.0 in sys.version
is a Python compatibility label, not the MicroPython release number.
Use sys.implementation.version to identify the interpreter release.

Documentation is generated from the prepared calculator source. Native APIs
are filtered using this port's build configuration. Upstream descriptions come
from the checked-in MicroPython reference, with calculator-specific corrections.
Builds with the ROM reference enabled expose these descriptions via help(obj)
and obj.__doc__, including native functions and frozen Python functions/methods.
For example: from py3d import vec3; help(vec3); print(vec3.__doc__). The reference
does not change calling conventions or add desktop APIs. It documents the
bundled public API; arbitrary user-defined function docstrings are not retained
by this MicroPython compiler. Earlier builds, including #131/#132, have the ZIP
reference but do not yet include the new runtime help implementation.

MAINTENANCE
Run tools/pythonultra_docs.py after the serial runtime preparation step.
Every new/changed public member must update documentation and examples.
CI must regenerate the reference and fail for missing member descriptions.
Keep the ZIP with each numbered release so readers know which build it covers.

MODULE FILES
'''
    (output / '00-START-HERE.txt').write_text(readme + '\n'.join(m + '.txt' for m in sorted(inventory)) + '\n')
    (output / 'LICENSE-MicroPython.txt').write_text((root / 'LICENSE').read_text())
    archive = output.parent / 'PythonUltra-Module-Documentation.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for file in sorted(output.glob('*')):
            if file.name in ('MISSING.json', 'documentation-index.json'):
                continue
            z.write(file, 'PythonUltra-Module-Documentation/' + file.name)
    print(json.dumps({'modules':len(inventory), 'members':sum(map(len, inventory.values())),
                      'missing':len(set(missing)), 'zip':str(archive),
                      'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--allow-missing', action='store_true')
    parser.add_argument('--revision', help='Verified upstream commit equivalent to the local source snapshot')
    parser.add_argument('--runtime-header', type=Path, help='Generate the ROM help/__doc__ table before compilation')
    args = parser.parse_args()
    build(args.source.resolve(), args.output.resolve(), args.allow_missing, args.revision,
          args.runtime_header.resolve() if args.runtime_header else None)
