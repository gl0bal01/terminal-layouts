# terminal-layouts — unified tmux + Zellij layout generator
#
# The manifest in manifest/workflows/*.yaml is the source of truth.
# dist/tmux/*.yaml and dist/zellij/*.kdl are generated artifacts.

WORKFLOWS := $(notdir $(basename $(wildcard manifest/workflows/*.yaml)))
GENERATORS := generators/gen-tmux.py generators/gen-zellij.py generators/validate.py
PYTHON := python3

.PHONY: help all tmux zellij schema parity test clean list

.DEFAULT_GOAL := help

help: ## Show this help
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  all        Generate tmux + zellij layouts for all workflows"
	@echo "  tmux       Generate tmux layouts (dist/tmux/*.yaml)"
	@echo "  zellij     Generate zellij layouts (dist/zellij/*.kdl)"
	@echo "  schema     Validate manifests against schema.json"
	@echo "  parity     Check tmux/zellij structural parity"
	@echo "  test       schema + parity + idempotence"
	@echo "  list       List available workflows"
	@echo "  clean      Remove dist/"
	@echo ""
	@echo "Workflows: $(WORKFLOWS)"

list: ## List available workflows
	@echo "Workflows in manifest/workflows/:"
	@for wf in $(WORKFLOWS); do echo "  $$wf"; done

all: tmux zellij ## Generate all layouts

tmux: ## Generate tmux layouts
	@mkdir -p dist/tmux
	@for wf in $(WORKFLOWS); do \
		$(PYTHON) generators/gen-tmux.py $$wf > dist/tmux/$$wf.yaml; \
		echo "  generated: dist/tmux/$$wf.yaml"; \
	done

zellij: ## Generate zellij layouts
	@mkdir -p dist/zellij
	@for wf in $(WORKFLOWS); do \
		$(PYTHON) generators/gen-zellij.py $$wf > dist/zellij/$$wf.kdl; \
		echo "  generated: dist/zellij/$$wf.kdl"; \
	done

schema: ## Validate manifests against schema.json
	@$(PYTHON) generators/validate.py

parity: tmux zellij ## Check tmux/zellij structural parity
	@bash tests/test-parity.sh

test: schema parity ## Run all tests
	@bash tests/test-idempotence.sh
	@echo "All tests passed."

clean: ## Remove dist/
	rm -rf dist/
	@echo "Removed dist/"
