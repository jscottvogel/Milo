#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';

import { DatabaseStack } from '../lib/database-stack';
import { IdentityStack } from '../lib/identity-stack';

const app = new cdk.App();
const mode = app.node.tryGetContext('mode') || 'poc';

const env = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: process.env.CDK_DEFAULT_REGION,
};

new DatabaseStack(app, `MiloDatabaseStack-${mode}`, { mode: mode as 'poc' | 'prod', env });
new IdentityStack(app, `MiloIdentityStack-${mode}`, { mode, env });
