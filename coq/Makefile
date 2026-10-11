COQC := coqc
COQFLAGS :=

VFILES := RubikSnake.v Enumeration.v CollisionFixtures.v
VOFILES := $(VFILES:.v=.vo)

all: $(VOFILES)

%.vo: %.v
	$(COQC) $(COQFLAGS) $<

Enumeration.vo: RubikSnake.vo
CollisionFixtures.vo: RubikSnake.vo

clean:
	rm -f *.vo *.vok *.vos *.glob .*.aux

.PHONY: all clean
