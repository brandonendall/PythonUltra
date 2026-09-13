"""Host-side regression checks for PythonUltra's pure-Python py3d layer."""

from pathlib import Path
import math
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ports" / "sh" / "modules"))

import py3d


def close(actual, expected, tolerance=1e-7):
    if abs(actual - expected) > tolerance:
        raise AssertionError("%r != %r" % (actual, expected))


# Core vector math.
close(py3d.dot((1, 2, 3), (4, 5, 6)), 32)
close(py3d.length((3, 4, 0)), 5)
normal = py3d.normalize((3, 0, 4))
close(normal[0], 0.6)
close(normal[2], 0.8)
assert py3d.cross((1, 0, 0), (0, 1, 0)) == (0, 0, 1)

# Matrix composition applies transforms in the order listed.
model = py3d.compose(
    py3d.rotation_x(math.pi * 0.5),
    py3d.translation(0, 0, 5),
)
point = py3d.transform((0, 1, 0), model)
close(point[0], 0)
close(point[1], 0)
close(point[2], 6)

# Projection keeps the optical axis centered and rejects the near plane.
projected = py3d.project((0, 0, 2), focal=100, center=(198, 112), near=0.1)
assert projected == (198, 112, 2)
assert py3d.project((1, 1, 0.05), focal=100, near=0.1) is None

# RGB565 helpers remain in-range and deterministic.
assert py3d.rgb565(255, 255, 255) == 0xffff
assert py3d.rgb565(0, 0, 0) == 0x0000
assert py3d.shade_rgb565(0xffff, 0.0) == 0x0000
assert py3d.shade_rgb565(0xffff, 1.0) == 0xffff

# A front-on cube should submit only the two front-face triangles after culling.
vertices, faces = py3d.cube(2.0)
triangles = py3d.prepare_triangles(
    vertices,
    faces,
    position=(0, 0, 5),
    focal=150,
    center=(198, 112),
)
assert len(triangles) == 2, len(triangles)
assert triangles[0][0] >= triangles[-1][0]

# Rotating the cube should expose more than one face while keeping every
# submitted vertex safely in front of the near plane.
rotated = py3d.prepare_triangles(
    vertices,
    faces,
    model=py3d.compose(py3d.rotation_x(0.45), py3d.rotation_y(0.65)),
    position=(0, 0, 5),
    focal=150,
    center=(198, 112),
)
assert 3 <= len(rotated) <= 8, len(rotated)
for triangle in rotated:
    assert triangle[0] > 0.1

print("py3d compatibility tests passed (%d rotated triangles)" % len(rotated))
