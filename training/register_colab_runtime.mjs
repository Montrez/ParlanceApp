#!/usr/bin/env node
import { randomUUID } from 'crypto';
import { ColabClient } from '/tmp/colab-cli-node/dist/colab/client.js';
import { Variant } from '/tmp/colab-cli-node/dist/colab/api.js';
import { AuthManager } from '/tmp/colab-cli-node/dist/auth/auth-manager.js';
import { storeServer } from '/tmp/colab-cli-node/dist/runtime/storage.js';
import { startDaemon } from '/tmp/colab-cli-node/dist/daemon/lifecycle.js';
import { COLAB_API_DOMAIN, COLAB_GAPI_DOMAIN } from '/tmp/colab-cli-node/dist/config.js';

const endpoint = process.argv[2];
if (!endpoint) {
  console.error('Usage: node register_colab_runtime.mjs <endpoint>');
  process.exit(1);
}

const auth = new AuthManager();
await auth.initialize();
if (!auth.isLoggedIn()) {
  console.error('Not logged in. Run: node /tmp/colab-cli-node/dist/index.js auth login --json');
  process.exit(1);
}

const client = new ColabClient(
  new URL(COLAB_API_DOMAIN),
  new URL(COLAB_GAPI_DOMAIN),
  () => auth.getAccessToken(),
  () => auth.logout(),
);

const proxy = await client.refreshConnection(endpoint);
const id = randomUUID();
const server = {
  id,
  label: 'Colab GPU T4 (browser)',
  variant: Variant.GPU,
  accelerator: 'T4',
  endpoint,
  proxyUrl: proxy.url,
  token: proxy.token,
  tokenExpiry: new Date(Date.now() + proxy.tokenExpiresInSeconds * 1000),
  dateAssigned: new Date(),
  kernelName: 'python3',
};
storeServer(server);
await startDaemon(id);
console.log(JSON.stringify({ id, endpoint }));
