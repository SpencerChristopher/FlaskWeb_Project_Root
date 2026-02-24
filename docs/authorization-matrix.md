# Authorization Matrix (Modular Monolith v1)

## Purpose
Define the granular permission-based authorization model. This matrix serves as the "Contract" for `src/services/roles.py` and the `AuthzService`.

## Permissions
- `content:manage`: Full administrative control over all content (Create, Edit All, Delete All).
- `content:author`: Control over personal content only (Create, Edit Own, Delete Own).
- `users:manage`: Administrative control over user accounts and role assignments.
- `system:view_logs`: Access to system diagnostics, audit trails, and application logs.

## Roles & Mapping
The system maps roles to a set of granular permissions.

| Role | Permissions | Description |
| :--- | :--- | :--- |
| **`admin`** | `content:manage`, `users:manage`, `system:view_logs` | System owner with total access. |
| **`author`** | `content:author` | Trusted content creator. |
| **`member`** | `none` | Standard authenticated user (Read-only access). |

## Implementation Rules
1. **Deny by Default:** If a permission check is required but the user role has no matching permission, access is denied.
2. **Resource Focus:** Authorization is checked at the Service layer using the resource ID (e.g., `is_owner(user_id, post_id)` for authors).
3. **Stateless Claims:** Permissions are derived from the `role` claim in the JWT to minimize database lookups, but verified against `token_version` for immediate revocation.
