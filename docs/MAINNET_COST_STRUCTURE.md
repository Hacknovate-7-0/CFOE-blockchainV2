# CfoE Mainnet Deployment Cost Structure

## Overview
This document outlines the complete cost structure for deploying and operating the Carbon Footprint Optimization Engine (CfoE) on Algorand Mainnet with production-grade infrastructure.

---

## 1. Algorand Blockchain Costs (Mainnet)

### 1.1 Initial Setup Costs

| Item | Cost (ALGO) | Cost (USD)* | Frequency | Notes |
|------|-------------|-------------|-----------|-------|
| **Account Minimum Balance** | 0.1 ALGO | $0.02 | One-time | Required to activate account |
| **Carbon Credit Token (ASA) Creation** | 0.1 ALGO | $0.02 | One-time | Fungible token for carbon credits |
| **Token Opt-In (per recipient)** | 0.1 ALGO | $0.02 | Per user | Each recipient must opt-in to receive tokens |
| **Reserve Account Funding** | 10-100 ALGO | $2-20 | One-time | Recommended reserve for operations |

**Total Initial Setup: ~10.3 ALGO ($2.06)**

*Assuming 1 ALGO = $0.20 (adjust based on current market price)

### 1.2 Per-Transaction Costs

| Transaction Type | Cost (ALGO) | Cost (USD) | Frequency | Annual Volume (Est.) | Annual Cost |
|------------------|-------------|------------|-----------|---------------------|-------------|
| **Score Anchor** | 0.001 | $0.0002 | Per audit | 10,000 audits | $2.00 |
| **Report Hash Registration** | 0.001 | $0.0002 | Per audit | 10,000 audits | $2.00 |
| **Carbon Credits Recording** | 0.001 | $0.0002 | Per audit | 10,000 audits | $2.00 |
| **HITL Decision** | 0.001 | $0.0002 | Per critical audit | 1,000 audits | $0.20 |
| **Credit Issuance (ASA Transfer)** | 0.001 | $0.0002 | Per issuance | 5,000 transfers | $1.00 |
| **Credit Retirement (Burn)** | 0.001 | $0.0002 | Per retirement | 2,000 burns | $0.40 |
| **Audit Certificate NFT** | 0.1 | $0.02 | Per NFT | 500 NFTs | $10.00 |

**Total Annual Blockchain Costs: ~$17.60** (for 10,000 audits/year)

### 1.3 Storage Costs

| Item | Cost | Notes |
|------|------|-------|
| **Per-Asset Storage** | 0.1 ALGO | Each ASA (token/NFT) increases minimum balance |
| **Per-Application Storage** | 0.1 ALGO per schema | If using smart contracts |

---

## 2. API Service Costs

### 2.1 Groq API (AI Report Generation)

| Tier | Model | Cost per 1M Tokens | Tokens per Audit | Cost per Audit | Annual Cost (10K audits) |
|------|-------|---------------------|------------------|----------------|-------------------------|
| **Free Tier** | llama-3.3-70b | $0 | ~2,000 | $0 | $0 |
| **Paid Tier** | llama-3.3-70b | $0.59 (input)<br>$0.79 (output) | 1,500 input<br>500 output | $0.0013 | $13.00 |

**Recommended: Start with Free Tier, upgrade if rate limits hit**

**Free Tier Limits:**
- 30 requests/minute
- 14,400 requests/day
- ~432,000 requests/month

**Paid Tier Benefits:**
- Higher rate limits
- Priority access
- SLA guarantees

### 2.2 Tavily API (External Risk Monitoring - Optional)

| Tier | Searches/Month | Cost/Month | Cost per Search | Annual Cost |
|------|----------------|------------|-----------------|-------------|
| **Free** | 1,000 | $0 | $0 | $0 |
| **Basic** | 10,000 | $29 | $0.0029 | $348 |
| **Pro** | 50,000 | $99 | $0.0020 | $1,188 |
| **Enterprise** | Unlimited | Custom | Custom | Custom |

**Recommended: Free tier for testing, Basic for production**

**Note:** Tavily is optional - system works without external monitoring

---

## 3. Infrastructure Costs

### 3.1 Hosting Options

#### Option A: Cloud VPS (Recommended for Production)

