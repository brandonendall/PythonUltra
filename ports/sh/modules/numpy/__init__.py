"""Calculator-sized NumPy compatibility subset for PythonUltra / fx-CG50.

The goal is useful game, geometry and classroom compatibility without carrying
CPython NumPy's native extension footprint.  Arrays are pure Python and small
matrices are intentionally optimized for correctness and memory simplicity.
"""

import math as _math

__version__ = "0.2.0-cg50"
pi = _math.pi
e = _math.e


def _product(shape):
    total = 1
    for value in shape:
        total *= int(value)
    return total


def _normalize_shape(shape):
    if isinstance(shape, int):
        return (int(shape),)
    return tuple(int(value) for value in shape)


def _infer_shape(value):
    if isinstance(value, ndarray):
        return value.shape
    if not isinstance(value, (list, tuple)):
        return ()
    if not value:
        return (0,)
    child = _infer_shape(value[0])
    for item in value[1:]:
        if _infer_shape(item) != child:
            raise ValueError("ragged arrays are not supported")
    return (len(value),) + child


def _flatten(value, output):
    if isinstance(value, ndarray):
        output.extend(value._data)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _flatten(item, output)
    else:
        output.append(value)


def _unflatten(data, shape, offset=0):
    if len(shape) == 0:
        return data[offset], offset + 1
    if len(shape) == 1:
        end = offset + shape[0]
        return list(data[offset:end]), end
    result = []
    for _ in range(shape[0]):
        item, offset = _unflatten(data, shape[1:], offset)
        result.append(item)
    return result, offset


class ndarray:
    def __init__(self, value, shape=None, dtype=None, _flat=False):
        self.dtype = dtype
        if _flat:
            self._data = list(value)
            self.shape = _normalize_shape(shape)
        elif isinstance(value, ndarray):
            self._data = list(value._data)
            self.shape = value.shape if shape is None else _normalize_shape(shape)
            if dtype is None:
                self.dtype = value.dtype
        else:
            inferred = _infer_shape(value)
            self._data = []
            _flatten(value, self._data)
            self.shape = inferred if shape is None else _normalize_shape(shape)
        if _product(self.shape) != len(self._data):
            raise ValueError("array size does not match shape")

    @property
    def size(self):
        return len(self._data)

    @property
    def ndim(self):
        return len(self.shape)

    def __len__(self):
        return self.shape[0] if self.shape else 0

    def __iter__(self):
        if self.ndim <= 1:
            return iter(self._data)
        stride = _product(self.shape[1:])
        rows = []
        for index in range(self.shape[0]):
            start = index * stride
            rows.append(ndarray(self._data[start:start + stride], self.shape[1:], self.dtype, True))
        return iter(rows)

    def __repr__(self):
        return "array(%r)" % self.tolist()

    def _flat_index(self, index):
        if not isinstance(index, tuple):
            index = (index,)
        if len(index) != self.ndim:
            raise IndexError("incorrect number of indices")
        offset = 0
        stride = self.size
        for axis, item in enumerate(index):
            dim = self.shape[axis]
            stride //= dim
            item = int(item)
            if item < 0:
                item += dim
            if item < 0 or item >= dim:
                raise IndexError("array index out of range")
            offset += item * stride
        return offset

    def __getitem__(self, index):
        if isinstance(index, slice):
            if self.ndim != 1:
                raise TypeError("slicing is supported for 1-D arrays")
            return ndarray(self._data[index], dtype=self.dtype)
        if isinstance(index, tuple) or self.ndim <= 1:
            return self._data[self._flat_index(index)]
        dim = self.shape[0]
        index = int(index)
        if index < 0:
            index += dim
        if index < 0 or index >= dim:
            raise IndexError("array index out of range")
        stride = _product(self.shape[1:])
        start = index * stride
        return ndarray(self._data[start:start + stride], self.shape[1:], self.dtype, True)

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            if self.ndim != 1:
                raise TypeError("slicing is supported for 1-D arrays")
            replacement = value._data if isinstance(value, ndarray) else list(value)
            self._data[index] = replacement
            self.shape = (len(self._data),)
            return
        self._data[self._flat_index(index)] = value

    def tolist(self):
        result, _ = _unflatten(self._data, self.shape)
        return result

    def copy(self):
        return ndarray(self._data, self.shape, self.dtype, True)

    def flatten(self):
        return ndarray(self._data, (self.size,), self.dtype, True)

    def reshape(self, *shape):
        if len(shape) == 1 and isinstance(shape[0], (tuple, list)):
            shape = tuple(shape[0])
        shape = list(int(value) for value in shape)
        missing = None
        known = 1
        for index, dim in enumerate(shape):
            if dim == -1:
                if missing is not None:
                    raise ValueError("only one unknown dimension is allowed")
                missing = index
            else:
                known *= dim
        if missing is not None:
            if known == 0 or self.size % known:
                raise ValueError("cannot infer reshape dimension")
            shape[missing] = self.size // known
        if _product(shape) != self.size:
            raise ValueError("cannot reshape array")
        return ndarray(self._data, tuple(shape), self.dtype, True)

    def astype(self, converter):
        return ndarray([converter(value) for value in self._data], self.shape, converter, True)

    def _binary(self, other, operation):
        if isinstance(other, ndarray):
            if self.shape != other.shape:
                raise ValueError("array shapes must match")
            values = [operation(a, b) for a, b in zip(self._data, other._data)]
        else:
            values = [operation(a, other) for a in self._data]
        return ndarray(values, self.shape, self.dtype, True)

    def __add__(self, other):
        return self._binary(other, lambda a, b: a + b)

    __radd__ = __add__

    def __sub__(self, other):
        return self._binary(other, lambda a, b: a - b)

    def __rsub__(self, other):
        return ndarray([other - value for value in self._data], self.shape, self.dtype, True)

    def __mul__(self, other):
        return self._binary(other, lambda a, b: a * b)

    __rmul__ = __mul__

    def __truediv__(self, other):
        return self._binary(other, lambda a, b: a / b)

    def __rtruediv__(self, other):
        return ndarray([other / value for value in self._data], self.shape, self.dtype, True)

    def __neg__(self):
        return ndarray([-value for value in self._data], self.shape, self.dtype, True)

    def sum(self):
        total = 0
        for value in self._data:
            total += value
        return total

    def mean(self):
        return self.sum() / self.size if self.size else 0

    def min(self):
        return min(self._data)

    def max(self):
        return max(self._data)

    @property
    def T(self):
        return transpose(self)


