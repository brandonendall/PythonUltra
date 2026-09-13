include ../../py/mkenv.mk

SH_CFLAGS := -DFXCG50
TARGETCASIO := "FXCG50"
SH_LDFLAGS := -T fxcg50.ld -ljustui-cg -lm -lgint-cg -lc -lgint-cg -lgcc

JETBRAINS_FONTS := font_jb_9.png font_jb_13.png font_jb_19.png
SH_ASSETS := img_modifier_states.png font_9.png font_13.png font_19.png $(JETBRAINS_FONTS) PoliceNW
SH_METADATA := fxconv-metadata.txt
SH_CONVFLAGS := --cg

# Generate fixed-width calculator raster fonts from the pinned official
# JetBrains Mono OFL source. The source TTF is not shipped as an artifact.
$(JETBRAINS_FONTS) &: prepare_jetbrains_mono.py JetBrainsMono-OFL.txt
	python3 prepare_jetbrains_mono.py

.PHONY: pythonultra-runtime-fixes
pythonultra-runtime-fixes:
ifneq ($(PYTHONULTRA_RUNTIME_PREPARED),1)
	python3 ../sh/apply_runtime_fixes.py
	python3 ../sh/apply_pythonultra_features.py
	python3 ../sh/apply_pythonultra_ui2.py
	python3 ../sh/apply_pythonultra_permissions.py
	python3 ../sh/apply_pythonultra_ui3_compat.py
	python3 ../sh/apply_pythonultra_symbols.py
	python3 ../../tools/pythonultra_docs.py --output ../../build-module-docs/reference --runtime-header ../sh/module_docs.h
endif
	python3 -m py_compile \
		../sh/modules/pythonultra/__init__.py \
		../sh/modules/pyeditor/__init__.py \
		../sh/modules/pyfiles/__init__.py \
		../sh/modules/pyperm/__init__.py \
		../sh/modules/pyterm/__init__.py \
		../sh/modules/zipfile/__init__.py
	python3 ../../tests/ports/sh/pygame_compat.py
	python3 ../../tests/ports/sh/pygame_cg50_regression.py
	python3 ../../tests/ports/sh/pygame_colorkey.py
	python3 ../../tests/ports/sh/numpy_compat.py
	python3 ../../tests/ports/sh/py3d_compat.py
	python3 ../../tests/ports/sh/pyeditor_regression.py
	python3 ../../tests/ports/sh/zipfile_roundtrip.py
	python3 ../../tests/ports/sh/pyterm_startup.py
	python3 ../../tests/ports/sh/fdfile_seek.py
	python3 ../../tests/ports/sh/catalog_ui.py
	python3 ../../tests/ports/sh/file_info_timestamp.py
	python3 ../../tests/ports/sh/pythonultra_features.py

# The frozen Python modules must be patched and tested before firmware.bin is generated.
$(BUILD)/firmware.bin: pythonultra-runtime-fixes

all: PythonUltra.g3a

ICONS_RELEASE := --icon-uns=icon-uns.png --icon-sel=icon-sel.png
ICONS_DEV := --icon-uns=icon-uns-dev.png --icon-sel=icon-sel-dev.png

PythonUltra.g3a: $(BUILD)/firmware.bin
	fxgxa --g3a -n PythonUltra $(ICONS_$(BUILDTYPE)) $< -o $@

send: all
	fxlink -sw PythonUltra.g3a

include $(TOP)/ports/sh/Makefile
