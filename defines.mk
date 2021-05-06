
-include my-defines.mk

DIST=dist

ifeq ($(OS),Windows_NT)
	PLATFORM = $(OS)
	SEARCH_CMD = where   # Windows only
	#Specific search path to prevent concatenation of multiple paths
	SEARCH_WIN_DIR = "C:\Program Files\Python38"\:
else
	PLATFORM=$(shell uname)
	SEARCH_CMD = which   # Linux, MacOS
endif

#
# Handle multiple Python installs. What python are we using?
#

ifeq ($(PLATFORM), Linux)

TIME ?= $(shell $(SEARCH_CMD) time)
YESTERDAY = $(shell date --date yesterday +"%m/%d/%Y")
PYTHON2=$(shell $(SEARCH_CMD) python)
PIP3=$(shell $(SEARCH_CMD) pip3)
PYTHON3=$(shell $(SEARCH_CMD) python3)

else ifeq ($(PLATFORM), Darwin) # MacOS

TIME ?= time
YESTERDAY = $(shell date -v-1d +"%m/%d/%Y")
PYTHON2 = $(shell $(SEARCH_CMD) python)
PIP3 = $(shell $(SEARCH_CMD) pip3)
PYTHON3 = $(shell $(SEARCH_CMD) python3)

else ifeq ($(PLATFORM), Windows_NT) # Windows

#TIME ?= $(shell $(SEARCH_CMD) time)
YESTERDAY = $(shell powershell "(Get-Date).AddDays(-1).ToString('yyyy-MM-dd')" )
PYTHON2 = $(shell $(SEARCH_CMD) $(SEARCH_WIN_DIR)python)
PIP3 = $(shell $(SEARCH_CMD) pip3)
PYTHON3 = $(shell $(SEARCH_CMD) $(SEARCH_WIN_DIR)python)

else

TIME ?= $(shell $(SEARCH_CMD) time)
YESTERDAY = $(shell date -v-1d +"%m/%d/%Y")
PYTHON2 = $(shell $(SEARCH_CMD) python)
PIP3 = $(shell $(SEARCH_CMD) pip3)
PYTHON3 = $(shell $(SEARCH_CMD) python3)

endif

FLAKE8 ?= $(shell $(SEARCH_CMD) flake8)
PYINSTALLER ?= $(shell $(SEARCH_CMD) pyinstaller)

#PYTHON ?= ${PYTHON2}
PYTHON ?= $(PYTHON3)
PIP ?= $(PIP3)

#
# Install pip packages as user for devs and to system for pipeline runner
#
ifeq ($(USER), runner)
PIP_INSTALL_OPT ?=
else
PIP_INSTALL_OPT ?= --user
endif

ifeq ($(PYTHON),)
$(error Python not found)
endif
ifeq ($(PIP),)
$(error pip not found)
endif

#$(info  Test TIME is evaluated to $(TIME))
#$(info  Test PLATFORM is evaluated to $(PLATFORM))
#$(info  Test PYTHON3 is evaluated to $(PYTHON3))
#$(info  Test PIP3 is evaluated to $(PIP3))
#$(info  Test PIP_INSTALL_OPT is evaluated to $(PIP_INSTALL_OPT))
#$(info  Test YESTERDAY is evaluated to $(YESTERDAY))
#$(info  Test PYINSTALLER is evaluated to $(PYINSTALLER))
#$(info  Test FLAKE8 is evaluated to $(FLAKE8))
#$(info ****************End defines.mk **********************)

export TIME PLATFORM PYTHON PIP PIP_INSTALL_OPT YESTERDAY PYINSTALLER FLAKE8
