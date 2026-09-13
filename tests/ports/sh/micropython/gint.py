"""Tiny host-only gint stand-in for MicroPython compatibility smoke tests."""

KEY_F1 = 1001
KEY_F2 = 1002
KEY_F3 = 1003
KEY_F4 = 1004
KEY_F5 = 1005
KEY_F6 = 1006
KEY_SHIFT = 1007
KEY_OPTN = 1008
KEY_VARS = 1009
KEY_MENU = 1010
KEY_LEFT = 1011
KEY_UP = 1012
KEY_ALPHA = 1013
KEY_SQUARE = 1014
KEY_POWER = 1015
KEY_EXIT = 1016
KEY_DOWN = 1017
KEY_RIGHT = 1018
KEY_XOT = 1019
KEY_LOG = 1020
KEY_LN = 1021
KEY_SIN = 1022
KEY_COS = 1023
KEY_TAN = 1024
KEY_FRAC = 1025
KEY_FD = 1026
KEY_LEFTP = 1027
KEY_RIGHTP = 1028
KEY_COMMA = 1029
KEY_ARROW = 1030
KEY_7 = 1031
KEY_8 = 1032
KEY_9 = 1033
KEY_DEL = 1034
KEY_4 = 1035
KEY_5 = 1036
KEY_6 = 1037
KEY_MUL = 1038
KEY_DIV = 1039
KEY_1 = 1040
KEY_2 = 1041
KEY_3 = 1042
KEY_ADD = 1043
KEY_SUB = 1044
KEY_0 = 1045
KEY_DOT = 1046
KEY_EXP = 1047
KEY_NEG = 1048
KEY_EXE = 1049
KEY_ACON = 1050

KEYEV_NONE = 0
KEYEV_DOWN = 1
KEYEV_UP = 2
KEYEV_HOLD = 3
DWIDTH = 396
DHEIGHT = 224
C_NONE = -1


class _Image:
    def __init__(self, width, height, data):
        self.width = width
        self.height = height
        self.data = data


class _RawEvent:
    def __init__(self, event_type=KEYEV_NONE, key=0, shift=False, alpha=False):
        self.type = event_type
        self.key = key
        self.shift = shift
        self.alpha = alpha


def __init__():
    return None


def image_rgb565(width, height, data):
    return _Image(width, height, data)


def dclear(*args):
    pass


def dupdate(*args):
    pass


def drect(*args):
    pass


def drect_border(*args):
    pass


def dpixel(*args):
    pass


def dgetpixel(*args):
    return 0


def dline(*args):
    pass


def dcircle(*args):
    pass


def dellipse(*args):
    pass


def dpoly(*args):
    pass


def dtext(*args):
    pass


def dimage(*args):
    pass


def dsubimage(*args):
    pass


def keydown(key):
    return False


def clearevents():
    pass


def pollevent():
    return _RawEvent()
