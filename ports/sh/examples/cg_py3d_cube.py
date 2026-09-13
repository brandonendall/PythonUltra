"""PythonUltra py3d rotating-cube demo for the fx-CG50.

Copy this script to storage memory and run it from PythonUltra. Press EXIT to
leave. The demo uses the built-in py3d module and native gint.dtriangle().
"""

import time
import gint
from py3d import Renderer, compose, cube, rotation_x, rotation_y


vertices, faces = cube(2.2)
renderer = Renderer(background=0x0000)
angle_x = 0.0
angle_y = 0.0

while not gint.keydown(gint.KEY_EXIT):
    # Arrow keys add manual steering while the cube also rotates on its own.
    if gint.keydown(gint.KEY_LEFT):
        angle_y -= 0.045
    if gint.keydown(gint.KEY_RIGHT):
        angle_y += 0.045
    if gint.keydown(gint.KEY_UP):
        angle_x += 0.045
    if gint.keydown(gint.KEY_DOWN):
        angle_x -= 0.045

    angle_x += 0.012
    angle_y += 0.020
    model = compose(rotation_x(angle_x), rotation_y(angle_y))

    renderer.clear()
    drawn = renderer.draw_mesh(
        vertices,
        faces,
        model=model,
        position=(0.0, 0.0, 5.2),
        ambient=0.34,
    )

    gint.dtext(6, 5, 0xffff, "PY3D  %d TRI" % drawn)
    gint.dtext(6, 20, 0xffff, "ARROWS: ROTATE  EXIT: QUIT")
    renderer.present()
    time.sleep_ms(20)
