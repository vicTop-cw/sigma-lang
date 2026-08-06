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
#   make ready    # 生产就绪检查（--launch-ready 一次性确认，v0.121）
#   make deploy   # 生产启动（就绪通过后 --launch 前后端，Ctrl+C 停止，v0.122）
#   make all      # 全部（= accept）

PYTHON ?= python3

.PHONY: accept check story prove rust elixir app stats portfolio inventory cross-domain errors points invchain credit full audit contribution quota badge invflow pfflow cb pq tpq vr sf apc da ready deploy all

accept: ## 九道门禁一键验收（CI 与本地同一条命令）
	$(PYTHON) tools/sigma-accept.py

check: ## 三端共识（Law XIII）+ 算法正确性
	$(PYTHON) verify_consensus.py
	$(PYTHON) verify_p0.py

story: ## 三域审计故事线（找茬 MVP+增长期 + 供应链）
	$(PYTHON) tools/sigma-runtime.py --domains

prove: ## z3 义务消解（全量语料重验，v0.65）
	$(PYTHON) tools/sigma-prove.py

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

stats: ## 业务统计对账（Python /stats + Rust --app-smoke 38/38，v0.141）
	$(PYTHON) impl/python/sigma_app.py --stats-test
	cd impl/verifier && cargo run -q -- --app-smoke

portfolio: ## 金融市场对账（Python /portfolio-test + Rust 43/43 + Elixir 三域自检，v0.151）
	$(PYTHON) impl/python/sigma_app.py --portfolio-test
	cd impl/verifier && cargo run -q -- --app-smoke
	cd impl/elixir_rt && elixir sigma_verify.exs --sk-portfolio
	cd impl/elixir_rt && elixir sigma_verify.exs --sk-inventory

inventory: ## 供应链对账（Python /inventory-test + Rust 44/44 + Elixir §IN 7/7，v0.161）
	$(PYTHON) impl/python/sigma_app.py --inventory-test
	cd impl/verifier && cargo run -q -- --app-smoke
	cd impl/elixir_rt && elixir sigma_verify.exs --sk-inventory

cross-domain: ## 跨域链对账（Python /cross-domain-test + Rust 46/46 + Elixir 三域链 5/5，v0.171）
	$(PYTHON) impl/python/sigma_app.py --cross-domain-test
	cd impl/verifier && cargo run -q -- --app-smoke
	cd impl/elixir_rt && elixir sigma_verify.exs --sk-cross-domain

errors: ## 错误边界对账（Python /errors-test + Rust 48/48 + Elixir 错误边界 10/10，v0.181）
	$(PYTHON) impl/python/sigma_app.py --errors-test
	cd impl/verifier && cargo run -q -- --app-smoke
	cd impl/elixir_rt && elixir sigma_verify.exs --sk-errors

points: ## 积分链对账（Python /points-test + Rust 50/50 + Elixir 积分链 3/3，v0.191）
	$(PYTHON) impl/python/sigma_app.py --points-test
	cd impl/verifier && cargo run -q -- --app-smoke
	cd impl/elixir_rt && elixir sigma_verify.exs --sk-points

invchain: ## 库存链对账（Python /inventory-chain-test + Rust 51/51 + Elixir 库存链 5/5，v0.201）
	$(PYTHON) impl/python/sigma_app.py --inventory-chain-test
	cd impl/verifier && cargo run -q -- --app-smoke
	cd impl/elixir_rt && elixir sigma_verify.exs --sk-invchain

credit: ## 信用链对账（Python /credit-test + Rust 53/53 + Elixir 信用链 5/5，v0.211）
	$(PYTHON) impl/python/sigma_app.py --credit-test
	cd impl/verifier && cargo run -q -- --app-smoke
	cd impl/elixir_rt && elixir sigma_verify.exs --sk-credit

full: ## 全流程对账（Python /full-test + Rust 56/56 + Elixir 全流程 6/6，v0.221）
	$(PYTHON) impl/python/sigma_app.py --full-test
	cd impl/verifier && cargo run -q -- --app-smoke
	cd impl/elixir_rt && elixir sigma_verify.exs --sk-full

audit: ## 审计对账（Python /audit-test + Rust 58/58 + Elixir 审计链 3/3，v0.231）
	$(PYTHON) impl/python/sigma_app.py --audit-test
	cd impl/verifier && cargo run -q -- --app-smoke
	cd impl/elixir_rt && elixir sigma_verify.exs --sk-audit

contribution: ## 贡献分对账（Python /contribution-test + Rust 60/60 + Elixir 贡献分 3/3，v0.241）
	$(PYTHON) impl/python/sigma_app.py --contribution-test
	cd impl/verifier && cargo run -q -- --app-smoke
	cd impl/elixir_rt && elixir sigma_verify.exs --sk-contribution

