
all: all_c all_fortran

all_c:
	$(MAKE) -C surfacelayer/dummyc
	$(MAKE) -C subsurface/dummyc
	$(MAKE) -C openwater/dummyc

all_fortran:
	$(MAKE) -C surfacelayer/dummyfortran
	$(MAKE) -C subsurface/dummyfortran
	$(MAKE) -C openwater/dummyfortran

clean: clean_c clean_fortran

clean_c:
	$(MAKE) clean -C surfacelayer/dummyc
	$(MAKE) clean -C subsurface/dummyc
	$(MAKE) clean -C openwater/dummyc

clean_fortran:
	$(MAKE) clean -C surfacelayer/dummyfortran
	$(MAKE) clean -C subsurface/dummyfortran
	$(MAKE) clean -C openwater/dummyfortran