| Provider | Plan | vCPU | RAM | Storage | Bandwidth | Cost/Month | Annual Cost |
|----------|------|------|-----|---------|-----------|------------|-------------|
| **DigitalOcean** | Basic Droplet | 1 | 1GB | 25GB SSD | 1TB | $6 | $72 |
| **DigitalOcean** | Standard | 2 | 2GB | 50GB SSD | 2TB | $12 | $144 |
| **AWS Lightsail** | Small | 1 | 2GB | 40GB SSD | 2TB | $10 | $120 |
| **Linode** | Nanode | 1 | 1GB | 25GB SSD | 1TB | $5 | $60 |
| **Hetzner** | CX11 | 1 | 2GB | 20GB SSD | 20TB | €4.15 | ~$55 |

**Recommended: Hetzner CX11 or Linode Nanode for cost efficiency**

#### Option B: Serverless (AWS Lambda + API Gateway)

| Service | Free Tier | Paid Tier | Est. Monthly Cost | Annual Cost |
|---------|-----------|-----------|-------------------|-------------|
| **Lambda** | 1M requests/month | $0.20 per 1M requests | $5 | $60 |
| **API Gateway** | 1M requests/month | $3.50 per 1M requests | $10 | $120 |
| **S3 Storage** | 5GB free | $0.023/GB | $2 | $24 |
| **CloudWatch Logs** | 5GB free | $0.50/GB | $3 | $36 |

**Total Serverless: ~$20/month ($240/year)**

#### Option C: Self-Hosted (On-Premises)

| Item | One-Time Cost | Monthly Cost | Annual Cost |
|------|---------------|--------------|-------------|
| **Raspberry Pi 4 (8GB)** | $75 | - | - |
| **Power** | - | $2 | $24 |
| **Internet** | - | $0 (existing) | $0 |
| **Domain** | - | $1 | $12 |

**Total Self-Hosted: $36/year (after initial $75 hardware)**

### 3.2 Domain & SSL

| Item | Provider | Cost/Year | Notes |
|------|----------|-----------|-------|
| **Domain (.com)** | Namecheap | $13 | Standard TLD |
| **Domain (.io)** | Namecheap | $39 | Tech-focused TLD |
| **SSL Certificate** | Let's Encrypt | $0 | Free automated SSL |
| **SSL Certificate** | Paid | $50-200 | Extended validation |

**Recommended: .com domain + Let's Encrypt SSL = $13/year**

### 3.3 Database (Optional - for scaling)

| Service | Plan | Storage | Cost/Month | Annual Cost |
|---------|------|---------|------------|-------------|
| **MongoDB Atlas** | Free | 512MB | $0 | $0 |
| **MongoDB Atlas** | Shared | 2GB | $9 | $108 |
| **PostgreSQL (Supabase)** | Free | 500MB | $0 | $0 |
| **PostgreSQL (Supabase)** | Pro | 8GB | $25 | $300 |

**Current Setup: JSON file storage (free, sufficient for <100K audits)**

---

## 4. Monitoring & Analytics (Optional)

| Service | Plan | Cost/Month | Annual Cost | Features |
|---------|------|------------|-------------|----------|
| **Sentry** | Free | $0 | $0 | Error tracking (5K events/month) |
| **Sentry** | Team | $26 | $312 | 50K events/month |
| **Datadog** | Free | $0 | $0 | Infrastructure monitoring (5 hosts) |
| **Datadog** | Pro | $15/host | $180 | Advanced monitoring |
| **Uptime Robot** | Free | $0 | $0 | 50 monitors, 5-min checks |

**Recommended: Free tiers for all monitoring services**

---

## 5. Security & Compliance

| Item | Cost | Frequency | Notes |
|------|------|-----------|-------|
| **SSL Certificate** | $0 | Annual | Let's Encrypt (free) |
| **DDoS Protection** | $0-200 | Monthly | Cloudflare free tier sufficient |
| **Backup Storage** | $5 | Monthly | 100GB cloud backup |
| **Security Audit** | $500-5000 | One-time | Smart contract audit (if needed) |
| **Penetration Testing** | $1000-10000 | Annual | Optional for enterprise |

---

## 6. Development & Maintenance

| Item | Cost | Frequency | Notes |
|------|------|-----------|-------|
| **Developer Time** | $50-150/hr | Ongoing | Maintenance, updates, features |
| **Bug Fixes** | $500-2000 | Monthly | Estimated 10-20 hours/month |
| **Feature Development** | $2000-10000 | Quarterly | New features, improvements |
| **DevOps** | $1000-5000 | Monthly | CI/CD, monitoring, scaling |

---

## 7. Total Cost Summary