quota: ## 额度链对账（Python /quota-flow-test + Rust 61/61 + Elixir 额度链 4/4，v0.251）
	$(PYTHON) impl/python/sigma_app.py --quota-flow-test
	cd impl/verifier && cargo run -q -- --app-smoke
	cd impl/elixir_rt && elixir sigma_verify.exs --sk-quota

badge: ## 勋章链对账（Python /badge-test + Rust 63/63 + Elixir 勋章链 4/4，v0.261）
	$(PYTHON) impl/python/sigma_app.py --badge-test
	cd impl/verifier && cargo run -q -- --app-smoke
	cd impl/elixir_rt && elixir sigma_verify.exs --sk-badge

invflow: ## 库存流转对账（Python /inventory-flow-test + Rust 65/65 + Elixir 库存流转 4/4，v0.271）
	$(PYTHON) impl/python/sigma_app.py --inventory-flow-test
	cd impl/verifier && cargo run -q -- --app-smoke
	cd impl/elixir_rt && elixir sigma_verify.exs --sk-invflow

pfflow: ## 组合流转对账（Python /portfolio-flow-test + Rust 67/67 + Elixir 组合流转 5/5，v0.281）
	$(PYTHON) impl/python/sigma_app.py --portfolio-flow-test
	cd impl/verifier && cargo run -q -- --app-smoke
	cd impl/elixir_rt && elixir sigma_verify.exs --sk-pfflow

cb: ## 三链联动对账（Python /credit-badge-test + Rust 70/70 + Elixir 三链联动 3/3，v0.291）
	$(PYTHON) impl/python/sigma_app.py --credit-badge-test
	cd impl/verifier && cargo run -q -- --app-smoke
	cd impl/elixir_rt && elixir sigma_verify.exs --sk-cb

pq: ## 积分-配额联动对账（Python /points-quota-test + Rust 72/72 + Elixir 积分-配额联动 3/3，v0.301）
	$(PYTHON) impl/python/sigma_app.py --points-quota-test
	cd impl/verifier && cargo run -q -- --app-smoke
	cd impl/elixir_rt && elixir sigma_verify.exs --sk-pq

tpq: ## 三维联动对账（Python /task-points-quota-test + Rust 75/75 + Elixir 三维联动 4/4，v0.311）
	$(PYTHON) impl/python/sigma_app.py --task-points-quota-test
	cd impl/verifier && cargo run -q -- --app-smoke
	cd impl/elixir_rt && elixir sigma_verify.exs --sk-tpq

vr: ## 估值-风险联动对账（Python /valuation-risk-test + Rust 77/77 + Elixir 估值-风险联动 3/3，v0.321）
	$(PYTHON) impl/python/sigma_app.py --valuation-risk-test
	cd impl/verifier && cargo run -q -- --app-smoke
	cd impl/elixir_rt && elixir sigma_verify.exs --sk-vr

sf: ## 库存-履约联动对账（Python /stock-fillrate-test + Rust 79/79 + Elixir 库存-履约联动 3/3，v0.331）
	$(PYTHON) impl/python/sigma_app.py --stock-fillrate-test
	cd impl/verifier && cargo run -q -- --app-smoke
	cd impl/elixir_rt && elixir sigma_verify.exs --sk-sf

apc: ## 验收-积分-契分三维联动对账（Python /accept-points-credit-test + Rust 82/82 + Elixir 验收-积分-契分联动 4/4，v0.341）
	$(PYTHON) impl/python/sigma_app.py --accept-points-credit-test
	cd impl/verifier && cargo run -q -- --app-smoke
	cd impl/elixir_rt && elixir sigma_verify.exs --sk-apc

da: ## 双资产交易链对账（Python /dual-asset-test + Rust 84/84 + Elixir 双资产交易链 4/4，v0.351）
	$(PYTHON) impl/python/sigma_app.py --dual-asset-test
	cd impl/verifier && cargo run -q -- --app-smoke
	cd impl/elixir_rt && elixir sigma_verify.exs --sk-da

ready: ## 生产就绪检查（--launch-ready 一次性确认环境，v0.121）
	$(PYTHON) impl/python/sigma_app.py --launch-ready

deploy: ## 生产启动（就绪检查通过后 --launch 前后端，Ctrl+C 停止，v0.122）
	$(PYTHON) impl/python/sigma_app.py --launch-ready && $(PYTHON) impl/python/sigma_app.py --launch

all: accept ## 全部（= 九道门禁一键验收）
