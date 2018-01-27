#export PYTHONPATH=/path/to/lib:/path/to/tests

#python3 -m unittest  test_RegUtils

default: alltests

alltests: gps  Register

Register: CallOut RegUtils

gps:
	python3 -m unittest  test_gps

RegUtils:
	python3 -m unittest  test_RegUtils

CallOut:
	python3 -m unittest  test_CallOut
