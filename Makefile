# ΣLang — 一键验收 (v0.56)
# 协议工程化：把九道门禁一键验收（sigma-accept.py）接到标准构建工具链。
#
#   make accept   # 九道门禁一键验收（CI 与本地同一条命令）
#   make check    # 三端共识 + 算法正确性（快速）
#   make story    # 三域审计故事线
#   make prove    # z3 义务消解
#   make rust     # Rust 编译 + §SK 自检
#   make elixir   # Elixir §SK 自检
#   make app      # 找茬 App 全测试（自检/持久化/审计/冒烟）
#   make all      # 全部（= accept）

PYTHON ?= python3

.PHONY: accept check story prove rust elixir app all

accept: ## 九道门禁一键验收（CI 与本地同一条命令）
	$(PYTHON) tools/sigma-accept.py

check: ## 三端共识（Law XIII）+ 算法正确性
	$(PYTHON) verify_consensus.py
	$(PYTHON) verify_p0.py

story: ## 三域审计故事线（找茬 MVP+增长期 + 供应链）
	$(PYTHON) tools/sigma-runtime.py --domains

prove: ## z3 义务消解（全量语料重验，v0.65）
	$(PYTHON) tools/sigma-prove.py corpus/*.md

rust: ## Rust 编译（0 warning）+ §SK 自检
	cd impl/verifier && cargo build
	cd impl/verifier && cargo run -q -- --sk-self-check

elixir: ## Elixir §SK 自检
	cd impl/elixir_rt && elixir sigma_verify.exs --sk-self-check

app: ## 找茬 App 全测试（自检 / 持久化 / 审计 / 冒烟）
	$(PYTHON) impl/python/sigma_app.py
	$(PYTHON) impl/python/sigma_app.py --persist-test
	$(PYTHON) impl/python/sigma_app.py --audit-test
	$(PYTHON) impl/python/sigma_app.py --smoke

all: accept ## 全部（= 九道门禁一键验收）
