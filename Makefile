SHELL 			:= /usr/bin/env bash
.DEFAULT_GOAL 	:= docset
export PATH 	:= $(shell pwd)/scripts:$(shell pwd)/.venv/bin:$(PATH)

.PHONY: venv
venv: .venv/bin/activate .build/.done-requirements

.venv/bin/activate:
	python3 -m venv .venv

.build/.done-requirements: .venv/bin/activate requirements.txt
	@mkdir -p $(dir $@)
	pip3 install -q -r requirements.txt
	@touch $@
