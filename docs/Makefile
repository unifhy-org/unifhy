# List of packages belongings to the science library (for local build)
PKGS := artemis rfm gr4 smart
ROOT := ../../..
SPACE :=
SPACE +=
PKGS := $(foreach pkg,$(PKGS),$(ROOT)/cm4twccontrib-$(pkg)/cm4twccontrib-$(pkg))
PKGS := $(subst $(SPACE),:,$(strip $(PKGS)))

# Minimal makefile for Sphinx documentation
#
.ONESHELL:

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = ./_doc_src
BUILDDIR      = ./_doc_build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@echo $$PYTHONPATH
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

github_clean:
	@make local_clean
	rm -rf _static _sources _images
	rm -rf classes methods attributes components
	rm -rf *.html *.inv *.js .buildinfo

github_html:
	@make github_clean
	@make html
	@cp -a $(BUILDDIR)/html/. .

local_clean:
	rm -rf $(BUILDDIR)/doctrees $(BUILDDIR)/html

local_html:
	@make local_clean
	export PYTHONPATH=$(PKGS):$$PYTHONPATH ; $(MAKE) html
