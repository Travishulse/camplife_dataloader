# 08 — Cost Analysis

> **Target Application**: Camplife DataLoader v1.1.0  
> **Status**: PLANNING  
> **Created**: 2026-05-27

---

## 1. Infrastructure Costs

### 1.1 Core Infrastructure (Required)

| Component | Provider | Tier | Monthly Cost | Annual Cost | Notes |
|-----------|----------|------|-------------|-------------|-------|
| Source control | GitHub | Free | $0 | $0 | Public or private repo (free for both) |
| CI/CD | GitHub Actions | Free | $0 | $0 | 2,000 min/month free (private); unlimited (public) |
| Artifact hosting | GitHub Releases | Free | $0 | $0 | Generous limits; no per-download charges |
| Manifest CDN | Firebase Hosting | Spark (Free) | $0 | $0 | 10 GB storage + 10 GB/month transfer |
| TUF key storage | Encrypted USB drives | One-time | — | $20 (one-time) | Two USB drives for root key + backup |

**Total Core Infrastructure: $0/month ($20 one-time setup)**

### 1.2 Optional Infrastructure

| Component | Provider | Tier | Monthly Cost | Annual Cost | When Needed |
|-----------|----------|------|-------------|-------------|-------------|
| Code signing | Azure Artifact Signing | Basic | $10 | $120 | Phase 3+ (production distribution) |
| Error monitoring | Sentry | Free | $0 | $0 | Phase 4+ (optional) |
| Custom domain | Registrar | Standard | $1 | $12 | Phase 4+ (optional, for Firebase) |
| Firebase Auth | Firebase | Spark (Free) | $0 | $0 | Phase 3+ (if beta channels needed) |

**Total Optional: $10-11/month ($120-132/year)**

### 1.3 Cost Scaling Projections

| User Count | Monthly Downloads | Infrastructure Cost | Notes |
|-----------|-------------------|-------------------|-------|
| 1-50 | < 100 | $0 | Well within all free tiers |
| 50-200 | 100-500 | $0 | Still within free tiers |
| 200-1000 | 500-2000 | $0 | GitHub and Firebase free tiers remain sufficient |
| 1000+ | 2000+ | $0-5 | May approach Firebase 10 GB/month transfer; upgrade to Blaze (pay-as-you-go) |

**Assessment**: For the expected user base (< 200 users across ~18 campground properties), infrastructure costs will remain **$0/month** indefinitely.

---

## 2. Claude API Cost Estimates

### 2.1 Current API Pricing (May 2026)

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Best For |
|-------|----------------------|----------------------|----------|
| **Claude Opus 4.7** | $5.00 | $25.00 | Architecture, complex agents, deep reasoning |
| **Claude Sonnet 4.6** | $3.00 | $15.00 | Production coding, balanced performance |
| **Claude Haiku 4.5** | $1.00 | $5.00 | High-volume tasks, simple operations |

### 2.2 Implementation Phase Cost Estimates

Estimated Claude API costs for AI-assisted implementation of the update system.

#### Assumptions
- Average task complexity: Medium (Sonnet-tier)
- Average tokens per task: ~15K input + ~5K output
- System prompt caching: 5-min TTL (reduces input cost by ~50% on repeated calls)
- Interactive development: ~3 iterations per task average

#### Phase 0: Foundation & Infrastructure

| Task | Model | Input Tokens | Output Tokens | Iterations | Est. Cost |
|------|-------|-------------|---------------|-----------|-----------|
| Create update package structure | Haiku | 10K | 3K | 1 | $0.03 |
| Implement version_utils.py | Sonnet | 12K | 5K | 2 | $0.22 |
| Write version_utils tests | Sonnet | 15K | 8K | 2 | $0.33 |
| Configure GitHub Actions | Sonnet | 20K | 10K | 3 | $0.63 |
| Initialize TUF repository | Sonnet | 15K | 5K | 2 | $0.24 |
| Setup Firebase Hosting | Haiku | 8K | 3K | 1 | $0.02 |
| Update PyInstaller spec | Haiku | 10K | 2K | 1 | $0.02 |
| **Phase 0 Subtotal** | | | | | **~$1.50** |

#### Phase 1: Core Update Logic

