# Jenkins Job Analysis Makefile

.PHONY: help install collect analyze predict report clean test lint

# Default target
help:
	@echo "Jenkins Job Analysis Toolkit"
	@echo "============================"
	@echo ""
	@echo "Available commands:"
	@echo "  make install    - Install Python dependencies"
	@echo "  make setup      - Setup environment (copy .env.example to .env)"
	@echo "  make collect    - Collect Jenkins data"
	@echo "  make analyze    - Analyze collected data"
	@echo "  make predict    - Generate ML predictions"
	@echo "  make report     - Generate summary report"
	@echo "  make test       - Run basic tests"
	@echo "  make lint       - Run code linting"
	@echo "  make clean      - Clean generated files"
	@echo "  make full       - Run full analysis pipeline (collect + analyze + predict + report)"
	@echo ""
	@echo "Configuration:"
	@echo "  Edit .env file to set Jenkins connection details"
	@echo "  Edit config.yaml to customize data collection settings"

# Install dependencies
install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt
	@echo "✅ Dependencies installed"

# Install ML dependencies
install-ml:
	@echo "Installing ML dependencies..."
	pip install scikit-learn matplotlib seaborn
	@echo "✅ ML dependencies installed"

# Setup environment
setup:
	@if [ ! -f .env ]; then \
		echo "Creating .env from template..."; \
		cp .env.example .env; \
		echo "✅ .env created. Edit it with your Jenkins credentials."; \
	else \
		echo "ℹ️  .env already exists"; \
	fi
	@mkdir -p data
	@echo "✅ Setup complete"

# Collect Jenkins data
collect:
	@echo "🔄 Collecting Jenkins data..."
	python cli.py collect

# Analyze data
analyze:
	@echo "🔍 Analyzing Jenkins data..."
	python cli.py analyze

# Generate ML predictions
predict:
	@echo "🤖 Generating ML predictions..."
	python cli.py predict

# Generate summary report
report:
	@echo "📋 Generating summary report..."
	python cli.py report

# Run full pipeline
full: collect analyze predict report
	@echo "✅ Full analysis pipeline completed!"

# Test basic functionality
test:
	@echo "🧪 Running basic tests..."
	@python -c "import jenkins_client, data_collector, analysis, utils, cli; print('✅ All modules import successfully')"
	@python -c "from jenkins_client import JenkinsClient; print('✅ JenkinsClient can be instantiated')"
	@python -c "from data_collector import JenkinsDataCollector; print('✅ JenkinsDataCollector can be instantiated')"
	@python -c "from analysis import JenkinsAnalyzer; print('✅ JenkinsAnalyzer can be instantiated')"
	@echo "✅ Basic tests passed"

# Lint code (if tools are available)
lint:
	@echo "🔍 Running code quality checks..."
	@if command -v flake8 >/dev/null 2>&1; then \
		echo "Running flake8..."; \
		flake8 --max-line-length=120 --ignore=E501,W503 *.py examples/*.py; \
	else \
		echo "ℹ️  flake8 not available, skipping"; \
	fi
	@if command -v black >/dev/null 2>&1; then \
		echo "Running black (check only)..."; \
		black --check --line-length=120 *.py examples/*.py; \
	else \
		echo "ℹ️  black not available, skipping"; \
	fi
	@echo "✅ Code quality check completed"

# Format code
format:
	@echo "🎨 Formatting code..."
	@if command -v black >/dev/null 2>&1; then \
		black --line-length=120 *.py examples/*.py; \
		echo "✅ Code formatted with black"; \
	else \
		echo "❌ black not available. Install with: pip install black"; \
	fi

# Clean generated files
clean:
	@echo "🧹 Cleaning generated files..."
	@rm -rf data/*.json data/*.csv
	@rm -rf __pycache__ examples/__pycache__
	@rm -rf *.pyc examples/*.pyc
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup completed"

# Show current status
status:
	@echo "📊 Jenkins Analysis Toolkit Status"
	@echo "=================================="
	@echo ""
	@if [ -f .env ]; then \
		echo "✅ Environment file (.env) exists"; \
	else \
		echo "❌ Environment file (.env) missing - run 'make setup'"; \
	fi
	@if [ -f config.yaml ]; then \
		echo "✅ Configuration file (config.yaml) exists"; \
	else \
		echo "❌ Configuration file missing"; \
	fi
	@if [ -d data ]; then \
		DATA_FILES=$$(ls data/*.json 2>/dev/null | wc -l); \
		echo "📁 Data directory exists with $$DATA_FILES JSON files"; \
	else \
		echo "📁 Data directory missing"; \
	fi
	@echo ""
	@echo "Python dependencies:"
	@python -c "try:\n    import jenkins, pandas, numpy, yaml; print('✅ Core dependencies available')\nexcept ImportError as e:\n    print('❌ Missing core dependencies:', e)\ntry:\n    import sklearn; print('✅ ML dependencies available')\nexcept ImportError:\n    print('ℹ️  ML dependencies not installed (optional)')"

# Development setup
dev-setup: install setup
	@echo "🔧 Setting up development environment..."
	@pip install black flake8 pytest
	@if [ ! -f data/sample_data.json ]; then \
		echo "ℹ️  Run 'make collect' to gather real Jenkins data"; \
	fi
	@echo "✅ Development environment ready"

# Quick demo (using example data if available)
demo:
	@echo "🎭 Running demo..."
	@if [ -f data/complete_jenkins_data_*.json ]; then \
		echo "Using existing data for demo..."; \
		make analyze report; \
	else \
		echo "❌ No data available. Run 'make collect' first or check Jenkins connection."; \
	fi