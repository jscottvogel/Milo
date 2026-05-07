# Milo PoC Deployment Runbook

## Overview
This runbook details how to deploy the Milo Proof-of-Concept (PoC) infrastructure to a fresh AWS account.

## Prerequisites
1. **AWS Account**: An active AWS account.
2. **AWS CLI**: Installed and configured (`aws configure`).
3. **Node.js**: v22+
4. **Python & uv**: Installed.

## Step 1: AWS Activate Credits (Optional)
If deploying for a startup, apply for AWS Activate credits at `https://aws.amazon.com/activate/` to cover initial PoC costs.

## Step 2: Bootstrap CDK
If this is the first time deploying CDK to this account/region:
```bash
npx cdk bootstrap aws://<ACCOUNT_ID>/<REGION>
```

## Step 3: Configure Secrets
The application requires a PostgreSQL database. For PoC, CDK provisions an RDS instance and stores credentials in AWS Secrets Manager.
If using an external DB or migrating, ensure `DATABASE_URL` is set appropriately in Secrets Manager.

## Step 4: Build and Deploy
Navigate to the CDK package and deploy the stacks:

```bash
cd packages/cdk
pnpm install
npx cdk deploy --all -c mode=poc
```

### Deployed Stacks:
- **MiloDatabaseStack-poc**: Provisions VPC and RDS Postgres instance.
- **MiloIdentityStack-poc**: Provisions Cognito User Pool.
- **MiloApiStack-poc**: Provisions the FastAPI Lambda and Function URL.
- **MiloWorkerStack-poc**: Provisions EventBridge cron jobs.
- **MiloWebStack-poc**: Placeholder for frontend.

## Step 5: Verify Deployment
After deployment, the terminal will output the `ApiUrl`. Test it:
```bash
curl <ApiUrl>/v1/health
```

## Step 6: Teardown
To avoid incurring further costs:
```bash
npx cdk destroy --all -c mode=poc
```
