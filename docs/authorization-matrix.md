# Authorization Matrix (RBAC v2 Transition)

## Purpose
Define role-to-capability mapping during the transition from legacy `admin` checks to capability checks.

## Roles
- `user`: authenticated user with no administrative capabilities.
- `editor`: reserved role with no administrative capabilities.
- `content_admin`: can manage content APIs.
- `ops_admin`: can manage operational APIs.
- `admin`: transitional legacy role; granted both capability sets.

## Capabilities
- `content.manage`: create, update, delete, and view admin content routes.
- `ops.manage`: operational maintenance and diagnostics routes (future phase).

## Mapping
| Role | Capabilities |
|---|---|
| `user` | none |
| `editor` | none |
| `content_admin` | `content.manage` |
| `ops_admin` | `ops.manage` |
| `admin` | `content.manage`, `ops.manage` |

## Transition behavior
- Tokens include `roles`, `capabilities`, and `tv` claims.
- Legacy tokens that include only `roles` remain valid because capability checks derive capabilities from role claims.
- Role changes increment `token_version` so old tokens are revoked.
