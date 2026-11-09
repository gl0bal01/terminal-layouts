# terminal-layouts — unified tmux + Zellij layout generator
#
# The manifest in terminal_layouts/manifest/workflows/*.yaml is the source of truth.
# dist/tmux/*.yaml and dist/zellij/*.kdl are generated artifacts.

MANIFEST_DIR := terminal_layouts/manifest
WORKFLOWS := $(notdir $(basename $(wildcard $(MANIFEST_DIR)/workflows/*.yaml)))
PYTHON := python3
TL := $(PYTHON) -m terminal_layouts.cli

# Herdr release used by the live end-to-end test (CI and `make ci`).
# Bump both lines together: sha256 of herdr-linux-x86_64 from the release.
HERDR_VERSION := 0.9.5
HERDR_SHA256 := 14d9e8bc8b4a9e0118d77c32266f76d461f09b40342eb23752960bd89f59929d
# Override with your own build: make e2e-herdr HERDR_BIN=/path/to/herdr
HERDR_BIN ?= .cache/herdr/$(HERDR_VERSION)/herdr

# Zellij release used by the live tmux/Zellij test; sha256 of the extracted
# binary as published in zellij-no-web-x86_64-unknown-linux-musl.sha256sum.
ZELLIJ_VERSION := 0.45.1
ZELLIJ_SHA256 := 0ec6ef07b63c6355c02ce18343d40ef5ef5af19e25313ea9009c8fceda29e94f
ZELLIJ_BIN ?= .cache/zellij/$(ZELLIJ_VERSION)/zellij

.PHONY: help all tmux zellij herdr schema parity test e2e e2e-herdr e2e-mux ci hooks clean list install doctor setup

.DEFAULT_GOAL := help

help: ## Show this help
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  all        Generate tmux, zellij and Herdr plans for all workflows"
	@echo "  tmux       Generate tmux layouts (dist/tmux/*.yaml)"
	@echo "  zellij     Generate zellij layouts (dist/zellij/*.kdl)"
	@echo "  herdr      Generate inert Herdr JSON plans (dist/herdr/*.json)"
	@echo "  schema     Validate manifests against schema.json"
	@echo "  parity     Check tmux/zellij structural parity"
	@echo "  test       schema + parity + idempotence + Herdr + shell helper tests"
	@echo "  e2e        Live tests: e2e-herdr + e2e-mux"
	@echo "  e2e-herdr  Live test against a real, throwaway Herdr server"
	@echo "  e2e-mux    Live test against real, isolated tmux and Zellij"
	@echo "  ci         Run every CI job locally (scripts/ci-local.sh)"
	@echo "  hooks      Run 'make ci' before every git push"
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

all: tmux zellij herdr ## Generate all layouts

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

herdr: ## Generate Herdr workspace plans
	@mkdir -p dist/herdr
	@for wf in $(WORKFLOWS); do \
		$(TL) gen herdr $$wf > dist/herdr/$$wf.json; \
		echo "  generated: dist/herdr/$$wf.json"; \
	done

schema: ## Validate manifests against schema.json
	@$(TL) validate

parity: tmux zellij ## Check tmux/zellij structural parity
	@bash tests/test-parity.sh

test: schema parity herdr ## Run all tests
	@bash tests/test-idempotence.sh
	@$(PYTHON) -m unittest discover -s tests -p 'test_*.py'
	@echo "All tests passed."

$(HERDR_BIN):
	@if [ "$$(uname -sm)" != "Linux x86_64" ]; then \
		echo "error: pinned Herdr download is linux-x86_64 only; run make e2e-herdr HERDR_BIN=/path/to/herdr" >&2; exit 1; fi
	@mkdir -p $(@D)
	curl -fsSL -o $@.tmp https://github.com/herdrdev/herdr/releases/download/v$(HERDR_VERSION)/herdr-linux-x86_64
	echo "$(HERDR_SHA256)  $@.tmp" | sha256sum -c -
	chmod +x $@.tmp && mv $@.tmp $@

e2e-herdr: $(HERDR_BIN) ## Live test against a real, throwaway Herdr server
	HERDR_BIN=$(abspath $(HERDR_BIN)) $(PYTHON) -m unittest discover -s tests -p herdr_live.py -v

$(ZELLIJ_BIN):
	@if [ "$$(uname -sm)" != "Linux x86_64" ]; then \
		echo "error: pinned Zellij download is linux-x86_64 only; run make e2e-mux ZELLIJ_BIN=/path/to/zellij" >&2; exit 1; fi
	@mkdir -p $(@D)
	curl -fsSL https://github.com/zellij-org/zellij/releases/download/v$(ZELLIJ_VERSION)/zellij-no-web-x86_64-unknown-linux-musl.tar.gz | tar -xzO zellij > $@.tmp
	echo "$(ZELLIJ_SHA256)  $@.tmp" | sha256sum -c -
	chmod +x $@.tmp && mv $@.tmp $@

e2e-mux: $(ZELLIJ_BIN) ## Live test against real, isolated tmux and Zellij
	ZELLIJ_BIN=$(abspath $(ZELLIJ_BIN)) $(PYTHON) -m unittest discover -s tests -p mux_live.py -v

e2e: e2e-herdr e2e-mux ## All live tests

ci: ## Run every CI job locally
	@bash scripts/ci-local.sh

hooks: ## Run `make ci` before every git push
	git config core.hooksPath .githooks
	@echo "pre-push hook enabled (.githooks/pre-push)"

clean: ## Remove dist/
	rm -rf dist/
	@echo "Removed dist/"

install: ## Install layouts into ~/.config (tmuxp + zellij)
	@$(TL) install

doctor: ## Check required + recommended tools are installed
	@missing=0; \
	if command -v python3 >/dev/null 2>&1; then echo "  ok: python3 (required)"; \
	else echo "  MISSING: python3 (required)"; missing=1; fi; \
	for bin in tmux tmuxp zellij herdr; do \
		if command -v $$bin >/dev/null 2>&1; then echo "  ok: $$bin"; \
		else echo "  recommended (not found): $$bin"; fi; \
	done; \
	if [ $$missing -eq 0 ]; then echo "Doctor: required tooling present."; \
	else echo "Doctor: required tooling missing."; exit 1; fi

setup: install ## Install layouts + print shell setup hint
	@echo ""
	@echo "Add to your ~/.zshrc (or ~/.bashrc with bash):"
	@echo '  eval "$$(command tl init zsh)"'
	@echo "Shortcuts for tmux (t*), Zellij (z*) and Herdr (h*) + tab completion; th / zh / hh for help."
