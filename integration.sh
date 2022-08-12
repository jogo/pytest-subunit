set -x
pytest --subunit --co
echo
pytest --subunit tests.list | subunit-ls
pytest --subunit integration_test | subunit-ls
stestr init
stestr run
