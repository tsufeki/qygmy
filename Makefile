
UIFILES = $(wildcard qygmy/ui/*.ui)
PYUIFILES = $(UIFILES:.ui=.py)
UIC = pyside-uic -x

all: $(PYUIFILES)

%.py: %.ui
	$(UIC) -o $@ $<

.PHONY: all
