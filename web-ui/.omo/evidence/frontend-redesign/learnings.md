## Task 21

- IconButton requires `label` prop (not `title`/`aria-label`); it wraps Tooltip internally
- Radix Tooltip's useSize requires ResizeObserver in jsdom → polyfill in tests
- ConfirmDialog `variant="warning"` with `confirmLabel` for non-delete actions; `impact` for blast-radius
- Per-pane loading/error state prevents stale state flash — each pane independently shows Skeleton or QueryError
- Zone search is client-side filtering on the already-fetched zones list
- Form extraction is pure visual refresh — payload shapes must remain identical to avoid breaking mutation hooks
