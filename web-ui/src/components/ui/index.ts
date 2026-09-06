/**
 * UI kit barrel — CURRENT exports are below. Do not remove them.
 *
 * Intended future kit exports (frontend-redesign manifest; modules do not
 * exist yet — add the export ONLY when its component lands):
 *   Button, IconButton, Input, Textarea, Select, Checkbox, Radio, Switch,
 *   Field, Card, PageHeader, Tabs, Breadcrumbs, Dialog/Modal, ConfirmDialog,
 *   DropdownMenu, Tooltip, Badge family, Toaster, Skeleton, QueryError,
 *   ErrorBoundary, CommandPalette, InstanceSwitcher
 */
export { Modal } from './Modal'
export { ConfirmDialog } from './ConfirmDialog'
export { StatusBadge, RoleBadge, AuthBackendBadge, ProtocolBadge, InstanceStatusBadge, VPNStatusBadge } from './StatusBadge'
export { EmptyState } from './EmptyState'
export { LoadingSpinner, PageSkeleton } from './LoadingSpinner'
export { DataTable, Pagination } from './DataTable'
export { InstanceSelector } from './InstanceSelector'
export { Tooltip } from './Tooltip'
export { DropdownMenu, Trigger as DropdownMenuTrigger, Content as DropdownMenuContent, Item as DropdownMenuItem, Separator as DropdownMenuSeparator } from './DropdownMenu'

// Wave-1 UI kit
export { Button, IconButton, buttonVariants } from './Button'
export { Field, Label } from './Field'
export { Input, Textarea } from './Input'
export { Select } from './Select'
export { Switch, Checkbox, Radio } from './Switch'
export { Card, CardHeader, CardTitle, CardActions, CardBody } from './Card'
export { PageHeader } from './PageHeader'
export { Tabs } from './Tabs'
export { Breadcrumbs } from './Breadcrumbs'
export { Badge } from './StatusBadge'
export { Toaster, toast } from './Toaster'
export { Skeleton, SkeletonText } from './Skeleton'
export { QueryError } from './QueryError'

// Wave-2 shell
export { InstanceSwitcher } from './InstanceSwitcher'
export { ErrorBoundary } from './ErrorBoundary'
export { CommandPalette } from './CommandPalette'
