# ADR 0001: Use pgvector over OpenSearch

## Context
We need a vector database to power Milo's semantic and episodic memory layers. Amazon OpenSearch Service is the standard AWS recommendation for vector workloads.

## Decision
We will use `pgvector` inside Aurora Serverless v2 PostgreSQL instead of Amazon OpenSearch Service.

## Rationale
An OpenSearch cluster sized for production workloads starts at >$300/month idle and adds operational complexity. At our scale (<1B vectors), `pgvector` with HNSW indexing is sufficient and adds zero cost beyond Aurora.
