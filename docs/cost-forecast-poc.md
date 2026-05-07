# Milo PoC Cost Forecast

This table outlines the expected monthly AWS costs for the `milo-poc` deployment, adhering to the strict ~$40/month PoC budget constraint.

| Service | Component | Spec | Est. Monthly Cost | Notes |
|---------|-----------|------|-------------------|-------|
| **RDS** | Database | db.t4g.micro (Single-AZ) | ~$13.00 | GP3 Storage (20GB) included. Public access enabled. |
| **Lambda** | API Compute | 1024MB Memory | ~$2.00 | Assumes ~100k requests/month, average 2s execution. |
| **Bedrock** | LLM Inference | Claude 3.5 Haiku / Titan | ~$5.00 | Usage dependent. Haiku is highly cost-effective for PoC volumes. |
| **CloudWatch** | Logs | 5GB ingestion | ~$2.50 | |
| **Cognito** | Auth | < 50k MAUs | $0.00 | Free tier covers 50k MAUs. |
| **S3** | Storage | Standard | ~$1.00 | Minimal footprint for PoC file storage. |
| **Secrets Manager** | Secrets | 1 Secret | $0.40 | DB Credentials. |
| **EventBridge** | Cron | 1 Rule | $0.00 | Covered by free tier. |
| **Total** | | | **~$23.90** | Well within the $40/mo target. |

*Note: Assumes light PoC usage. Actual Bedrock and Lambda costs scale with traffic.*
