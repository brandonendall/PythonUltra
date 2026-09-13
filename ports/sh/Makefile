CROSS_COMPILE := sh-elf-

# The compact pygame layer currently targets the color fx-CG50 build. Point
# MPY_LIB_DIR at the source tree because this manifest uses no micropython-lib
# packages; mkrules only requires a directory containing README.md.
ifeq ($(TARGETCASIO),"FXCG50")
    MPY_LIB_DIR := $(TOP)
    FROZEN_MANIFEST := $(TOP)/ports/sh/manifest.py
endif

include $(TOP)/py/py.mk
include $(TOP)/extmod/extmod.mk

CFLAGS += -m4-nofpu -mb -Wa,--dsp -flto=auto -fstrict-volatile-bitfields \
          -I. -I$(TOP)/ports/sh -I$(BUILD) -I$(TOP) \
          $(SH_CFLAGS) -Os -Wall -Wextra -Wno-unused-parameter
LIBS += -nostdlib -Wl,--no-warn-rwx-segments $(SH_LDFLAGS) -Wl,-Map=build/map
LDFLAGS := -Wno-lto-type-mismatch

# Source files
SRC_C = \
    ports/sh/main.c \
    ports/sh/console.c \
    ports/sh/debug.c \
    ports/sh/fdfile.c \
    ports/sh/keymap.c \
    ports/sh/libc_compat.c \
    ports/sh/pathutil.c \
    ports/sh/modcasioplot.c \
    ports/sh/modchecksum.c \
    ports/sh/modctypes.c \
    ports/sh/modgint.c \
    ports/sh/modnumpy.c \
    ports/sh/modos.c \
    ports/sh/mphalport.c \
    ports/sh/objgintimage.c \
    ports/sh/objgintfont.c \
    ports/sh/pyexec.c \
    ports/sh/resources.c \
    ports/sh/stredit.c \
    ports/sh/widget_shell.c \
    shared/runtime/gchelper_generic.c \
    shared/runtime/stdout_helpers.c \
    shared/runtime/interrupt_char.c \

# Prevent GCC from rewriting these fallback libc implementations as calls to
# the same unavailable target symbols.
$(BUILD)/ports/sh/libc_compat.o: CFLAGS += $(CFLAGS_BUILTIN)

SRC_QSTR += \
    ports/sh/fdfile.c \
    ports/sh/main.c \
    ports/sh/modcasioplot.c \
    ports/sh/modchecksum.c \
    ports/sh/modctypes.c \
    ports/sh/modgint.c \
    ports/sh/modnumpy.c \
    ports/sh/modos.c \
    ports/sh/objgintimage.c \
    ports/sh/objgintfont.c \
    ports/sh/pyexec.c \

# The upstream project normally has release tags available to git describe.
# Fork/import workflows may intentionally omit upstream Git history, so always
# provide a usable build identifier instead of allowing git describe to fail.
GIT_DESCRIBE := $(shell git describe --tags --always 2>/dev/null || git rev-parse --short HEAD)

ifeq ($(shell [[ x"$$(git rev-parse HEAD)" == x"$$(git rev-parse main 2>/dev/null)" ]] \
              && [[ -z "$$(git status -uno --porcelain)" ]] \
              && echo y),y)
    BUILDTYPE := RELEASE
    BUILDTYPE_STR := $(shell echo -e "\x1b[32;1mRelease build\x1b[0m")
    PE_BUILD := $(GIT_DESCRIBE)
else
    BUILDTYPE := DEV
    BUILDTYPE_STR := $(shell echo -e "\x1b[33;1mDevelopment build\x1b[0m")
    PE_BUILD := $(shell git rev-parse --short HEAD)
endif

CFLAGS += -DPE_BUILD='"$(PE_BUILD)"'

ifeq ($(TARGETCASIO),"FXCG50")
    PE_NAME := fx-CG

    SRC_C += \
        ports/sh/numworks/modkandinsky.c \
        ports/sh/numworks/modion.c \

    SRC_ASM += \
        ports/sh/numworks/syscalls.S \

    SRC_QSTR += \
        ports/sh/numworks/modkandinsky.c \
        ports/sh/numworks/modion.c \

else ifeq ($(TARGETCASIO),"FX9860G")
    PE_NAME := fx-9860G III
    PE_EXT_NUMWORKS := 0
else ifeq ($(TARGETCASIO),"FXCP")
    PE_NAME := fx-CP 400
    PE_EXT_NUMWORKS := 0
endif

HEADER := PythonUltra for $(PE_NAME)
HEADER := $(shell echo -e "\x1b[4;1m$(HEADER)\x1b[0m")
HEADER := $(HEADER) - $(BUILDTYPE_STR)
HASHES := \#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#
$(info $(HASHES) $(HEADER) $(HASHES))

ASSETS_O := $(SH_ASSETS:%=$(BUILD)/sh_assets/%.o)

OBJ = $(PY_O) $(ASSETS_O) \
      $(addprefix $(BUILD)/, $(SRC_C:.c=.o)) \
      $(addprefix $(BUILD)/, $(SRC_ASM:.S=.o))

$(BUILD)/firmware.bin: $(BUILD)/firmware.elf
	$(Q)$(CC:gcc=objcopy) -O binary -R .bss -R .gint_bss $< $@

$(BUILD)/firmware.elf: $(OBJ)
	$(ECHO) "LINK $@"
	$(Q)$(CC) $(LDFLAGS) -o $@ $^ $(LIBS)
	$(Q)$(SIZE) $@

$(BUILD)/sh_assets/%.o: % $(SH_METADATA)
	$(Q)mkdir -p $(dir $@)
	$(Q)fxconv --toolchain=$(CROSS_COMPILE:%-=%) $(SH_CONVFLAGS) $< -o $@

ARCHIVE := PythonUltra-$(GIT_DESCRIBE).zip

# Weird rules calling back to fxcg50 and fx9860g3, both of which include this
release:
	$(MAKE) -C ../fx9860g3
	$(MAKE) -C ../fxcg50
	$(MAKE) -C ../fxcp
	cd ../sh && zip "$(ARCHIVE)" -j ../fx9860g3/PythonEx.g1a ../fxcg50/PythonUltra.g3a ../fxcp/PythonExtra-hh2.bin
	cd ../sh && zip "$(ARCHIVE)" -r examples modules

.PHONY: release
.PRECIOUS: $(ARCHIVE)

include $(TOP)/py/mkrules.mk
