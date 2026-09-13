"""Lightweight pygame.math compatibility for PythonUltra on fx-CG50.

The implementation is intentionally compact and allocation-conscious. It
covers the vector operations most useful to 2D/3D calculator games without
pulling in desktop pygame or NumPy.
"""

import math as _math


_EPSILON = 1e-12


def _number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        raise TypeError("vector components must be numbers")


def _components(value, size):
    if isinstance(value, _VectorBase):
        values = list(value)
    else:
        try:
            values = list(value)
        except TypeError:
            raise TypeError("expected a vector or sequence")
    if len(values) != size:
        raise ValueError("expected %d components" % size)
    return [_number(item) for item in values]


class _VectorBase:
    _size = 0
    __slots__ = ("_v",)

    def __len__(self):
        return self._size

    def __iter__(self):
        return iter(self._v)

    def __getitem__(self, index):
        return self._v[index]

    def __setitem__(self, index, value):
        self._v[index] = _number(value)

    def __repr__(self):
        return "%s(%s)" % (
            self.__class__.__name__,
            ", ".join(str(value) for value in self._v),
        )

    __str__ = __repr__

    def __eq__(self, other):
        try:
            values = _components(other, self._size)
        except (TypeError, ValueError):
            return False
        return all(abs(a - b) <= _EPSILON for a, b in zip(self._v, values))

    def __add__(self, other):
        values = _components(other, self._size)
        return self.__class__([a + b for a, b in zip(self._v, values)])

    __radd__ = __add__

    def __sub__(self, other):
        values = _components(other, self._size)
        return self.__class__([a - b for a, b in zip(self._v, values)])

    def __rsub__(self, other):
        values = _components(other, self._size)
        return self.__class__([a - b for a, b in zip(values, self._v)])

    def __neg__(self):
        return self.__class__([-value for value in self._v])

    def __pos__(self):
        return self.copy()

    def __mul__(self, scalar):
        scalar = _number(scalar)
        return self.__class__([value * scalar for value in self._v])

    __rmul__ = __mul__

    def __truediv__(self, scalar):
        scalar = _number(scalar)
        if scalar == 0:
            raise ZeroDivisionError("division by zero")
        return self.__class__([value / scalar for value in self._v])

    def __iadd__(self, other):
        values = _components(other, self._size)
        for index in range(self._size):
            self._v[index] += values[index]
        return self

    def __isub__(self, other):
        values = _components(other, self._size)
        for index in range(self._size):
            self._v[index] -= values[index]
        return self

    def __imul__(self, scalar):
        scalar = _number(scalar)
        for index in range(self._size):
            self._v[index] *= scalar
        return self

    def __itruediv__(self, scalar):
        scalar = _number(scalar)
        if scalar == 0:
            raise ZeroDivisionError("division by zero")
        for index in range(self._size):
            self._v[index] /= scalar
        return self

    def copy(self):
        return self.__class__(self._v)

    def update(self, *values):
        if len(values) == 1:
            values = _components(values[0], self._size)
        elif len(values) == self._size:
            values = [_number(value) for value in values]
        else:
            raise ValueError("expected %d components" % self._size)
        self._v[:] = values

    def length_squared(self):
        return sum(value * value for value in self._v)

    def length(self):
        return _math.sqrt(self.length_squared())

    magnitude = length
    magnitude_squared = length_squared

    def dot(self, other):
        values = _components(other, self._size)
        return sum(a * b for a, b in zip(self._v, values))

    def normalize(self):
        result = self.copy()
        result.normalize_ip()
        return result

    def normalize_ip(self):
        length = self.length()
        if length <= _EPSILON:
            raise ValueError("Can't normalize Vector of length Zero")
        for index in range(self._size):
            self._v[index] /= length

    def is_normalized(self):
        return abs(self.length_squared() - 1.0) <= 1e-6

    def scale_to_length(self, new_length):
        current = self.length()
        if current <= _EPSILON:
            raise ValueError("Cannot scale a vector with zero length")
        scale = _number(new_length) / current
        for index in range(self._size):
            self._v[index] *= scale

    def distance_squared_to(self, other):
        values = _components(other, self._size)
        return sum((a - b) * (a - b) for a, b in zip(self._v, values))

    def distance_to(self, other):
        return _math.sqrt(self.distance_squared_to(other))

    def lerp(self, other, amount):
        amount = _number(amount)
        if amount < 0.0 or amount > 1.0:
            raise ValueError("Argument 2 must be in range [0, 1]")
        values = _components(other, self._size)
        return self.__class__([
            a + (b - a) * amount for a, b in zip(self._v, values)
        ])


class Vector2(_VectorBase):
    """Two-component vector compatible with the core pygame.math.Vector2 API."""

    _size = 2

    def __init__(self, x=0.0, y=None):
        if y is None:
            if isinstance(x, (int, float)):
                self._v = [_number(x), 0.0]
            else:
                self._v = _components(x, 2)
        else:
            self._v = [_number(x), _number(y)]

    @property
    def x(self):
        return self._v[0]

    @x.setter
    def x(self, value):
        self._v[0] = _number(value)

    @property
    def y(self):
        return self._v[1]

    @y.setter
    def y(self, value):
        self._v[1] = _number(value)

    def cross(self, other):
        x, y = _components(other, 2)
        return self.x * y - self.y * x

    def angle_to(self, other):
        x, y = _components(other, 2)
        dot = self.x * x + self.y * y
        cross = self.x * y - self.y * x
        return _math.degrees(_math.atan2(cross, dot))

    def rotate(self, angle):
        radians = _math.radians(_number(angle))
        sine = _math.sin(radians)
        cosine = _math.cos(radians)
        return Vector2(
            self.x * cosine - self.y * sine,
            self.x * sine + self.y * cosine,
        )

    def rotate_ip(self, angle):
        result = self.rotate(angle)
        self._v[:] = result._v


class Vector3(_VectorBase):
    """Three-component vector for compact 3D game and geometry code."""

    _size = 3

    def __init__(self, x=0.0, y=None, z=None):
        if y is None and z is None:
            if isinstance(x, (int, float)):
                self._v = [_number(x), 0.0, 0.0]
            else:
                self._v = _components(x, 3)
        elif y is not None and z is not None:
            self._v = [_number(x), _number(y), _number(z)]
        else:
            raise ValueError("Vector3 requires 0, 1 sequence, or 3 components")

    @property
    def x(self):
        return self._v[0]

    @x.setter
    def x(self, value):
        self._v[0] = _number(value)

    @property
    def y(self):
        return self._v[1]

    @y.setter
    def y(self, value):
        self._v[1] = _number(value)

    @property
    def z(self):
        return self._v[2]

    @z.setter
    def z(self, value):
        self._v[2] = _number(value)

    def cross(self, other):
        x, y, z = _components(other, 3)
        return Vector3(
            self.y * z - self.z * y,
            self.z * x - self.x * z,
            self.x * y - self.y * x,
        )


__all__ = ("Vector2", "Vector3")