| Task | Model | Input Tokens | Output Tokens | Iterations | Est. Cost |
|------|-------|-------------|---------------|-----------|-----------|
| Implement integrity.py | Sonnet | 12K | 6K | 2 | $0.25 |
| Implement update_checker.py | Sonnet | 20K | 12K | 3 | $0.72 |
| Implement update_manager.py | Sonnet | 25K | 15K | 4 | $1.20 |
| Implement rollback_manager.py | Sonnet | 20K | 12K | 3 | $0.72 |
| Implement apply_update.bat | Sonnet | 15K | 8K | 3 | $0.50 |
| Protected file logic | Sonnet | 10K | 5K | 2 | $0.24 |
| Download resume/retry | Sonnet | 12K | 6K | 2 | $0.25 |
| bsdiff integration | Sonnet | 12K | 5K | 2 | $0.22 |
| Write all unit tests | Sonnet | 25K | 15K | 3 | $0.90 |
| Write integration tests | Sonnet | 30K | 18K | 4 | $1.35 |
| **Phase 1 Subtotal** | | | | | **~$6.35** |

#### Phase 2: UI Integration & Pipeline

| Task | Model | Input Tokens | Output Tokens | Iterations | Est. Cost |
|------|-------|-------------|---------------|-----------|-----------|
| Update notification widget | Sonnet | 20K | 12K | 3 | $0.72 |
| Integrate checker in main.py | Sonnet | 15K | 5K | 2 | $0.24 |
| Download progress UI | Sonnet | 15K | 8K | 2 | $0.33 |
| Restart-to-update button | Sonnet | 12K | 5K | 2 | $0.22 |
| Health check on startup | Sonnet | 12K | 6K | 2 | $0.25 |
| CI/CD pipeline finalization | Sonnet | 20K | 10K | 3 | $0.63 |
| Update QA test plan | Haiku | 15K | 8K | 1 | $0.06 |
| **Phase 2 Subtotal** | | | | | **~$2.45** |

#### Phase 3: Security Hardening

| Task | Model | Input Tokens | Output Tokens | Iterations | Est. Cost |
|------|-------|-------------|---------------|-----------|-----------|
| TUF metadata integration | Opus | 25K | 10K | 3 | $1.13 |
| Manifest signature verify | Opus | 20K | 8K | 2 | $0.60 |
| HTTPS cert pinning | Sonnet | 10K | 5K | 2 | $0.21 |
| Security audit logging | Sonnet | 12K | 5K | 2 | $0.22 |
| Security-focused tests | Sonnet | 20K | 12K | 3 | $0.72 |
| **Phase 3 Subtotal** | | | | | **~$2.88** |

#### Phase 4: Polish & Release

| Task | Model | Input Tokens | Output Tokens | Iterations | Est. Cost |
|------|-------|-------------|---------------|-----------|-----------|
| Documentation updates | Haiku | 30K | 15K | 2 | $0.18 |
| Version history entry | Haiku | 10K | 5K | 1 | $0.04 |
| End-to-end testing | Sonnet | 20K | 8K | 3 | $0.54 |
| Security audit | Opus | 30K | 10K | 2 | $0.80 |
| User documentation | Haiku | 15K | 8K | 1 | $0.06 |
| **Phase 4 Subtotal** | | | | | **~$1.62** |

### 2.3 Implementation Cost Summary

| Phase | Estimated Cost | Model Mix |
|-------|---------------|-----------|
| Phase 0: Foundation | $1.50 | 60% Sonnet, 30% Haiku, 10% Opus |
| Phase 1: Core Logic | $6.35 | 90% Sonnet, 10% Haiku |
| Phase 2: UI & Pipeline | $2.45 | 85% Sonnet, 15% Haiku |
| Phase 3: Security | $2.88 | 60% Sonnet, 40% Opus |
| Phase 4: Polish | $1.62 | 40% Haiku, 35% Sonnet, 25% Opus |
| **Total Implementation** | **~$14.80** | |

#### With Safety Buffer

| Scenario | Multiplier | Total |
|----------|-----------|-------|
| Best case (smooth implementation) | 1.0x | $14.80 |
| **Likely case** (normal iterations) | **1.5x** | **$22.20** |
| Worst case (significant rework) | 2.5x | $37.00 |

### 2.4 Operational API Costs (Post-Launch)

| Activity | Frequency | Model | Tokens/Call | Monthly Cost |
|----------|-----------|-------|------------|-------------|
| Bug fix patches | 1-2/month | Sonnet | ~20K total | $0.30-0.60 |
| Feature additions | 0-1/month | Sonnet | ~30K total | $0-0.45 |
| Documentation updates | 1/month | Haiku | ~10K total | $0.06 |
| Security reviews | 1/quarter | Opus | ~30K total | $0.27 |
| **Monthly operational** | | | | **$0.36-$1.38** |
| **Annual operational** | | | | **$4.32-$16.56** |

---

## 3. Development Time Cost

### 3.1 Estimated Developer/Agent Hours

