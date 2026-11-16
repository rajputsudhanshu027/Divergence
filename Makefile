.PHONY: bootstrap demo sample full analyze monitor build test

bootstrap:
	uv sync --locked --all-extras

demo:
	uv run retail-planner demo --ml --output-dir reports/demo

sample:
	uv run retail-planner run --config configs/sample.json --data-dir data/raw/m5 --output-dir reports/latest

full:
	uv run retail-planner run --config configs/full.json --data-dir data/raw/m5 --output-dir reports/full

analyze:
	uv run retail-planner analyze --output-dir reports/latest --analysis-dir reports/analysis

monitor:
	uv run retail-planner monitor --output-dir reports/latest

build:
	uv build

test:
	uv run pytest -q