class matrix(ndarray):
    """Small 2-D matrix type compatible with the common ``numpy.matrix`` API.

    Unlike ndarray, ``*`` performs matrix multiplication when the other operand
    is an array/matrix.  Scalar multiplication remains element-wise.
    """

    def __init__(self, value, dtype=None, copy=True, shape=None, _flat=False):
        if _flat:
            final_shape = _normalize_shape(shape)
            if len(final_shape) == 1:
                final_shape = (1, final_shape[0])
            if len(final_shape) != 2:
                raise ValueError("matrix must be 2-dimensional")
            ndarray.__init__(self, value, final_shape, dtype, True)
            return

        if isinstance(value, ndarray):
            data = list(value._data) if copy else value._data
            final_shape = value.shape
            if len(final_shape) == 1:
                final_shape = (1, final_shape[0])
            elif len(final_shape) == 0:
                final_shape = (1, 1)
            if len(final_shape) != 2:
                raise ValueError("matrix must be 2-dimensional")
            ndarray.__init__(self, data, final_shape, dtype if dtype is not None else value.dtype, True)
        else:
            inferred = _infer_shape(value)
            if len(inferred) == 0:
                value = [[value]]
            elif len(inferred) == 1:
                value = [list(value)]
            elif len(inferred) != 2:
                raise ValueError("matrix must be 2-dimensional")
            ndarray.__init__(self, value, dtype=dtype)

    def __repr__(self):
        return "matrix(%r)" % self.tolist()

    def copy(self):
        return matrix(self._data, self.dtype, True, self.shape, True)

    def _binary(self, other, operation):
        result = ndarray._binary(self, other, operation)
        return matrix(result)

    def __rsub__(self, other):
        return matrix([other - value for value in self._data], self.dtype, True, self.shape, True)

    def __mul__(self, other):
        if isinstance(other, ndarray):
            result = matmul(self, other)
            return matrix(result) if isinstance(result, ndarray) else result
        return self._binary(other, lambda a, b: a * b)

    def __rmul__(self, other):
        if isinstance(other, ndarray):
            result = matmul(other, self)
            return matrix(result) if isinstance(result, ndarray) else result
        return self._binary(other, lambda a, b: b * a)

    def __matmul__(self, other):
        result = matmul(self, other)
        return matrix(result) if isinstance(result, ndarray) else result

    def __rmatmul__(self, other):
        result = matmul(other, self)
        return matrix(result) if isinstance(result, ndarray) else result

    def __pow__(self, exponent):
        exponent = int(exponent)
        if self.shape[0] != self.shape[1]:
            raise ValueError("matrix power requires a square matrix")
        if exponent == -1:
            return self.I
        if exponent < 0:
            return self.I ** (-exponent)
        result = matrix(identity(self.shape[0], dtype=self.dtype))
        base = self.copy()
        while exponent:
            if exponent & 1:
                result = result * base
            exponent >>= 1
            if exponent:
                base = base * base
        return result

    def reshape(self, *shape):
        if len(shape) == 1 and isinstance(shape[0], (tuple, list)):
            shape = tuple(shape[0])
        if len(shape) == 1:
            shape = (1, int(shape[0]))
        if len(shape) != 2:
            raise ValueError("matrix must remain 2-dimensional")
        result = ndarray.reshape(self, *shape)
        return matrix(result)

    def flatten(self):
        return matrix(self._data, self.dtype, True, (1, self.size), True)

    def transpose(self):
        rows, cols = self.shape
        output = []
        for col in range(cols):
            for row in range(rows):
                output.append(self._data[row * cols + col])
        return matrix(output, self.dtype, True, (cols, rows), True)

    @property
    def T(self):
        return self.transpose()

    @property
    def H(self):
        # PythonUltra's compact numeric layer currently stores real numbers.
        return self.transpose()

    @property
    def I(self):
        rows, cols = self.shape
        if rows != cols:
            raise ValueError("inverse requires a square matrix")
        n = rows
        work = []
        for row in range(n):
            values = []
            for col in range(n):
                values.append(float(self._data[row * n + col]))
            for col in range(n):
                values.append(1.0 if row == col else 0.0)
            work.append(values)

        width = n * 2
        for pivot_col in range(n):
            pivot_row = pivot_col
            pivot_size = abs(work[pivot_row][pivot_col])
            for candidate in range(pivot_col + 1, n):
                candidate_size = abs(work[candidate][pivot_col])
                if candidate_size > pivot_size:
                    pivot_row = candidate
                    pivot_size = candidate_size
            if pivot_size == 0:
                raise ValueError("singular matrix")
            if pivot_row != pivot_col:
                work[pivot_col], work[pivot_row] = work[pivot_row], work[pivot_col]

            pivot = work[pivot_col][pivot_col]
            for col in range(width):
                work[pivot_col][col] /= pivot

            for row in range(n):
                if row == pivot_col:
                    continue
                factor = work[row][pivot_col]
                if factor == 0:
                    continue
                for col in range(width):
                    work[row][col] -= factor * work[pivot_col][col]

        inverse = []
        for row in range(n):
            inverse.extend(work[row][n:])
        return matrix(inverse, float, True, (n, n), True)

    @property
    def A(self):
        return ndarray(self._data, self.shape, self.dtype, True)

    @property
    def A1(self):
        return ndarray(self._data, (self.size,), self.dtype, True)

    def getA(self):
        return self.A

    def getA1(self):
        return self.A1

    def getT(self):
        return self.T

    def getH(self):
        return self.H

    def getI(self):
        return self.I


