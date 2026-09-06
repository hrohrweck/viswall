# Canonical Mutation-Toast Pattern

## How it works

Mutation hooks in `src/hooks/useApi.ts` hardcode `onSuccess` (query invalidation)
and accept **no** options from call sites. Call sites add toasts via the **per-call
callbacks** that TanStack Query v5 passes to `mutation.mutate()`:

```ts
mutation.mutate(vars, {
  onSuccess: () => toast.success('…'),
  onError: (e) => toast.error(getErrMsg(e)),
})
```

TanStack v5 runs per-call callbacks **in addition** to the hook-level `onSuccess`,
so invalidation is preserved.

## getErrMsg helper

Located in `src/lib/utils.ts`:

```ts
import { getErrMsg } from '../../lib/utils'
```

Safely extracts a human-readable message from any thrown value:
- Axios errors → `response.data.detail`
- `Error` instances → `.message`
- Strings → as-is
- Anything else → `'An unexpected error occurred'`

## Full example: useCreateFirewallRule

### Before (no toast — silent success)

```tsx
import { useCreateFirewallRule } from '../../hooks/useApi'

function CreateRuleButton() {
  const createRule = useCreateFirewallRule(instanceId)

  const handleClick = () => {
    createRule.mutate({
      name: 'Allow HTTPS',
      action: 'accept',
      protocol: 'tcp',
      dst_port: 443,
    })
  }

  return <Button onClick={handleClick}>Create Rule</Button>
}
```

### After (with toast)

```tsx
import { useCreateFirewallRule } from '../../hooks/useApi'
import { toast } from '../ui/Toaster'
import { getErrMsg } from '../../lib/utils'

function CreateRuleButton() {
  const createRule = useCreateFirewallRule(instanceId)

  const handleClick = () => {
    createRule.mutate(
      {
        name: 'Allow HTTPS',
        action: 'accept',
        protocol: 'tcp',
        dst_port: 443,
      },
      {
        onSuccess: () => toast.success('Firewall rule created'),
        onError: (e) => toast.error(getErrMsg(e)),
      },
    )
  }

  return <Button onClick={handleClick}>Create Rule</Button>
}
```

The hook's own `onSuccess` (query invalidation + refetch) still fires.
The per-call `onSuccess` shows the user a success toast on top of that.

## Rules

1. **Always import `toast` from `../ui/Toaster`**, never directly from `'sonner'`.
   This ensures the same import path works whether the Toaster component is
   mounted in the shell or not (sonner's toast function works without Toaster
   mounted — it just won't render visible toasts until Toaster is present).
2. **Always use `getErrMsg(e)`** in `onError` — never pass the raw error object.
3. **Keep toasts brief**: `'Rule created'`, `'VPN server deleted'`, etc.
4. **No toast on list/detail queries** — only on mutations (create/update/delete/deploy).
