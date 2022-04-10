
all: clean lib

lib:
	python setup.py build_ext --inplace
	rm -rf ./build
	rm dummyc.c

clean:
	rm -rf *.so
