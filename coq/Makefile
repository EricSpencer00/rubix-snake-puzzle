COQC := coqc
COQFLAGS := -Q . RubikSnake

VFILES := RubikSnake.v Enumeration.v
VOFILES := $(VFILES:.v=.vo)

all: $(VOFILES)

%.vo: %.v
	$(COQC) $(COQFLAGS) $<

Enumeration.vo: RubikSnake.vo

clean:
	rm -f *.vo *.vok *.vos *.glob .*.aux

.PHONY: all clean
