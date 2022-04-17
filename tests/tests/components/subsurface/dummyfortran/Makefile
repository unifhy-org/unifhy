
all: clean sig lib

sig:
	python -m numpy.f2py -m dummyfortran -h dummyfortran.pyf --overwrite-signature dummy.f90

lib:
	rm -rf *.so
	python -m numpy.f2py -c dummyfortran.pyf dummy.f90 --fcompiler=gfortran-10
	rm -rf *.pyf

clean:
	rm -rf *.pyf *.so
