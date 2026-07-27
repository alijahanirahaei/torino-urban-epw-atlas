.PHONY: serve validate test rebuild

serve:
	python3 -m http.server 8000

validate:
	python3 scripts/validate_release.py

test:
	python3 -m unittest discover -s tests -v

rebuild:
	python3 scripts/build_release.py