mat = matrix


def array(value, dtype=None):
    return ndarray(value, dtype=dtype)


def asarray(value, dtype=None):
    if isinstance(value, ndarray) and (dtype is None or dtype == value.dtype):
        return value
    return ndarray(value, dtype=dtype)


def asmatrix(value, dtype=None):
    return matrix(value, dtype=dtype, copy=False)


def zeros(shape, dtype=float):
    shape = _normalize_shape(shape)
    return ndarray([dtype(0)] * _product(shape), shape, dtype, True)


def ones(shape, dtype=float):
    shape = _normalize_shape(shape)
    return ndarray([dtype(1)] * _product(shape), shape, dtype, True)


def full(shape, value, dtype=None):
    shape = _normalize_shape(shape)
    if dtype is not None:
        value = dtype(value)
    return ndarray([value] * _product(shape), shape, dtype, True)


def identity(n, dtype=float):
    n = int(n)
    values = [dtype(0)] * (n * n)
    for index in range(n):
        values[index * n + index] = dtype(1)
    return ndarray(values, (n, n), dtype, True)


def eye(n, m=None, k=0, dtype=float):
    n = int(n)
    m = n if m is None else int(m)
    values = [dtype(0)] * (n * m)
    for row in range(n):
        col = row + int(k)
        if 0 <= col < m:
            values[row * m + col] = dtype(1)
    return ndarray(values, (n, m), dtype, True)


