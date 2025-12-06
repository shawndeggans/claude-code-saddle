# API Documentation Template

Use this template when documenting REST API endpoints.

## Format

```markdown
### Endpoint: [METHOD] /path/to/endpoint

**Description**: [What this endpoint does]

**Authentication**: [Required/Optional/None] - [Type: Bearer, API Key, etc.]

**Request Parameters**:

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| param1    | path     | str  | Yes      | [description] |
| param2    | query    | int  | No       | [description] |

**Request Body** (if applicable):
\`\`\`json
{
  "field": "type - description"
}
\`\`\`

**Response**:
\`\`\`json
{
  "field": "value"
}
\`\`\`

**Error Codes**:
| Code | Reason |
|------|--------|
| 400  | [Bad request reason] |
| 401  | [Unauthorized reason] |
| 404  | [Not found reason] |
```

## Example

### Endpoint: POST /api/v1/users

**Description**: Create a new user account.

**Authentication**: Required - Bearer token with `users:write` scope

**Request Parameters**:

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| X-Idempotency-Key | header | str | No | Key for idempotent requests |

**Request Body**:
```json
{
  "email": "string - User's email address",
  "password": "string - Password (min 8 characters)",
  "name": "string - Display name",
  "role": "string - One of: 'user', 'admin' (default: 'user')"
}
```

**Response** (201 Created):
```json
{
  "id": "usr_abc123",
  "email": "user@example.com",
  "name": "John Doe",
  "role": "user",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Error Codes**:
| Code | Reason |
|------|--------|
| 400  | Invalid email format or password too short |
| 401  | Missing or invalid authentication token |
| 403  | Insufficient permissions to create users |
| 409  | Email already registered |
| 422  | Invalid role value |

**Example Request**:
```bash
curl -X POST https://api.example.com/api/v1/users \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "name": "John Doe"
  }'
```

---

### Endpoint: GET /api/v1/users/{user_id}

**Description**: Retrieve a user by ID.

**Authentication**: Required - Bearer token

**Request Parameters**:

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| user_id   | path     | str  | Yes      | User ID (format: usr_*) |
| fields    | query    | str  | No       | Comma-separated list of fields to return |

**Response** (200 OK):
```json
{
  "id": "usr_abc123",
  "email": "user@example.com",
  "name": "John Doe",
  "role": "user",
  "created_at": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-20T14:22:00Z"
}
```

**Error Codes**:
| Code | Reason |
|------|--------|
| 401  | Missing or invalid authentication token |
| 403  | Not authorized to view this user |
| 404  | User not found |

---

## OpenAPI/Swagger Integration

For projects using OpenAPI, include the YAML specification:

```yaml
paths:
  /api/v1/users:
    post:
      summary: Create a new user
      operationId: createUser
      tags:
        - Users
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUserRequest'
      responses:
        '201':
          description: User created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '400':
          description: Invalid request
        '409':
          description: Email already exists
```
