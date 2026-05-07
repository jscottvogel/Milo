#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';

import { DatabaseStack } from '../lib/database-stack';
import { IdentityStack } from '../lib/identity-stack';

const app = new cdk.App();
const mode = app.node.tryGetContext('mode') || 'poc';

new DatabaseStack(app, `MiloDatabaseStack-${mode}`, { mode });
new IdentityStack(app, `MiloIdentityStack-${mode}`, { mode });
