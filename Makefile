# terminal-layouts — unified tmux + Zellij layout generator
#
# The manifest in terminal_layouts/manifest/workflows/*.yaml is the source of truth.
# dist/tmux/*.yaml and dist/zellij/*.kdl are generated artifacts.

MANIFEST_DIR := terminal_layouts/manifest
WORKFLOWS := $(notdir $(basename $(wildcard $(MANIFEST_DIR)/workflows/*.yaml)))
PYTHON := python3
TL := $(PYTHON) -m terminal_layouts.cli

.PHONY: help all tmux zellij schema parity test clean list install doctor setup

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
	@echo "  install    Install layouts into ~/.config (tmuxp + zellij)"
	@echo "  doctor     Check required tools are installed"
	@echo "  setup      install + print shell setup hint"
	@echo "  clean      Remove dist/"
	@echo ""
	@echo "Workflows: $(WORKFLOWS)"

list: ## List available workflows
	@echo "Workflows in $(MANIFEST_DIR)/workflows/:"
	@for wf in $(WORKFLOWS); do echo "  $$wf"; done

all: tmux zellij ## Generate all layouts

tmux: ## Generate tmux layouts
	@mkdir -p dist/tmux
	@for wf in $(WORKFLOWS); do \
		$(TL) gen tmux $$wf > dist/tmux/$$wf.yaml; \
		echo "  generated: dist/tmux/$$wf.yaml"; \
	done

zellij: ## Generate zellij layouts
	@mkdir -p dist/zellij
	@for wf in $(WORKFLOWS); do \
		$(TL) gen zellij $$wf > dist/zellij/$$wf.kdl; \
		echo "  generated: dist/zellij/$$wf.kdl"; \
	done

schema: ## Validate manifests against schema.json
	@$(TL) validate

parity: tmux zellij ## Check tmux/zellij structural parity
	@bash tests/test-parity.sh

test: schema parity ## Run all tests
	@bash tests/test-idempotence.sh
	@echo "All tests passed."

clean: ## Remove dist/
	rm -rf dist/
	@echo "Removed dist/"

install: ## Install layouts into ~/.config (tmuxp + zellij)
	@$(TL) install

doctor: ## Check required + recommended tools are installed
	@missing=0; \
	if command -v python3 >/dev/null 2>&1; then echo "  ok: python3 (required)"; \
	else echo "  MISSING: python3 (required)"; missing=1; fi; \
	for bin in tmux tmuxp zellij; do \
		if command -v $$bin >/dev/null 2>&1; then echo "  ok: $$bin"; \
		else echo "  recommended (not found): $$bin"; fi; \
	done; \
	if [ $$missing -eq 0 ]; then echo "Doctor: required tooling present."; \
	else echo "Doctor: required tooling missing."; exit 1; fi

setup: install ## Install layouts + print shell setup hint
	@echo ""
	@echo "Add to your ~/.zshrc:"
	@echo "  source $(CURDIR)/shell/tmux-layouts.zsh"
	@echo "  source $(CURDIR)/shell/zellij-layouts.zsh"
