"""PythonUltra compact software 3D engine for the Casio fx-CG50.

The renderer is intentionally small: transform vertices in Python, use a
painter's algorithm for depth, cull back faces, and hand filled triangles to
the native ``gint.dtriangle()`` rasterizer.  The camera looks along +Z.
"""

import math

SCREEN_WIDTH = 396
SCREEN_HEIGHT = 224


def vec3(x=0.0, y=0.0, z=0.0):
    return (float(x), float(y), float(z))


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def scale(v, amount):
    return (v[0] * amount, v[1] * amount, v[2] * amount)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def length(v):
    return math.sqrt(dot(v, v))


def normalize(v):
    magnitude = length(v)
    if magnitude == 0:
        return (0.0, 0.0, 0.0)
    return scale(v, 1.0 / magnitude)


def identity():
    return (
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    )


def matmul4(a, b):
    """Multiply two row-major 4x4 matrices (a * b)."""
    output = [0.0] * 16
    for row in range(4):
        row4 = row * 4
        for col in range(4):
            output[row4 + col] = (
                a[row4] * b[col]
                + a[row4 + 1] * b[4 + col]
                + a[row4 + 2] * b[8 + col]
                + a[row4 + 3] * b[12 + col]
            )
    return tuple(output)


def compose(*matrices):
    """Compose transforms in the order listed.

    ``compose(rotation_y(a), translation(0, 0, 5))`` rotates first and then
    translates, which is usually the useful order for model transforms.
    """
    result = identity()
    for matrix in matrices:
        result = matmul4(matrix, result)
    return result


def translation(x, y, z):
    return (
        1.0, 0.0, 0.0, float(x),
        0.0, 1.0, 0.0, float(y),
        0.0, 0.0, 1.0, float(z),
        0.0, 0.0, 0.0, 1.0,
    )


def scaling(x, y=None, z=None):
    if y is None:
        y = x
    if z is None:
        z = x
    return (
        float(x), 0.0, 0.0, 0.0,
        0.0, float(y), 0.0, 0.0,
        0.0, 0.0, float(z), 0.0,
        0.0, 0.0, 0.0, 1.0,
    )


