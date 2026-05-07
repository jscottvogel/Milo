#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';

import { DatabaseStack } from '../lib/database-stack';
import { IdentityStack } from '../lib/identity-stack';
import { WorkerStack } from '../lib/worker-stack';
import { ApiStack } from '../lib/api-stack';
import { WebStack } from '../lib/web-stack';
import { ObservabilityStack } from '../lib/observability-stack';

const app = new cdk.App();
const mode: 'poc' | 'prod' = app.node.tryGetContext('mode') === 'prod' ? 'prod' : 'poc';

const env = {
  account: process.env.CDK_DEFAULT_ACCOUNT || process.env.AWS_ACCOUNT_ID,
  region: process.env.CDK_DEFAULT_REGION || process.env.AWS_REGION || 'us-east-1',
};

new DatabaseStack(app, `MiloDatabaseStack-${mode}`, { mode, env });
new IdentityStack(app, `MiloIdentityStack-${mode}`, { mode, env });
new WorkerStack(app, `MiloWorkerStack-${mode}`, { mode, env });
new ApiStack(app, `MiloApiStack-${mode}`, { mode, env });
new WebStack(app, `MiloWebStack-${mode}`, { mode, env });
