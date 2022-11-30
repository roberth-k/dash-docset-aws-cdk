SHELL 			:= /usr/bin/env bash
.DEFAULT_GOAL 	:= docset
export PATH 	:= $(shell pwd)/scripts:$(shell pwd)/.venv/bin:$(PATH)

BUILD	:= .build/docset
DOCSET 	:= $(BUILD)/AWS-CDK.docset
TGZ		:= $(BUILD)/AWS-CDK.tgz

STATIC_FILES := \
	$(DOCSET)/icon.png \
	$(DOCSET)/Contents/Info.plist

.PHONY: clean venv static html docset tgz
clean:
	-rm -r .build
venv: .venv/bin/activate .build/.done-requirements
static: $(STATIC_FILES)
html: $(BUILD)/.done-make-html
tgz: $(TGZ)
docset:
	$(MAKE) venv
	$(MAKE) static
	$(MAKE) html
	$(MAKE) tgz

.venv/bin/activate:
	python3 -m venv .venv

.build/.done-requirements: .venv/bin/activate requirements.txt
	@mkdir -p $(dir $@)
	pip3 install -q -r requirements.txt
	@touch $@

$(STATIC_FILES): $(DOCSET)/%:  static/%
	@mkdir -p $(dir $@)
	cp $< $@

$(BUILD)/.done-make-html:
	mkdir -p $(DOCSET)/Contents/Resources/Documents
	python docset.py \
		--index $(DOCSET)/Contents/Resources/docSet.dsidx \
		--documents $(DOCSET)/Contents/Resources/Documents
	touch $(DOCSET)/.done-make-html

$(TGZ):
	cd $(dir $@) \
	&& tar --exclude='.DS_Store' -czf $(notdir $@) $(patsubst %.tgz,%.docset,$(notdir $@))
