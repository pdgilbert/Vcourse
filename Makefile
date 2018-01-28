#export PYTHONPATH=/path/to/lib:/path/to/tests

#python3 -m unittest  test_RegUtils

default: test_Register test_RC

test_BT: test_gps

test_RC: test_gps
	python3 -m unittest  test_RC

test_Register: test_CallOut test_RegUtils

test_gps:
	python3 -m unittest  test_gps

testRegUtils:
	python3 -m unittest  test_RegUtils

test_CallOut:
	python3 -m unittest  test_CallOut
