# OSImager Development Makefile

.PHONY: help install install-plugins test validate clean docs build lint format check-deps
.DEFAULT_GOAL := help

# Configuration
PYTHON := python3
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest
BLACK := $(PYTHON) -m black
FLAKE8 := $(PYTHON) -m flake8

# Project paths
SRC_DIR := cli/osimager
TEST_DIR := tests
DATA_DIR := data
SCHEMAS_DIR := schemas
EXAMPLES_DIR := examples

help: ## Show this help message
	@echo 'OSImager Development Commands:'
	@echo ''
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install development dependencies
	$(PIP) install -r cli/requirements.txt
	$(PIP) install pytest black flake8 jsonschema
	@echo "✅ Development dependencies installed"

install-plugins: ## Install required Packer plugins
	@echo "Installing Packer plugins..."
	@./install-plugins.sh
	@echo "✅ Packer plugins installed"

test: ## Run unit tests
	$(PYTEST) $(TEST_DIR) -v
	@echo "✅ Tests completed"

test-coverage: ## Run tests with coverage report
	$(PYTEST) $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=html --cov-report=term
	@echo "✅ Tests with coverage completed"

validate: ## Validate all configuration files
	$(PYTHON) validate_config.py --validate-all
	@echo "✅ Configuration validation completed"

validate-quiet: ## Validate configurations (summary only)
	$(PYTHON) validate_config.py --validate-all --quiet

validate-syntax: ## Check JSON syntax of all configurations
	find $(DATA_DIR) -name '*.json' -exec $(PYTHON) validate_config.py --check-syntax {} \;
	@echo "✅ Syntax validation completed"

lint: ## Run code linting
	$(FLAKE8) $(SRC_DIR) --max-line-length=120 --ignore=E203,W503
	$(FLAKE8) *.py --max-line-length=120 --ignore=E203,W503
	@echo "✅ Linting completed"

format: ## Format code with black
	$(BLACK) $(SRC_DIR)
	$(BLACK) *.py
	@echo "✅ Code formatting completed"

format-check: ## Check if code needs formatting
	$(BLACK) --check $(SRC_DIR)
	$(BLACK) --check *.py

analyze-configs: ## Analyze all configuration files
	@echo "Analyzing configuration files..."
	@find $(DATA_DIR) -name '*.json' -type f | head -5 | while read file; do \
		echo "📊 $$file"; \
		$(PYTHON) config_converter.py --analyze "$$file" | head -10; \
		echo ""; \
	done

normalize-configs: ## Normalize all configuration files
	@echo "Normalizing configuration files..."
	@find $(DATA_DIR) -name '*.json' -type f | while read file; do \
		echo "Normalizing $$file"; \
		$(PYTHON) config_converter.py --normalize "$$file" --output "$$file.normalized"; \
		mv "$$file.normalized" "$$file"; \
	done
	@echo "✅ Configuration normalization completed"

docs: ## Generate documentation
	@echo "📚 Documentation files:"
	@echo "  • CONFIGURATION.md - Complete format specification"
	@echo "  • CONFIG_README.md - Quick start guide"
	@echo "  • schemas/ - JSON validation schemas"
	@echo "  • examples/ - Example configurations"
	@echo "Use 'make validate' to check configurations against schemas"

clean: ## Clean up generated files
	rm -rf __pycache__ .pytest_cache .coverage htmlcov
	find . -name '*.pyc' -delete
	find . -name '*.pyo' -delete
	find . -name '*~' -delete
	@echo "✅ Cleanup completed"

build: validate test lint ## Run full build pipeline
	@echo "✅ Full build pipeline completed successfully"

check-deps: ## Check for missing dependencies
	@echo "Checking dependencies..."
	@$(PYTHON) -c "import jsonschema; print('✅ jsonschema available')" || echo "❌ jsonschema missing - run 'make install'"
	@$(PYTHON) -c "import pytest; print('✅ pytest available')" || echo "❌ pytest missing - run 'make install'"
	@$(PYTHON) -c "import black; print('✅ black available')" || echo "❌ black missing - run 'make install'"

dev: install install-plugins validate test ## Set up development environment
	@echo "✅ Development environment ready"

# Schema validation targets
validate-specs: ## Validate only spec files
	find $(DATA_DIR)/specs -name '*.json' -exec $(PYTHON) validate_config.py --schema-type spec {} \;

validate-platforms: ## Validate only platform files
	find $(DATA_DIR)/platforms -name '*.json' -exec $(PYTHON) validate_config.py --schema-type platform {} \;

validate-locations: ## Validate only location files
	find $(DATA_DIR)/locations -name '*.json' -exec $(PYTHON) validate_config.py --schema-type location {} \;

# Example generation targets
generate-example-spec: ## Generate example spec from template
	@echo "Creating example spec configuration..."
	@echo '{"dist": "example", "version_pattern": "1.0", "supported_arches": ["x86_64"]}' > /tmp/values.json
	$(PYTHON) config_converter.py --generate-from-template $(EXAMPLES_DIR)/complex-nested-spec.json /tmp/values.json --pretty
	@rm /tmp/values.json

# CI/CD targets
ci-test: check-deps validate-syntax validate test ## Run CI test pipeline
	@echo "✅ CI test pipeline completed"

ci-full: check-deps validate test lint format-check ## Run full CI pipeline
	@echo "✅ Full CI pipeline completed"

# Server management
start-backend: ## Start OSImager backend server
	@echo "Starting OSImager backend server..."
	cd backend && ./run_with_venv.sh > ../logs/backend.log 2>&1 &
	@echo "Backend started - logs in logs/backend.log"

start-frontend: ## Start frontend development server
	@echo "Starting frontend development server..."
	cd frontend && source ~/.zshrc && pnpm run dev > ../logs/frontend.log 2>&1 &
	@echo "Frontend started - logs in logs/frontend.log"

stop-servers: ## Stop all servers
	@echo "Stopping servers..."
	@pkill -f "python.*main.py" || true
	@pkill -f "npm.*dev" || true
	@echo "✅ Servers stopped"

restart-servers: stop-servers start-backend start-frontend ## Restart all servers
	@echo "✅ Servers restarted"

# Documentation generation
generate-schema-docs: ## Generate schema documentation
	@echo "Generating schema documentation..."
	@for schema in $(SCHEMAS_DIR)/*.json; do \
		echo "## $$(basename $$schema .json | sed 's/-/ /g' | sed 's/\b\w/\u&/g')" ; \
		echo ""; \
		echo '```json'; \
		cat $$schema | jq '.properties | keys[]' -r | head -10; \
		echo '```'; \
		echo ""; \
	done

# Advanced targets
find-unused-variables: ## Find potentially unused variables in configurations
	@echo "Analyzing variable usage..."
	@find $(DATA_DIR) -name '*.json' -exec $(PYTHON) config_converter.py --analyze {} \; | grep -A 10 "Variables:"

check-config-consistency: ## Check configuration consistency across files
	@echo "Checking configuration consistency..."
	@$(PYTHON) validate_config.py --validate-all | grep -E "(✅|❌)" | sort | uniq -c

backup-configs: ## Backup configuration files
	@echo "Creating configuration backup..."
	@tar -czf "osimager-configs-$$(date +%Y%m%d-%H%M%S).tar.gz" $(DATA_DIR) $(SCHEMAS_DIR) $(EXAMPLES_DIR)
	@echo "✅ Backup created"

# Help for specific tools
validator-help: ## Show validator help
	$(PYTHON) validate_config.py --help

converter-help: ## Show converter help
	$(PYTHON) config_converter.py --help