### Minimal Production Setup (Recommended for MVP)

| Category | Annual Cost |
|----------|-------------|
| **Algorand Blockchain** | $20 |
| **Groq API (Free Tier)** | $0 |
| **Tavily API (Free Tier)** | $0 |
| **Hosting (Hetzner CX11)** | $55 |
| **Domain + SSL** | $13 |
| **Database (JSON files)** | $0 |
| **Monitoring (Free tiers)** | $0 |
| **Backup Storage** | $60 |
| **TOTAL** | **$148/year** |

### Standard Production Setup

| Category | Annual Cost |
|----------|-------------|
| **Algorand Blockchain** | $20 |
| **Groq API (Paid Tier)** | $13 |
| **Tavily API (Basic)** | $348 |
| **Hosting (DigitalOcean Standard)** | $144 |
| **Domain + SSL** | $13 |
| **Database (MongoDB Atlas Shared)** | $108 |
| **Monitoring (Free tiers)** | $0 |
| **Backup Storage** | $60 |
| **TOTAL** | **$706/year** |

### Enterprise Production Setup

| Category | Annual Cost |
|----------|-------------|
| **Algorand Blockchain** | $50 |
| **Groq API (Paid Tier)** | $50 |
| **Tavily API (Pro)** | $1,188 |
| **Hosting (AWS/Multi-region)** | $2,400 |
| **Domain + SSL (EV)** | $200 |
| **Database (Supabase Pro)** | $300 |
| **Monitoring (Datadog Pro)** | $180 |
| **Backup Storage** | $120 |
| **Security Audit** | $5,000 |
| **Developer Maintenance** | $24,000 |
| **TOTAL** | **$33,488/year** |

---

## 8. Cost Per Audit Breakdown

### Minimal Setup (10,000 audits/year)

| Component | Cost per Audit |
|-----------|----------------|
| Blockchain transactions | $0.0018 |
| API calls (Groq) | $0.0000 |
| Infrastructure | $0.0055 |
| Storage | $0.0006 |
| **TOTAL** | **$0.0079** |

### Standard Setup (10,000 audits/year)

| Component | Cost per Audit |
|-----------|----------------|
| Blockchain transactions | $0.0018 |
| API calls (Groq + Tavily) | $0.0361 |
| Infrastructure | $0.0144 |
| Database | $0.0108 |
| Storage | $0.0006 |
| **TOTAL** | **$0.0637** |

---

## 9. Scaling Projections

### 100,000 Audits/Year

| Category | Annual Cost |
|----------|-------------|
| Algorand Blockchain | $170 |
| Groq API | $130 |
| Tavily API | $3,480 |
| Hosting (Load Balanced) | $1,200 |
| Database (Pro) | $300 |
| CDN & Caching | $240 |
| **TOTAL** | **$5,520** |

**Cost per audit: $0.055**

### 1,000,000 Audits/Year

| Category | Annual Cost |
|----------|-------------|
| Algorand Blockchain | $1,700 |
| Groq API | $1,300 |
| Tavily API | $34,800 |
| Hosting (Multi-region) | $12,000 |
| Database (Enterprise) | $3,600 |
| CDN & Caching | $2,400 |
| Load Balancer | $1,200 |
| **TOTAL** | **$57,000** |

**Cost per audit: $0.057**

---

## 10. Cost Optimization Strategies

### 10.1 Reduce Blockchain Costs
- **Batch transactions**: Group multiple audits into single transaction
- **Off-chain storage**: Store full data off-chain, only hashes on-chain
- **Selective anchoring**: Only anchor critical/high-value audits

### 10.2 Reduce API Costs
- **Caching**: Cache AI reports for similar audits
- **Rate limiting**: Implement request throttling
- **Fallback logic**: Use deterministic reports when AI unavailable
- **Model selection**: Use smaller models for simple audits

### 10.3 Reduce Infrastructure Costs
- **Auto-scaling**: Scale down during low-traffic periods
- **Reserved instances**: Commit to 1-3 year plans for discounts
- **CDN caching**: Reduce server load with edge caching
- **Compression**: Reduce bandwidth with gzip/brotli

### 10.4 Revenue Models to Offset Costs

| Model | Price per Audit | Revenue (10K audits) | Profit Margin |
|-------|-----------------|---------------------|---------------|
| **Freemium** | $0 (free tier) | $0 | -$148 |
| **Basic** | $0.10 | $1,000 | 85% |
| **Standard** | $0.50 | $5,000 | 86% |
| **Enterprise** | $2.00 | $20,000 | 96% |

