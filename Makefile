SHELL 			:= /usr/bin/env bash
.DEFAULT_GOAL 	:= docset
export PATH 	:= $(shell pwd)/scripts:$(shell pwd)/.venv/bin:$(PATH)
MAKEFLAGS		:= --no-print-directory

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

.PHONY: get-current-online-version
get-current-online-version:
	@./scripts/get-current-online-version.py
