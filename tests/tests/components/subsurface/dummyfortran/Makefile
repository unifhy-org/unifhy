
all: clean sig lib

sig:
	python -m numpy.f2py -m dummyfortran -h dummyfortran.pyf --overwrite-signature dummy.f90

lib:
	rm -rf *.so
	alias gfortran="gfortran-9"
	python -m numpy.f2py -c dummyfortran.pyf dummy.f90
	rm -rf *.pyf

clean:
	rm -rf *.pyf *.so