| Phase | Tasks | Estimated Hours | Notes |
|-------|-------|----------------|-------|
| Phase 0 | 10 | 8-12 hours | Setup and scaffolding |
| Phase 1 | 14 | 20-30 hours | Most complex phase; core logic |
| Phase 2 | 11 | 12-18 hours | UI integration + CI/CD |
| Phase 3 | 9 | 10-15 hours | Security hardening |
| Phase 4 | 11 | 8-12 hours | Documentation + testing |
| **Total** | **55** | **58-87 hours** | |

### 3.2 Calendar Time Estimate

| Scenario | Duration | Assumptions |
|----------|----------|-------------|
| Full-time (AI + human) | 2-3 weeks | 4-6 hours/day of focused work |
| Part-time (evenings/weekends) | 4-6 weeks | 1-2 hours/day |
| Conservative (with testing) | 6-8 weeks | Including buffer for unexpected issues |

---

## 4. Total Cost of Ownership (Year 1)

### 4.1 Year 1 Costs

| Category | One-Time | Monthly | Annual |
|----------|----------|---------|--------|
| **Infrastructure** | $20 (USB drives) | $0 | $0 |
| **Code signing (optional)** | — | $10 | $120 |
| **Claude API (implementation)** | $22 | — | — |
| **Claude API (operations)** | — | $1 | $12 |
| **Domain name (optional)** | — | $1 | $12 |
| **Total (minimum)** | **$42** | **$1** | **$54** |
| **Total (with all options)** | **$42** | **$12** | **$186** |

### 4.2 Year 2+ Costs (Steady State)

| Category | Monthly | Annual |
|----------|---------|--------|
| **Infrastructure** | $0 | $0 |
| **Code signing** | $10 | $120 |
| **Claude API (operations)** | $1 | $12 |
| **Domain** | $1 | $12 |
| **Total (minimum)** | **$1** | **$12** |
| **Total (with all options)** | **$12** | **$144** |

---

## 5. Cost Optimization Strategies

### 5.1 Claude API Optimization

| Strategy | Savings | Implementation |
|----------|---------|---------------|
| **Prompt caching** (5-min TTL) | 40-50% on input tokens | Cache system prompt + project context for multi-step tasks |
| **Model routing** (Haiku for simple) | 60-70% on simple tasks | Use Haiku for docs, formatting; Sonnet for coding; Opus for architecture |
| **Batch API** (non-urgent) | 50% on all tokens | Use for test generation, documentation, non-interactive work |
| **Self-contained tasks** | 30-40% on context tokens | Pre-written task files eliminate need to scan the codebase |

### 5.2 Infrastructure Optimization

| Strategy | Savings | Implementation |
|----------|---------|---------------|
| **GitHub public repo** | Unlimited Actions minutes | Open-source the update system (application stays private) |
| **Skip code signing initially** | $120/year | Accept SmartScreen warnings for internal distribution |
| **Skip custom domain** | $12/year | Use Firebase default domain (*.web.app) |

---

## 6. Cost Comparison: Build vs. Buy

| Approach | Implementation Cost | Annual Operating Cost | Total Year 1 |
|----------|-------------------|---------------------|-------------|
| **Custom (this plan)** | ~$42-62 | $12-144 | $54-186 |
| **Electron + electron-updater** | Rewrite app (~$500-1000 in AI time) | $0-120 | $500-1120 |
| **MSIX + Microsoft Store** | Moderate packaging work (~$100-200) | $0 (free store) | $100-200 |
| **Manual distribution (status quo)** | $0 | $0 | $0 (but no auto-updates) |

**Assessment**: The custom approach offers the best balance of capability and cost. MSIX is a viable alternative if Microsoft Store distribution is acceptable. Manual distribution is free but doesn't meet the requirements.

---

## 7. Budget Recommendation

### Minimum Viable Budget

| Item | Amount | Priority |
|------|--------|----------|
| TUF key USB drives | $20 | Required |
| Claude API (implementation) | $25 | Required |
| Claude API (12 months operations) | $12 | Required |
| **Total** | **$57** | |

### Recommended Budget (with safety margin)

| Item | Amount | Priority |
|------|--------|----------|
| TUF key USB drives | $20 | Required |
| Claude API (implementation, 1.5x buffer) | $40 | Required |
| Claude API (12 months operations) | $20 | Required |
| Code signing (12 months) | $120 | Recommended |
| Contingency (20%) | $40 | Recommended |
| **Total** | **$240** | |

---

> This concludes the planning framework. See the [tasks/](./tasks/) directory for execution-ready task files.