def rotation_x(angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return (
        1.0, 0.0, 0.0, 0.0,
        0.0, c, -s, 0.0,
        0.0, s, c, 0.0,
        0.0, 0.0, 0.0, 1.0,
    )


def rotation_y(angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return (
        c, 0.0, s, 0.0,
        0.0, 1.0, 0.0, 0.0,
        -s, 0.0, c, 0.0,
        0.0, 0.0, 0.0, 1.0,
    )


def rotation_z(angle):
    c = math.cos(angle)
    s = math.sin(angle)
    return (
        c, -s, 0.0, 0.0,
        s, c, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    )


def transform(vertex, matrix):
    x, y, z = vertex
    tx = matrix[0] * x + matrix[1] * y + matrix[2] * z + matrix[3]
    ty = matrix[4] * x + matrix[5] * y + matrix[6] * z + matrix[7]
    tz = matrix[8] * x + matrix[9] * y + matrix[10] * z + matrix[11]
    tw = matrix[12] * x + matrix[13] * y + matrix[14] * z + matrix[15]
    if tw != 0.0 and tw != 1.0:
        return (tx / tw, ty / tw, tz / tw)
    return (tx, ty, tz)


def focal_length(width=SCREEN_WIDTH, fov=70.0):
    return (width * 0.5) / math.tan(math.radians(fov) * 0.5)


def project(vertex, focal=None, center=None, near=0.1):
    """Perspective-project a view-space vertex to screen coordinates."""
    x, y, z = vertex
    if z <= near:
        return None
    if focal is None:
        focal = focal_length()
    if center is None:
        center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    return (
        int(center[0] + x * focal / z),
        int(center[1] - y * focal / z),
        z,
    )


def rgb565(r, g, b):
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)


def shade_rgb565(color, amount):
    amount = max(0.0, min(1.0, float(amount)))
    r = int(((color >> 11) & 31) * amount)
    g = int(((color >> 5) & 63) * amount)
    b = int((color & 31) * amount)
    return (r << 11) | (g << 5) | b


def prepare_triangles(vertices, faces, model=None, position=(0.0, 0.0, 0.0),
                      focal=None, center=None, near=0.1, cull=True,
                      ambient=0.28, light_dir=(-0.35, -0.45, -1.0),
                      default_color=0xffff):
    """Transform, cull, light, project and depth-sort a triangle mesh.

    Faces are ``(i0, i1, i2)`` or ``(i0, i1, i2, rgb565_color)``.  The return
    value is painter-sorted from far to near and can be rendered directly with
    ``gint.dtriangle``.
    """
    if model is None:
        model = identity()
    if focal is None:
        focal = focal_length()
    if center is None:
        center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

    px, py, pz = position
    transformed = []
    for vertex in vertices:
        value = transform(vertex, model)
        transformed.append((value[0] + px, value[1] + py, value[2] + pz))

    light = normalize(light_dir)
    triangles = []
    for face in faces:
        a = transformed[face[0]]
        b = transformed[face[1]]
        c = transformed[face[2]]

        # Milestone 1 keeps clipping cheap: triangles crossing the near plane
        # are skipped rather than split. This avoids bad perspective divides.
        if a[2] <= near or b[2] <= near or c[2] <= near:
            continue

        normal = cross(sub(b, a), sub(c, a))
        normal_length = length(normal)
        if normal_length == 0:
            continue

        # The camera is at the origin looking along +Z. Outward-wound faces
        # point toward the camera when normal dot vertex is negative.
        if cull and dot(normal, a) >= 0:
            continue

        pa = project(a, focal, center, near)
        pb = project(b, focal, center, near)
        pc = project(c, focal, center, near)
        if pa is None or pb is None or pc is None:
            continue

        base_color = face[3] if len(face) > 3 else default_color
        unit_normal = scale(normal, 1.0 / normal_length)
        diffuse = dot(unit_normal, light)
        if diffuse < 0.0:
            diffuse = 0.0
        intensity = ambient + (1.0 - ambient) * diffuse
        color = shade_rgb565(base_color, intensity)
        depth = (a[2] + b[2] + c[2]) / 3.0

        triangles.append((
            depth,
            pa[0], pa[1], pb[0], pb[1], pc[0], pc[1], color,
        ))

    triangles.sort(key=lambda triangle: triangle[0], reverse=True)
    return triangles


def cube(size=2.0):
    """Return vertices/faces for a colored, outward-wound cube."""
    h = float(size) * 0.5
    vertices = (
        (-h, -h, -h), (h, -h, -h), (h, h, -h), (-h, h, -h),
        (-h, -h, h), (h, -h, h), (h, h, h), (-h, h, h),
    )

    red = rgb565(235, 76, 76)
    orange = rgb565(245, 155, 55)
    green = rgb565(70, 205, 105)
    cyan = rgb565(55, 190, 220)
    blue = rgb565(70, 100, 235)
    violet = rgb565(175, 90, 225)

    faces = (
        (0, 2, 1, red), (0, 3, 2, red),          # front (-Z)
        (4, 5, 6, orange), (4, 6, 7, orange),     # back (+Z)
        (0, 4, 7, green), (0, 7, 3, green),       # left (-X)
        (1, 2, 6, cyan), (1, 6, 5, cyan),         # right (+X)
        (3, 7, 6, blue), (3, 6, 2, blue),         # top (+Y)
        (0, 1, 5, violet), (0, 5, 4, violet),     # bottom (-Y)
    )
    return vertices, faces


class Renderer:
    """Small fx-CG50 renderer backed by the native gint triangle rasterizer."""

    def __init__(self, width=SCREEN_WIDTH, height=SCREEN_HEIGHT, fov=70.0,
                 near=0.1, background=0x0000):
        import gint
        self.gint = gint
        self.width = int(width)
        self.height = int(height)
        self.center = (self.width // 2, self.height // 2)
        self.fov = float(fov)
        self.focal = focal_length(self.width, self.fov)
        self.near = float(near)
        self.background = int(background)

    def clear(self, color=None):
        if color is None:
            color = self.background
        self.gint.dclear(int(color))

    def draw_mesh(self, vertices, faces, model=None,
                  position=(0.0, 0.0, 0.0), cull=True, wireframe=False,
                  ambient=0.28, light_dir=(-0.35, -0.45, -1.0),
                  default_color=0xffff, wire_color=0xffff):
        triangles = prepare_triangles(
            vertices, faces, model, position, self.focal, self.center,
            self.near, cull, ambient, light_dir, default_color)

        for triangle in triangles:
            _, x0, y0, x1, y1, x2, y2, color = triangle
            self.gint.dtriangle(x0, y0, x1, y1, x2, y2, color)
            if wireframe:
                self.gint.dline(x0, y0, x1, y1, wire_color)
                self.gint.dline(x1, y1, x2, y2, wire_color)
                self.gint.dline(x2, y2, x0, y0, wire_color)
        return len(triangles)

    def present(self):
        self.gint.dupdate()
