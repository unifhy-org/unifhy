
all: all_c all_fortran

all_c:
	$(MAKE) -C surfacelayer/dummyc
	$(MAKE) -C subsurface/dummyc
	$(MAKE) -C openwater/dummyc
	$(MAKE) -C nutrientsurfacelayer/dummyc
	$(MAKE) -C nutrientsubsurface/dummyc
	$(MAKE) -C nutrientopenwater/dummyc

all_fortran:
	$(MAKE) -C surfacelayer/dummyfortran
	$(MAKE) -C subsurface/dummyfortran
	$(MAKE) -C openwater/dummyfortran
	$(MAKE) -C nutrientsurfacelayer/dummyfortran
	$(MAKE) -C nutrientsubsurface/dummyfortran
	$(MAKE) -C nutrientopenwater/dummyfortran

clean: clean_c clean_fortran

clean_c:
	$(MAKE) clean -C surfacelayer/dummyc
	$(MAKE) clean -C subsurface/dummyc
	$(MAKE) clean -C openwater/dummyc
	$(MAKE) clean -C nutrientsurfacelayer/dummyc
	$(MAKE) clean -C nutrientsubsurface/dummyc
	$(MAKE) clean -C nutrientopenwater/dummyc

clean_fortran:
	$(MAKE) clean -C surfacelayer/dummyfortran
	$(MAKE) clean -C subsurface/dummyfortran
	$(MAKE) clean -C openwater/dummyfortran
	$(MAKE) clean -C nutrientsurfacelayer/dummyfortran
	$(MAKE) clean -C nutrientsubsurface/dummyfortran
	$(MAKE) clean -C nutrientopenwater/dummyfortran
