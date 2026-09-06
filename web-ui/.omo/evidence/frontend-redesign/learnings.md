## Task 20

- VPNServerDetail: MSW 404 sets `isError=true` via React Query — check `!server` BEFORE `isError` to show EmptyState instead of QueryError for not-found
- VPNCreate: Dynamic `text-${p.color}-600` template classNames replaced with static `colorMap` Record — prevents Tailwind purging and enables predictable test assertions on rendered classes
- TabsContent not exported from UI barrel — import directly from `../../components/ui/Tabs`
- Radix DropdownMenu portals render outside jsdom DOM tree — tests cannot click kebab items; verify data presence instead
- ConfirmDialog `impact` prop is the blast-radius secondary line; use for disconnect/revoke consequences
- Button component has no `asChild` prop — use `buttonVariants()` with `<Link>` for styled link-buttons
- Create VPNClient POST needs MSW override in tests (`server.use()`) since shared handlers are read-only

## Task 21

- IconButton requires `label` prop (not `title`/`aria-label`); it wraps Tooltip internally
- Radix Tooltip's useSize requires ResizeObserver in jsdom → polyfill in tests
- ConfirmDialog `variant="warning"` with `confirmLabel` for non-delete actions; `impact` for blast-radius
- Per-pane loading/error state prevents stale state flash — each pane independently shows Skeleton or QueryError
- Zone search is client-side filtering on the already-fetched zones list
- Form extraction is pure visual refresh — payload shapes must remain identical to avoid breaking mutation hooks
