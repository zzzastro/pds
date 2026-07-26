.PHONY: setup run migrate check test clean

setup:
	./run.sh

run:
	./run.sh

migrate:
	. venv/bin/activate && python manage.py migrate

check:
	. venv/bin/activate && python manage.py check

test:
	. venv/bin/activate && python manage.py test

clean:
	rm -rf /tmp/pds_venv venv *.pyc __pycache__ .pytest_cache
