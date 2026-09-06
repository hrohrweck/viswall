import { z } from 'zod'

/* -------------------------------------------------------------------------- */
/*  Shared predicates                                                          */
/* -------------------------------------------------------------------------- */

const IPV4_OR_CIDR_REGEX =
  /^(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}(\/(3[0-2]|[12]?\d))?$/

const isIpv4OrCidr = (value: string): boolean => IPV4_OR_CIDR_REGEX.test(value)

const isIpv6Address = (value: string): boolean => {
  try {
    new URL(`http://[${value}]/`)
    return true
  } catch {
    return false
  }
}

const isIpv6OrCidr = (value: string): boolean => {
  const [address, prefix] = value.split('/')
  if (!isIpv6Address(address)) return false
  if (prefix === undefined) return true
  return /^\d{1,3}$/.test(prefix) && Number(prefix) <= 128
}

const HOSTNAME_LABEL_REGEX = /^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$/

const isHostname = (value: string): boolean =>
  value.length >= 1 &&
  value.length <= 253 &&
  value.split('.').every((label) => HOSTNAME_LABEL_REGEX.test(label))

const splitList = (value: string): string[] =>
  value.split(',').map((item) => item.trim()).filter(Boolean)

/* -------------------------------------------------------------------------- */
/*  Zod primitives                                                             */
/* -------------------------------------------------------------------------- */

/** IPv4 address, optionally with a CIDR prefix (e.g. `192.0.2.10`, `10.0.0.0/8`). */
export const ipv4OrCidr = z
  .string()
  .refine(isIpv4OrCidr, 'Enter a valid IPv4 address or CIDR (e.g. 192.0.2.10 or 10.0.0.0/8)')

/** IPv6 address, optionally with a CIDR prefix (e.g. `2001:db8::1`, `fd00::/64`). */
export const ipv6OrCidr = z
  .string()
  .refine(isIpv6OrCidr, 'Enter a valid IPv6 address or CIDR (e.g. 2001:db8::1 or fd00::/64)')

/** Either an IPv4 or an IPv6 address/CIDR, with a single readable message. */
export const anyIpOrCidr = z
  .string()
  .refine(
    (value) => isIpv4OrCidr(value) || isIpv6OrCidr(value),
    'Enter a valid IP address or CIDR',
  )

/** Comma-separated list of IP addresses ('' and trailing commas allowed). */
export const ipList = z
  .string()
  .refine(
    (value) => splitList(value).every((item) => isIpv4OrCidr(item) || isIpv6OrCidr(item)),
    'Enter valid IP addresses, comma separated',
  )

/** Port or port-range list as used by firewall service ports (e.g. `80, 443 or 1000-2000`). */
export const portRange = z
  .string()
  .refine((value) => {
    const parts = value.split(',').map((part) => part.trim()).filter(Boolean)
    if (parts.length === 0) return false
    return parts.every((part) => {
      const match = /^(\d{1,5})(?:-(\d{1,5}))?$/.exec(part)
      if (!match) return false
      const start = Number(match[1])
      const end = match[2] === undefined ? undefined : Number(match[2])
      if (start > 65535) return false
      if (end === undefined) return true
      return end <= 65535 && end >= start
    })
  }, 'Enter ports as 80, 443 or 1000-2000')

/** Colon-separated hex octets — matches MAC (6 octets) and DUID-LL (10+ octets) forms. */
export const macAddress = z
  .string()
  .regex(
    /^(?:[0-9A-Fa-f]{2}:){5,15}[0-9A-Fa-f]{2}$/,
    'Enter a valid MAC address or DUID (e.g. 52:54:00:12:34:56)',
  )

/** RFC-1123 hostname — dot-separated labels, no leading/trailing hyphens. */
export const hostname = z
  .string()
  .refine(isHostname, 'Enter a valid hostname (e.g. edge-berlin-01)')

/** Domain name — hostname with at least two dot-separated labels (e.g. `example.internal`). */
export const domainName = z
  .string()
  .refine(
    (value) => value.split('.').length >= 2 && isHostname(value),
    'Enter a valid domain name (e.g. example.internal)',
  )

/** Email address. */
export const email = z.string().email('Enter a valid email address')

/** Required name — rejects empty and whitespace-only strings. */
export const nonEmptyName = z.string().trim().min(1, 'Name is required')

/** Non-negative whole-number string (for `type="number"` inputs kept as strings). */
export const intString = (message = 'Enter a whole number'): z.ZodString =>
  z.string().regex(/^\d+$/, message)