---

## 11. Mainnet Migration Checklist

### Pre-Deployment
- [ ] Audit smart contracts (if using)
- [ ] Load testing (1000+ concurrent audits)
- [ ] Security penetration testing
- [ ] Backup and disaster recovery plan
- [ ] Monitoring and alerting setup
- [ ] Rate limiting and DDoS protection
- [ ] Legal compliance review (GDPR, etc.)

### Algorand Mainnet Setup
- [ ] Create mainnet wallet (secure key storage)
- [ ] Fund wallet with operational ALGO (100-1000 ALGO recommended)
- [ ] Create carbon credit token (ASA) on mainnet
- [ ] Test token transfers and burns
- [ ] Configure mainnet node endpoints
- [ ] Update `.env` with mainnet credentials

### API Configuration
- [ ] Upgrade Groq to paid tier (if needed)
- [ ] Upgrade Tavily to paid tier (if needed)
- [ ] Configure API rate limits
- [ ] Set up API key rotation
- [ ] Enable API usage monitoring

### Infrastructure
- [ ] Provision production servers
- [ ] Configure load balancer
- [ ] Set up SSL certificates
- [ ] Configure CDN (Cloudflare)
- [ ] Set up database backups
- [ ] Configure log aggregation

### Monitoring
- [ ] Set up uptime monitoring
- [ ] Configure error tracking (Sentry)
- [ ] Set up performance monitoring
- [ ] Configure alerting (PagerDuty/Slack)
- [ ] Set up cost monitoring

### Documentation
- [ ] API documentation (Swagger/OpenAPI)
- [ ] User guides
- [ ] Admin documentation
- [ ] Incident response playbook
- [ ] Runbook for common issues

---

## 12. Recommended Deployment Path

### Phase 1: MVP Launch (Months 1-3)
- **Budget**: $150/year
- **Setup**: Minimal production (Hetzner + Free APIs)
- **Volume**: 1,000-5,000 audits/year
- **Focus**: Validate product-market fit

### Phase 2: Growth (Months 4-12)
- **Budget**: $700/year
- **Setup**: Standard production (DigitalOcean + Paid APIs)
- **Volume**: 10,000-50,000 audits/year
- **Focus**: Scale infrastructure, add features

### Phase 3: Scale (Year 2+)
- **Budget**: $5,000-50,000/year
- **Setup**: Enterprise production (Multi-region + Premium services)
- **Volume**: 100,000+ audits/year
- **Focus**: Global expansion, enterprise clients

---

## 13. Cost Comparison: Testnet vs Mainnet

| Item | Testnet | Mainnet | Notes |
|------|---------|---------|-------|
| **ALGO Cost** | Free (faucet) | $0.20/ALGO | Real money required |
| **Transaction Fees** | 0.001 ALGO (free) | 0.001 ALGO ($0.0002) | Same fee structure |
| **Token Creation** | 0.1 ALGO (free) | 0.1 ALGO ($0.02) | One-time cost |
| **API Costs** | Same | Same | No difference |
| **Infrastructure** | Same | Same | No difference |
| **Risk** | Zero | Real financial risk | Mainnet = production |

---

## 14. Break-Even Analysis

### Minimal Setup ($148/year)

| Price per Audit | Audits Needed to Break Even |
|-----------------|----------------------------|
| $0.10 | 1,480 audits |
| $0.50 | 296 audits |
| $1.00 | 148 audits |
| $2.00 | 74 audits |

### Standard Setup ($706/year)

| Price per Audit | Audits Needed to Break Even |
|-----------------|----------------------------|
| $0.10 | 7,060 audits |
| $0.50 | 1,412 audits |
| $1.00 | 706 audits |
| $2.00 | 353 audits |

---

## 15. Contact & Support

For questions about mainnet deployment costs:
- **Algorand**: https://developer.algorand.org/
- **Groq**: https://console.groq.com/
- **Tavily**: https://tavily.com/pricing

---

**Last Updated**: January 2025  
**Next Review**: Quarterly (April 2025)

---

## Appendix: Current Market Prices (as of Jan 2025)

| Asset | Price | Source |
|-------|-------|--------|
| ALGO | $0.20 | CoinGecko |
| ETH | $3,200 | CoinGecko |
| BTC | $42,000 | CoinGecko |

**Note**: Cryptocurrency prices are volatile. Update costs based on current market rates.
