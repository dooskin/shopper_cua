.PHONY: venv vendor install run batch
venv:
	python3 -m venv .venv

vendor:
	git submodule update --init --recursive

install: venv vendor
	. .venv/bin/activate; pip install -r requirements.txt; pip install -r vendor/openai-cua-sample-app/requirements.txt

run:
	. .venv/bin/activate; python scripts/run_once.py --persona personas/p01.json --variant A

batch:
	. .venv/bin/activate; python scripts/batch.py
