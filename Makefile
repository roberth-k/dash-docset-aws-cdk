SHELL 			:= /usr/bin/env bash
.DEFAULT_GOAL 	:= docset
export PATH 	:= $(shell pwd)/scripts:$(shell pwd)/.venv/bin:$(PATH)

BUILD	:= .build/docset
SRC		:= $(BUILD)/src
DOCSET 	:= $(BUILD)/AWS-CDK.docset
TGZ		:= $(BUILD)/AWS-CDK.tgz

DOCUMENTS := $(DOCSET)/Contents/Resources/Documents

STATIC_FILES := \
	$(DOCSET)/icon.png \
	$(DOCSET)/Contents/Info.plist

.PHONY: clean clean-all venv static download html docset tgz
clean:
	-rm -r $(TGZ) $(DOCSET)
clean-all:
	-rm -r .build
venv: .venv/bin/activate .build/.done-requirements
static: $(STATIC_FILES)
download: $(SRC)/.done
html: $(DOCSET)/.done
tgz: $(TGZ)
docset:
	$(MAKE) venv
	$(MAKE) static
	$(MAKE) download
	$(MAKE) html
	$(MAKE) tgz

.venv/bin/activate:
	python3 -m venv .venv

.build/.done-requirements: .venv/bin/activate requirements.txt
	@mkdir -p $(dir $@)
	pip3 install -q -r requirements.txt
	@touch $@

$(STATIC_FILES): $(DOCSET)/%: static/%
	@mkdir -p $(dir $@)
	cp $< $@

$(BUILD)/.done-make-html:
	@$(eval $@_VERSION_AT_START := $(shell $(MAKE) get-current-online-version))
	@mkdir -p $(DOCSET)/Contents/Resources/Documents
	./scripts/build-docset.py \
		--index $(DOCSET)/Contents/Resources/docSet.dsidx \
		--documents $(DOCSET)/Contents/Resources/Documents
	@$(eval $@_VERSION_AT_END := $(shell $(MAKE) get-current-online-version))
	@if [[ "$($@_VERSION_AT_START))" != "$($@_VERSION_AT_END))" ]]; then \
		1>&2 echo "Version mismatch! Started with $($@_VERSION_AT_START), and ended with $($@_VERSION_AT_END)."; \
		exit 1; \
	fi
	touch $(DOCSET)/.done-make-html

$(TGZ):
	cd $(dir $@) \
	&& tar --exclude='.DS_Store' -czf $(notdir $@) $(patsubst %.tgz,%.docset,$(notdir $@))

$(SRC)/.done: ./scripts/download-pages.py $(BUILD)/cdk-version
	@mkdir -p $(BUILD)/src
	./scripts/download-pages.py \
		--target-dir $(SRC) \
		--expect-version $(shell cat $(BUILD)/cdk-version)
	@touch $@

$(BUILD)/cdk-version:
	@mkdir -p $(dir $@)
	./scripts/get-current-online-version.py > $@