def arange(start, stop=None, step=1, dtype=None):
    if stop is None:
        start, stop = 0, start
    if step == 0:
        raise ValueError("step must not be zero")
    values = []
    current = start
    if step > 0:
        while current < stop:
            values.append(dtype(current) if dtype else current)
            current += step
    else:
        while current > stop:
            values.append(dtype(current) if dtype else current)
            current += step
    return ndarray(values, dtype=dtype)


def linspace(start, stop, num=50):
    num = int(num)
    if num <= 0:
        return ndarray([])
    if num == 1:
        return ndarray([float(start)])
    step = (stop - start) / (num - 1)
    return ndarray([start + step * index for index in range(num)])


def reshape(value, newshape):
    return asarray(value).reshape(newshape)


def transpose(value):
    value = asarray(value)
    if value.ndim <= 1:
        return value.copy()
    if value.ndim != 2:
        raise NotImplementedError("transpose currently supports 1-D and 2-D arrays")
    rows, cols = value.shape
    output = []
    for col in range(cols):
        for row in range(rows):
            output.append(value._data[row * cols + col])
    result = ndarray(output, (cols, rows), value.dtype, True)
    return matrix(result) if isinstance(value, matrix) else result


def concatenate(values):
    output = []
    for value in values:
        output.extend(asarray(value).flatten()._data)
    return ndarray(output)


def dot(a, b):
    a = asarray(a)
    b = asarray(b)
    if a.ndim == 1 and b.ndim == 1:
        if a.size != b.size:
            raise ValueError("vectors must have the same length")
        total = 0
        for x, y in zip(a._data, b._data):
            total += x * y
        return total
    return matmul(a, b)


def matmul(a, b):
    a_matrix = isinstance(a, matrix)
    b_matrix = isinstance(b, matrix)
    a = asarray(a)
    b = asarray(b)

    if a.ndim == 1 and b.ndim == 1:
        if a.size != b.size:
            raise ValueError("vectors must have the same length")
        total = 0
        for x, y in zip(a._data, b._data):
            total += x * y
        return total

    if a.ndim == 2 and b.ndim == 1:
        rows, cols = a.shape
        if cols != b.size:
            raise ValueError("shapes are not aligned")
        result = []
        for row in range(rows):
            total = 0
            start = row * cols
            for col in range(cols):
                total += a._data[start + col] * b._data[col]
            result.append(total)
        output = ndarray(result)
        return matrix(output) if a_matrix else output

    if a.ndim == 1 and b.ndim == 2:
        rows, cols = b.shape
        if a.size != rows:
            raise ValueError("shapes are not aligned")
        result = []
        for col in range(cols):
            total = 0
            for row in range(rows):
                total += a._data[row] * b._data[row * cols + col]
            result.append(total)
        output = ndarray(result)
        return matrix(output) if b_matrix else output

    if a.ndim == 2 and b.ndim == 2:
        a_rows, a_cols = a.shape
        b_rows, b_cols = b.shape
        if a_cols != b_rows:
            raise ValueError("shapes are not aligned")
        result = []
        for row in range(a_rows):
            for col in range(b_cols):
                total = 0
                for index in range(a_cols):
                    total += a._data[row * a_cols + index] * b._data[index * b_cols + col]
                result.append(total)
        output = ndarray(result, (a_rows, b_cols), _flat=True)
        return matrix(output) if (a_matrix or b_matrix) else output

    raise NotImplementedError("matmul currently supports 1-D and 2-D arrays")


def _unary(value, function):
    if isinstance(value, ndarray):
        output = ndarray([function(item) for item in value._data], value.shape, value.dtype, True)
        return matrix(output) if isinstance(value, matrix) else output
    return function(value)


def sqrt(value):
    return _unary(value, _math.sqrt)


def sin(value):
    return _unary(value, _math.sin)


def cos(value):
    return _unary(value, _math.cos)


def tan(value):
    return _unary(value, _math.tan)


def abs(value):
    return _unary(value, lambda item: -item if item < 0 else item)


def sum(value):
    if isinstance(value, ndarray):
        return value.sum()
    total = 0
    for item in value:
        total += item
    return total


def mean(value):
    return asarray(value).mean()


def amin(value):
    return asarray(value).min()


def amax(value):
    return asarray(value).max()


float32 = float
float64 = float
int8 = int
int16 = int
int32 = int
int64 = int
uint8 = int
uint16 = int
uint32 = int
bool_ = bool
