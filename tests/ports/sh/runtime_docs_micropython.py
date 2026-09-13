"""Run on the host interpreter with the actual calculator ROM doc table."""
import sys
root = sys.argv[1]
sys.path.insert(0, root + '/tests/ports/sh/micropython')
sys.path.insert(0, root + '/ports/sh/modules')

from py3d import vec3
import py3d
import math
assert vec3(1, 2, 3) == (1.0, 2.0, 3.0)
assert 'vec3(x=0.0, y=0.0, z=0.0)' in vec3.__doc__
assert 'tuple' in vec3.__doc__
assert getattr(vec3, '__doc__') == vec3.__doc__
assert {vec3.__doc__: 1}[vec3.__doc__] == 1
assert hash(vec3.__doc__) == hash(str(vec3.__doc__))
assert 'square root' in math.sqrt.__doc__
assert 'Example:' in py3d.__doc__
help(vec3)
help(math.sqrt)
help(py3d)

import pygame
surface = pygame.Surface((2, 2))
assert 'set_colorkey' in surface.set_colorkey.__doc__
assert 'set_colorkey' in pygame.Surface.set_colorkey.__doc__
assert 'Rect(' in pygame.Rect.__doc__
assert 'fill' in surface.fill.__doc__
assert 'line' in pygame.draw.line.__doc__
surface.set_colorkey((0, 0, 0))
assert surface.get_colorkey() == (0, 0, 0)
class Derived(pygame.Surface):
    pass
assert 'fill' in Derived((2, 2)).fill.__doc__
help(surface.set_colorkey)

# Native bound/unbound methods use a shared implementation, but their docs
# must refer to the correct receiving class; checked wrappers still enforce it.
assert 'list.append' in [].append.__doc__
assert 'list.append' in list.append.__doc__
assert 'str.join' in ''.join.__doc__
assert 'bytes.join' in b''.join.__doc__
try:
    list.append({}, 1)
    raise AssertionError('method type checks changed')
except TypeError:
    pass
import io
assert 'StringIO' in io.StringIO().read.__doc__
assert 'BytesIO' in io.BytesIO().read.__doc__

# Looking up docs must not import/reinitialize gint or execute descriptors.
import gint
def fail(*args):
    raise AssertionError('documentation executed user code')
gint.__init__ = fail
gint.__getattr__ = fail
class NoAttributes:
    __getattr__ = fail
    @property
    def fill(self):
        return fail()
pygame.Surprise = NoAttributes()
for _ in range(20):
    assert 'vec3(' in vec3.__doc__
    assert 'line' in pygame.draw.line.__doc__

# An unrelated same-named function must not get the bundled vec3 docs.
def vec3():
    return 123
assert getattr(vec3, '__doc__', None) is None
assert vec3() == 123
assert getattr(42, '__doc__', None) is None
print('runtime documentation: PASS')
