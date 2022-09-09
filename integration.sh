set -x
pytest --subunit --co
echo
pytest --subunit integration_test
pytest --subunit integration_test | subunit-ls
stestr init
stestr list
PY_COLORS=1 stestr -p run --color
