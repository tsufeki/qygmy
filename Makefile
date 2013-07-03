
LANGUAGES := pl
PY := $(wildcard qygmy/*.py qygmy/templates/*.py)
UI := $(wildcard qygmy/ui/*.ui)

PRO := qygmy.pro

UIPY := $(UI:.ui=.py)
TS := $(foreach lang,$(LANGUAGES),qygmy/translations/qygmy_$(lang).ts)
QM := $(TS:.ts=.qm)
PY := $(PY) $(UIPY)

UIC := pyside-uic -x
LUPDATE := pyside-lupdate
LRELEASE := lrelease -compress -silent -nounfinished

all: ui ts

ui: $(UIPY)

%.py: %.ui
	$(UIC) -o $@ $<

ts: $(QM)

%.qm: %.ts
	$(LRELEASE) $< -qm $@

$(TS): $(PY)
	@echo SOURCES = $^ >$(PRO)
	@echo TRANSLATIONS = $@ >>$(PRO)
	@echo $(LUPDATE) ... -ts $@
	@$(LUPDATE) $(PRO)
	@sed 's/filename="qygmy\//filename="..\//g' <$@ >$@.tmp; mv -f $@.tmp $@
	@-rm $(PRO)

clean:
	-rm -rf $(PRO)
	-rm -rf qygmy/ui/[!_]*.py
	-rm -rf qygmy/translations/*.qm
	-rm -rf __pycache__/
	-rm -rf */__pycache__/
	-rm -rf */*/__pycache__/
	-rm -rf build/
	-rm -rf MANIFEST

.PHONY: all ui ts clean
