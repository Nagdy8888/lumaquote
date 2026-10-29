/**
 * @file shared/api/guards/authorize.ts
 * Authorization guards: `roles()` (RBAC), `permissions()` (DRF-style policy),
 * and `ownership()` (resource-level). All three require `auth()` to run first
 * — their `Needs` type is `{ principal }`, so omitting `auth()` is a compile
 * error. ADMIN bypasses every check.
 */
import { fail } from "@/shared/api/respond"
import type { GuardContext, Guard, Principal } from "@/shared/api/types"

/** The role name that bypasses all authorization checks. */
const ADMIN_ROLE = "admin"

/**
 * Whether the principal holds the admin role (case-insensitive).
 *
 * @param principal - the authenticated caller
 * @returns true if the caller is an admin
 */
export function isAdmin(principal: Principal): boolean {
  return principal.roles.some(function isAdminRole(role) {
    return role.toLowerCase() === ADMIN_ROLE
  })
}

/**
 * Require one of `allowed` roles (admin always passes). With no arguments, only
 * admins pass. Returns 403 when the role is insufficient.
 *
 * @param allowed - permitted role names (case-insensitive)
 * @returns a guard that requires an authenticated principal
 */
export function roles(...allowed: string[]): Guard<{ principal: Principal }, object> {
  const wanted = allowed.map(function lower(role) {
    return role.toLowerCase()
  })
  return {
    name: "roles",
    run(ctx) {
      const { principal } = ctx
      const granted =
        isAdmin(principal) ||
        principal.roles.some(function hasRole(role) {
          return wanted.includes(role.toLowerCase())
        })
      if (!granted) {
        return fail(ctx, 403, "forbidden", "Insufficient role")
      }
    },
  }
}

/**
 * Require all of `required` permissions (admin always passes). Returns 403 when
 * any permission is missing. Models DRF's `permission_classes` granularity.
 *
 * @param required - permission keys the caller must hold
 * @returns a guard that requires an authenticated principal
 */
export function permissions(...required: string[]): Guard<{ principal: Principal }, object> {
  return {
    name: "permissions",
    run(ctx) {
      const granted = ctx.principal.permissions ?? []
      const allowed =
        isAdmin(ctx.principal) ||
        required.every(function has(permission) {
          return granted.includes(permission)
        })
      if (!allowed) {
        return fail(ctx, 403, "forbidden", "Missing required permission")
      }
    },
  }
}

/** What an {@link ownership} loader resolves: the resource and its owner. */
export interface OwnedResource<R> {
  /** The id of the resource's owner. */
  ownerId: string
  /** The loaded resource, exposed to the handler as `ctx.resource`. */
  resource: R
}

/**
 * Require the principal to own the addressed resource (admins bypass). `load`
 * fetches the resource and returns its owner id; returning `null` yields 404.
 * On success the resource is added to the context as `{ resource }`.
 *
 * @typeParam R - the loaded resource type
 * @param load - resolves the resource + owner from the request/params
 * @returns a guard that requires an authenticated principal and adds `{ resource }`
 */
export function ownership<R>(
  load: (ctx: GuardContext & { principal: Principal }) => Promise<OwnedResource<R> | null>,
): Guard<{ principal: Principal }, { resource: R }> {
  return {
    name: "ownership",
    async run(ctx) {
      const found = await load(ctx)
      if (found === null) {
        return fail(ctx, 404, "not_found", "Resource not found")
      }
      if (found.ownerId !== ctx.principal.id && !isAdmin(ctx.principal)) {
        return fail(ctx, 403, "forbidden", "You do not own this resource")
      }
      return { resource: found.resource }
    },
  }
}
