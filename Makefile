
PY := $(wildcard qygmy/*.py qygmy/templates/*.py)
UI := $(wildcard qygmy/ui/*.ui)
TS := i18n/qygmy_pl.ts

PRO := qygmy.pro

UIPY := $(UI:.ui=.py)
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
	@sed 's/filename="\([^.]\)/filename="..\/\1/g' <$@ >$@.tmp; mv -f $@.tmp $@
	@-rm $(PRO)

clean:
	-rm -rf $(PRO) qygmy/ui/[!_]*.py i18n/*.qm {,*/{,*/}}__pycache__

.PHONY: all ui ts clean
