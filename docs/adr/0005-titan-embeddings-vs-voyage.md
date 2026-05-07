# ADR 0005: Amazon Titan Embeddings vs Voyage AI

## Status
Accepted

## Context
Milo needs to generate vector embeddings for its Episodic Memory layer (`memory_chunks` table). Our options were Amazon Titan Text Embeddings v2 (native to Bedrock) or Voyage AI (external, highly performant on standard benchmarks).

## Decision
We chose Amazon Titan Text Embeddings v2.

## Consequences

**Positive:**
- **Data Privacy**: Titan is hosted entirely within AWS Bedrock, ensuring customer data (which can be highly sensitive program/strategy info) never leaves the AWS VPC boundary.
- **IAM Integration**: No need to manage external API keys; authentication is handled natively via AWS IAM roles.
- **Latency/Cost**: Calling Bedrock from a Lambda in the same region provides optimal network latency and cost structures that roll up into our single AWS bill.

**Negative:**
- **Benchmark Performance**: While highly capable, Titan v2 may score marginally lower than specialized models like Voyage AI on specific semantic retrieval benchmarks. We mitigate this through strong metadata filtering and hybrid search if needed.
