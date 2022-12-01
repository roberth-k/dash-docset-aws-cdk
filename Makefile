SHELL 			:= /usr/bin/env bash -euo pipefail
.DEFAULT_GOAL	:= tgz
export PATH		:= $(shell pwd)/.venv/bin:$(PATH)

BUILD	:= .build/docset
SRC		:= $(BUILD)/src
DOCSET 	:= $(BUILD)/AWS-CDK.docset
TGZ		:= $(BUILD)/AWS-CDK.tgz
DOCUMENTS := $(DOCSET)/Contents/Resources/Documents

.FORCE:

all: tgz
venv: .build/.done-requirements
clean: .FORCE
	-rm -r $(TGZ) $(DOCSET)
clean/all: .FORCE
	-rm -r .build .venv
test/unit: venv .FORCE
	python -m unittest discover ./scripts
test: test/unit
tgz: $(TGZ)
download: $(SRC)/.done

.venv/bin/activate:
	python3 -m venv .venv

.build/.done-requirements: .venv/bin/activate requirements.txt
	@mkdir -p $(dir $@)
	pip3 install -q --disable-pip-version-check -r requirements.txt
	@touch $@

STATIC_TARGETS := $(patsubst static/%, $(DOCSET)/%, $(shell find static -type f))

$(STATIC_TARGETS): $(DOCSET)/%: static/%
	@mkdir -p $(dir $@)
	cp $< $@

$(DOCSET)/.done: 	$(SRC)/.done \
					$(DOCUMENTS)/cdk-version \
					./scripts/build-docset.py \
					$(STATIC_TARGETS) \
					venv
	@mkdir -p $(DOCUMENTS)
	./scripts/build-docset.py \
		--source-dir $(SRC) \
		--target-dir $(DOCUMENTS) \
		--index $(DOCSET)/Contents/Resources/docSet.dsidx \
		--expect-version $(shell cat $(BUILD)/cdk-version)
	@touch $@

$(TGZ): $(DOCSET)/.done
	cd $(dir $@) \
	&& tar --exclude='.DS_Store' -czf $(notdir $@) $(patsubst %.tgz,%.docset,$(notdir $@))

$(SRC)/.done: ./scripts/download-pages.py $(BUILD)/cdk-version venv
	@mkdir -p $(BUILD)/src
	./scripts/download-pages.py \
		--target-dir $(SRC) \
		--expect-version $(shell cat $(BUILD)/cdk-version)
	@touch $@

$(BUILD)/cdk-version: ./scripts/get-current-online-version.py venv
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
