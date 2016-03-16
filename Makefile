requirements: venv
	source venv/bin/activate && pip install -r requirements.txt

venv:
	virtualenv --no-site-packages --distribute -p python2.7 venv
	virtualenv --relocatable venv

db:
	venv/bin/python manage.py migrate

clean_pyc:
	find . -name '*.pyc' -print0 | xargs -0 rm
	@echo "done"
