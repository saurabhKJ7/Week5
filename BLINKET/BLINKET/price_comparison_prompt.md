You are CursorAI, tasked with building a real-time price-comparison platform for quick-commerce apps (Blinkit, Zepto, Instamart, BigBasket Now, etc.).  
The system must track live prices, discounts, and availability for thousands of products and answer natural-language questions accurately.  
Deliver the application end-to-end in clearly defined phases. Do not hallucinate tables, columns, or functionality—ask questions whenever something is ambiguous.

========================
GENERAL CODING GUIDELINES
========================
1. Clean, idiomatic code with comments for any non-obvious logic.
2. Modular, layered architecture (data, services, interfaces).
3. Unit & integration tests for every non-trivial module.
4. After each phase, update README with new capabilities and how to run tests.
5. Use env vars; never hard-code secrets.
6. Honour licences for third-party code.
7. Explain design trade-offs.
8. Add linters/formatters (ruff, black, or ESLint) and CI hooks.
9. Guardrails against hallucination:
   • Cite exact table/column names in all answers.  
   • If something does not exist, stop and create it or ask—never invent.  
   • Run a quick consistency check before returning query results.

========================
PHASE-BY-PHASE PLAN
========================
PHASE 0 – Project Bootstrap  
• Monorepo skeleton (Python or TypeScript; justify choice) with FastAPI or Express.  
• docker-compose with PostgreSQL 15+.  
• Connection pooling (pg-bouncer or asyncpg).  
• Health-check endpoint GET /ping.  
Guardrails: list all generated files in PR; show how to start dev stack in exactly three commands.

PHASE 1 – Database Schema Design  
• ≥ 50 tables covering product, platform, category, brand, price, availability, promotion, uom, currency, tax, location, mapping tables, etc.  
• Indices & constraints (PK, FK, unique, partial, composite).  
• ER diagram (Mermaid).  
Deliver Alembic (or equivalent) migrations with SQL comments and schema.md.  
Guardrails: run EXPLAIN on sample joins; max 5 seq scans.

PHASE 2 – Data Generation & Real-Time Simulation  
• Seed script: 5 platforms, 10 000 products, random categories/brands.  
• Scheduler (APScheduler/Celery Beat) every 30 s inserts price & availability deltas.  
• Append-only history; optional Kafka ingestion.  
Deliver seed/simulation scripts and rows-per-second benchmark.  
Guardrails: verify referential integrity on every batch.

PHASE 3 – Semantic Indexing & SQL Agent  
• Integrate LangChain SQLDatabaseToolkit.  
• Semantic index over table & column names + docstrings.  
• Retriever selects top-k tables (≥ 50 total).  
• Multi-step reasoning: parse NL → plan SQL → validate.  
• Log chain-of-thought to agent_logs table.  
Deliver POST /nl-query endpoint with tests for sample prompts.  
Guardrails: 400 error if agent selects non-existent table.

PHASE 4 – Advanced Query Planning & Optimisation  
• Stats-aware join ordering.  
• Automatic pagination & statistical sampling for large sets.  
• EXPLAIN ANALYSE feedback loop: if > 1 s, rewrite.  
• WITH CTEs vs sub-query decision.  
Deliver query_planner.py and benchmark naïve vs optimised plans.  
Guardrails: abort queries predicted to scan > 1 M rows w/o pagination.

PHASE 5 – Caching & Performance  
• Schema caching (Redis TTL).  
• Result caching keyed on normalised SQL + params.  
• 50–100 pooled connections.  
• Query monitoring (Prometheus + Grafana).  
• Query complexity analyser to reject abusive queries.  
Deliver Redis integration and dashboard JSON.  
Guardrails: document cache invalidation strategy.

PHASE 6 – API & Sample Queries  
REST endpoints:  
• /prices/cheapest?item=onions  
• /discounts?platform=Blinkit&min_pct=30  
• /compare?items=apple,banana&platforms=Zepto,Instamart  
CLI: compare_prices "onions"  
Run system tests for:  
• “Which app has cheapest onions right now?”  
• “Show products with 30%+ discount on Blinkit”  
• “Compare fruit prices between Zepto and Instamart”  
• “Find best deals for ₹1000 grocery list”  
Deliver OpenAPI docs and optional demo GIF.  
Guardrails: validate all inputs; return 422 on bad requests.

PHASE 7 – End-to-End Testing & Validation  
• Stress: 500 NL queries during price bursts.  
• Fault-injection: drop DB connection, ensure graceful retry.  
• Accuracy test with deterministic seed.  
• Security review against OWASP Top 10.  
Deliver tests folder; ≥ 85 % coverage.  
Guardrails: no phase passes with failing tests.

PHASE 8 – Deployment & Docs  
• Multi-stage Dockerfile (slim image).  
• Terraform/Ansible for PostgreSQL + Redis + app.  
• GitHub Actions CI/CD: lint → test → build → push.  
• Final README with architecture, setup, ops run-book.  
Guardrails: document DB migration rollback.

========================
ACCEPTANCE CRITERIA
========================
1. All phases deliver passing tests and documented trade-offs.  
2. Sample NL queries return correct, timely results.  
3. System sustains 100 QPS with < 300 ms p95 latency on 10 k products.  
4. Zero hallucinated tables/columns/functions.

========================
NEXT STEPS
========================
1. Confirm understanding of this plan.  
2. Begin Phase 0 and open a PR describing progress.  
3. After each phase is merged, proceed to the next.  
4. Ask for clarification whenever something is unclear. 