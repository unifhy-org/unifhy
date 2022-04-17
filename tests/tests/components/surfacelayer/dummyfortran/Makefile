
all: clean sig lib

sig:
	python -m numpy.f2py -m dummyfortran -h dummyfortran.pyf --overwrite-signature dummy.f90

lib:
	rm -rf *.so
ifdef ON_MACOS
	python -m numpy.f2py -c dummyfortran.pyf dummy.f90 --f90flags='-L/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/lib'
else
	python -m numpy.f2py -c dummyfortran.pyf dummy.f90
endif
	rm -rf *.pyf

clean:
	rm -rf *.pyf *.so
