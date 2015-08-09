
LANGUAGES := pl
PY := $(wildcard qygmy/*.py qygmy/templates/*.py)
UI := $(wildcard qygmy/ui/*.ui)

PRO := qygmy.pro
UIPY := $(UI:.ui=.py)
TS := $(foreach lang,$(LANGUAGES),qygmy/translations/qygmy_$(lang).ts)
QM := $(TS:.ts=.qm)
PY := $(PY) $(UIPY)

export QT_SELECT := 4

UIC := pyside-uic -x
LUPDATE := pyside-lupdate
LRELEASE := lrelease -compress -silent -nounfinished
DCH := dch -D unstable -p --package qygmy

all: ui ts

ui: $(UIPY)

%.py: %.ui
	$(UIC) -o $@ $<

ts: $(QM)

%.qm: %.ts
	$(LRELEASE) $< -qm $@

$(TS): $(PY)
	echo SOURCES = $^ >$(PRO)
	echo TRANSLATIONS = $@ >>$(PRO)
	$(LUPDATE) $(PRO)
	sed 's/filename="qygmy\//filename="..\//g' <$@ >$@.tmp; mv -f $@.tmp $@
	-rm $(PRO)

dch:
	srcver=`./bin/qygmyrun --version | sed -e 's/\.dev/~dev/' -e 's/[a-c]/~\0/'` \
	dchver=`dpkg-parsechangelog --count 1 | grep '^Version: ' | sed 's/^Version:\s\+\([^-]\+\)-.*$$/\1/'` \
	sh -c 'if [ $$srcver != $$dchver ]; then $(DCH) -m -v $$srcver-1; else $(DCH) -m -i; fi'

dchcreate:
	-rm debian/changelog
	$(DCH) -M --create -v `./bin/qygmyrun --version | sed -e 's/\.dev/~dev/' -e 's/[a-c]/~\0/'`-1

dchrelease:
	srcver=`./bin/qygmyrun --version | sed -e 's/\.dev/~dev/' -e 's/[a-c]/~\0/'` \
	dchver=`dpkg-parsechangelog --count 1 | grep '^Version: ' | sed 's/^Version:\s\+\([^-]\+\)-.*$$/\1/'` \
	sh -c 'if [ $$srcver != $$dchver ]; then $(DCH) -m -v $$srcver-1; fi'

clean:
	-rm -rf $(PRO)
	-rm -rf qygmy/ui/[!_]*.py
	-rm -rf qygmy/translations/*.qm
	-rm -rf qygmy/gittimestamp.txt
	-rm -rf __pycache__/
	-rm -rf */__pycache__/
	-rm -rf */*/__pycache__/
	-rm -rf build/
	-rm -rf MANIFEST

.PHONY: all ui ts clean dch dchcreate dchrelease
