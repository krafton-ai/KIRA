---
name: it-role-expert
description: Provides role-specific expertise for 26+ IT company positions. Use when responding from a specific role's perspective, providing role-based advice, or when specialized knowledge is needed for engineering, product, design, data, marketing, sales, operations, HR, legal, finance, leadership, or academic functions.
---

# IT Role Expert

## Overview

This skill provides concise, role-specific guidance for 26+ IT company positions. Each role has a reference file with responsibilities, technical knowledge, decision-making frameworks, and best practices.

**When to use**: Responding as a specific role, providing role-specific advice, understanding role priorities and workflows, or when general professional judgment is needed (use General Colleague).

## Available Roles (26 total)

### Engineering (8 roles)
- **Frontend Engineer** - UI development, performance, accessibility, browser compatibility
- **Backend Engineer** - APIs, databases, scalability, security, server-side logic
- **DevOps Engineer** - CI/CD, infrastructure as code, monitoring, reliability, cloud
- **Data Engineer** - Data pipelines, ETL/ELT, data quality, warehouses
- **Mobile Engineer** - iOS/Android native or cross-platform apps
- **QA Engineer** - Testing strategy, automation, quality assurance
- **Security Engineer** - Security assessments, vulnerability management, compliance
- **AI Engineer (ML Engineer)** - Production ML systems, MLOps, model deployment, optimization

### Product & Design (4 roles)
- **Product Manager** - Strategy, roadmaps, prioritization, metrics, requirements
- **UX Designer** - User research, wireframes, prototypes, usability testing
- **UI Designer** - Visual design, design systems, branding, iconography
- **Product Designer** - End-to-end design (UX + UI combined)

### Data & Analytics (2 roles)
- **Data Analyst** - SQL, visualization, statistical analysis, dashboards, A/B testing
- **Data Scientist** - Machine learning, predictive modeling, feature engineering, deployment

### Marketing & Sales (4 roles)
- **Marketing Manager** - Campaign management, multi-channel strategy, metrics, budget
- **Content Marketer** - Content creation, SEO, distribution, engagement
- **Growth Marketer** - Rapid experimentation, funnel optimization, viral growth
- **Sales (Account Executive)** - Lead qualification, demos, closing deals, consultative selling

### Operations (2 roles)
- **Customer Success Manager** - Onboarding, retention, expansion, customer health
- **Operations Manager** - Process optimization, resource allocation, vendor management

### HR & Admin (2 roles)
- **HR Manager** - Recruitment, performance, compensation, compliance, culture
- **Recruiter** - Sourcing, screening, candidate experience, hiring efficiency

### Finance & Legal (2 roles)
- **Legal Counsel** - Contracts, compliance, IP protection, data privacy, risk management
- **Finance Manager** - FP&A, budgeting, forecasting, financial reporting, cash flow

### Leadership (2 roles)
- **CEO** - Vision, strategy, fundraising, board management, culture, stakeholder communication
- **CTO** - Technology strategy, engineering leadership, architecture, technical hiring

### Academic (1 role)
- **Research Paper Writer** - Academic writing, paper structure, methodology, peer review

### General (1 role) - **DEFAULT**
- **General Colleague** - Use when no specialized expertise is needed. Applies general professional skills, common sense, and cross-functional awareness. The default fallback for general workplace scenarios.

## Usage Instructions

**Step 1**: Identify the appropriate role based on the query or user's request.

**Step 2**: Read the corresponding reference file in `references/[category]/[role].md`

**Step 3**: Apply the role's knowledge, decision frameworks, and best practices to formulate the response.

**Examples**:
- "How should we prioritize these features?" → Read `product-design/product-manager.md`
- "Act as a frontend engineer and review this code" → Read `engineering/frontend-engineer.md`
- "What should our hiring process look like?" → Read `hr-admin/hr-manager.md`
- "Help me draft this vendor contract" → Read `finance-legal/legal-counsel.md`
- "Help me write the introduction for my research paper" → Read `academic/research-paper-writer.md`
- "General advice on workplace communication" → Read `general/general-colleague.md`

## Reference File Locations

```
references/
├── engineering/
│   ├── frontend-engineer.md
│   ├── backend-engineer.md
│   ├── devops-engineer.md
│   ├── data-engineer.md
│   ├── mobile-engineer.md
│   ├── qa-engineer.md
│   ├── security-engineer.md
│   └── ai-engineer.md
├── product-design/
│   ├── product-manager.md
│   ├── ux-designer.md
│   ├── ui-designer.md
│   └── product-designer.md
├── data-analytics/
│   ├── data-analyst.md
│   └── data-scientist.md
├── marketing-sales/
│   ├── marketing-manager.md
│   ├── content-marketer.md
│   ├── growth-marketer.md
│   └── sales.md
├── operations/
│   ├── customer-success.md
│   └── operations-manager.md
├── hr-admin/
│   ├── hr-manager.md
│   └── recruiter.md
├── finance-legal/
│   ├── legal-counsel.md
│   └── finance-manager.md
├── leadership/
│   ├── ceo.md
│   └── cto.md
├── academic/
│   └── research-paper-writer.md
└── general/
    └── general-colleague.md (DEFAULT)
```

## Important Notes

- **Focus on expertise, not persona**: Provides professional knowledge and decision-making frameworks, not communication styles or tone
- **Multiple roles may apply**: Some questions benefit from multiple perspectives (e.g., PM + UX for product design)
- **General Colleague as default**: When no specialized expertise is needed, use the General Colleague perspective for practical, common-sense guidance
- **Adapt to context**: Apply role knowledge to specific situations and constraints
- **Cross-functional awareness**: Understand how roles interact and their different priorities
