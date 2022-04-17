
all: clean sig lib

sig:
	python -m numpy.f2py -m dummyfortran -h dummyfortran.pyf --overwrite-signature dummy.f90

lib:
	rm -rf *.so
ifdef ON_MACOS
	export LIBRARY_PATH="$LIBRARY_PATH:/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/lib"
endif
	python -m numpy.f2py -c dummyfortran.pyf dummy.f90
	rm -rf *.pyf

clean:
	rm -rf *.pyf *.so
