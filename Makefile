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

PNG_TARGETS = $(patsubst $(SRC)/%, $(DOCUMENTS)/%, $(shell find $(SRC) -name '*.png'))
CSS_TARGETS = $(patsubst $(SRC)/%, $(DOCUMENTS)/%, $(shell find $(SRC) -name '*.css'))

$(DOCSET)/.done: $(SRC)/.done $(PNG_TARGETS) $(CSS_TARGETS) $(DOCUMENTS)/cdk-version
	@mkdir -p $(DOCUMENTS)
	./scripts/build-docset.py \
		--source-dir $(SRC) \
		--target-dir $(DOCUMENTS) \
		--index $(DOCSET)/Contents/Resources/docSet.dsidx
	@touch $@

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

$(DOCUMENTS)/%.png: $(SRC)/%.png
	@mkdir -p $(dir $@)
	cp $< $@

$(DOCUMENTS)/%.css: $(SRC)/%.css
	@mkdir -p $(dir $@)
	cp $< $@

$(DOCUMENTS)/cdk-version: $(BUILD)/cdk-version
	@mkdir -p $(dir $@)
	cp $< $@
