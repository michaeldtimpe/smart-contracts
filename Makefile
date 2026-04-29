.PHONY: help install verify pilot benchmark wild grade analyze clean

PYTHON := python3
DATASET := dataset

help:
	@echo "Targets:"
	@echo "  install        Install Python deps + Foundry"
	@echo "  verify         Run reference Foundry exploits against pinned forks (CI gate)"
	@echo "  pilot          5-contract pilot run (1 frontier + 1 local model, single-shot)"
	@echo "  benchmark      Full 2160-trial benchmark run"
	@echo "  wild           Wild-phase real-world exploit search (post-benchmark, gated)"
	@echo "  grade          Re-grade results from a run directory"
	@echo "  analyze        Generate whitepaper figures from results/"
	@echo "  clean          Remove caches and intermediate artifacts"

install:
	$(PYTHON) -m pip install -e .
	@command -v forge >/dev/null 2>&1 || curl -L https://foundry.paradigm.xyz | bash
	foundryup

verify:
	$(PYTHON) -m grading.auto_grade --verify-references --dataset $(DATASET)

pilot:
	$(PYTHON) -m harness.single_shot --pilot --dataset $(DATASET)

benchmark:
	@echo "REFUSING: run only after PREREGISTRATION.md is frozen and committed."
	@echo "Set BENCHMARK_PREREG_HASH=<commit_hash> in env to proceed."
	@test -n "$$BENCHMARK_PREREG_HASH" || exit 1
	$(PYTHON) -m harness.run_benchmark --prereg-hash $$BENCHMARK_PREREG_HASH

wild:
	@echo "REFUSING: wild phase requires benchmark complete and liaison confirmed."
	@echo "Set WILD_LIAISON_CONFIRMED=1 and WILD_PREREG_HASH=<hash> to proceed."
	@test "$$WILD_LIAISON_CONFIRMED" = "1" || exit 1
	@test -n "$$WILD_PREREG_HASH" || exit 1
	$(PYTHON) -m harness.run_wild --prereg-hash $$WILD_PREREG_HASH

grade:
	$(PYTHON) -m grading.auto_grade --run-dir $(RUN_DIR)

analyze:
	$(PYTHON) -m analysis.report --results results/ --out analysis/figures/

clean:
	rm -rf cache/ out/ .anvil-cache/ __pycache__/ */__pycache__/ */*/__pycache__/
