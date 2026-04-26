# @viswall/sdk

TypeScript SDK for the Viswall distributed security appliance platform.

## Installation

```bash
npm install @viswall/sdk
```

## Usage

```typescript
import { ViswallClient } from '@viswall/sdk';

const client = new ViswallClient({
  baseURL: 'https://viswall.example.com',
  token: 'your-jwt-token',
});

// Auth
const me = await client.auth.me();

// Instances
const instances = await client.instances.list();
const newInstance = await client.instances.create({
  name: 'edge-01',
  hostname: '10.0.0.10',
});

// Firewall
const rules = await client.firewall.listRules(instance.id);

// DHCP
const servers = await client.dhcp.listServers(1);
const subnet = await client.dhcp.createSubnet(1, {
  name: 'lan-v4',
  subnet: '192.168.10.0/24',
  type: 'v4',
});
```

## Resources

- `client.auth` — Authentication
- `client.instances` — Instance management
- `client.firewall` — Firewall rules
- `client.routing` — Policy routing
- `client.mail` — Mail domains and users
- `client.metrics` — Metrics and monitoring
- `client.audit` — Audit logs
- `client.vpn` — VPN servers and clients
- `client.dhcp` — DHCP servers, subnets, pools, reservations, options, and leases
- `client.assistant` — AI assistant
- `client.groupware` — SOGo groupware

## Error Handling

```typescript
import { AuthenticationError, NotFoundError } from '@viswall/sdk';

try {
  await client.instances.get(999);
} catch (error) {
  if (error instanceof NotFoundError) {
    console.log('Instance not found');
  }
}
```

## Development

```bash
cd sdk/typescript
npm install
npm run generate-types  # Regenerate types from OpenAPI spec
npm run type-check      # TypeScript check
npm run test            # Run tests
npm run build           # Build
```

## License

MIT
