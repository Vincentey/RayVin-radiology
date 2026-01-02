# Radiology AI Assistant - API Documentation

**Version:** 1.0.0  
**Base URL:** `http://your-domain.com` or `http://localhost:8000`  
**API Prefix:** `/api`

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Endpoints Reference](#endpoints-reference)
   - [Health Check](#health-check)
   - [Authentication Endpoints](#authentication-endpoints)
   - [Analysis Endpoints](#analysis-endpoints)
   - [Study Management](#study-management)
4. [Request/Response Formats](#requestresponse-formats)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)
7. [Code Examples](#code-examples)

---

## Overview

The Radiology AI Assistant API provides endpoints for:
- User authentication and account management
- DICOM file upload and analysis
- AI-powered radiology findings detection
- Clinical recommendation generation
- Study management

### Supported Modalities

| Modality | DICOM Code | Description |
|----------|------------|-------------|
| X-Ray | CR, DX | Chest radiographs, 2D analysis |
| CT | CT | Computed Tomography, 3D analysis |
| MRI | MR | Magnetic Resonance Imaging, 3D analysis |

### Response Format

All API responses are in JSON format:

```json
{
  "field": "value",
  "nested": {
    "field": "value"
  }
}
```

---

## Authentication

### Authentication Method: OAuth2 Bearer Token (JWT)

All protected endpoints require a valid JWT token in the Authorization header:

```
Authorization: Bearer <access_token>
```

### Token Lifetime

- **Access Token:** 60 minutes
- **Password Reset Token:** 30 minutes
- **Email Verification Token:** 24 hours

### User Roles

| Role | Permissions |
|------|-------------|
| `user` | Upload files, view own analyses |
| `radiologist` | All user permissions + analyze studies, view all studies |
| `admin` | All permissions + delete studies, manage users |

---

## Endpoints Reference

### Health Check

#### `GET /health`

Check if the API is running and healthy.

**Authentication:** Not required

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

### Authentication Endpoints

#### `POST /api/auth/signup`

Register a new user account. Sends verification email.

**Authentication:** Not required

**Request Body:**
```json
{
  "username": "newuser",
  "password": "securepassword123",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "user"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| username | string | Yes | 3-50 chars, alphanumeric with underscores/hyphens |
| password | string | Yes | Minimum 8 characters |
| email | string | Yes | Valid email address (for verification) |
| full_name | string | No | Display name |
| role | string | No | "user" or "radiologist" (default: "user") |

**Success Response (201):**
```json
{
  "message": "Account created successfully. Please check your email to verify your account.",
  "user": {
    "username": "newuser",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "user",
    "email_verified": false
  },
  "email_sent": true,
  "note": "You must verify your email before logging in."
}
```

**Error Responses:**
- `400`: Invalid input (username exists, email exists, validation failed)
- `500`: Server error

---

#### `POST /api/auth/token`

Login and obtain access token.

**Authentication:** Not required

**Request Body (form-data):**
```
username: your_username
password: your_password
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Error Responses:**
- `401`: Invalid credentials
- `403`: Email not verified

---

#### `GET /api/auth/me`

Get current authenticated user information.

**Authentication:** Required (any role)

**Response:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "radiologist",
  "email_verified": true
}
```

---

#### `POST /api/auth/forgot-password`

Request a password reset email.

**Authentication:** Not required

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response (always 200 for security):**
```json
{
  "message": "If an account with that email exists, a password reset link has been sent.",
  "note": "The link expires in 30 minutes."
}
```

---

#### `POST /api/auth/reset-password`

Reset password using token from email.

**Authentication:** Not required

**Request Body:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "new_password": "newsecurepassword123"
}
```

**Success Response:**
```json
{
  "message": "Password has been reset successfully. You can now log in with your new password."
}
```

**Error Responses:**
- `400`: Invalid/expired token, password too short

---

#### `POST /api/auth/verify-email`

Verify email address using token from verification email.

**Authentication:** Not required

**Request Body:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success Response:**
```json
{
  "message": "Email verified successfully! You are now logged in.",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

#### `POST /api/auth/resend-verification`

Resend email verification link.

**Authentication:** Not required

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "Verification email has been sent. Please check your inbox.",
  "email_sent": true
}
```

---

#### `GET /api/auth/email-status`

Check if email service is configured.

**Authentication:** Not required

**Response:**
```json
{
  "configured": true,
  "note": "Email service is configured and ready."
}
```

---

### Analysis Endpoints

#### `POST /api/analyze`

Upload DICOM files and run AI analysis.

**Authentication:** Required (user, radiologist, admin)

**Request:** `multipart/form-data`

| Field | Type | Description |
|-------|------|-------------|
| files | file[] | DICOM files (.dcm) |

**Limits:**
- Max file size: 500MB per file
- Max files: 1000 per request

**Success Response:**
```json
{
  "study_id": "550e8400-e29b-41d4-a716-446655440000",
  "modality": "CR",
  "findings": [
    {
      "positive_findings": ["Cardiomegaly", "Pleural_Effusion"],
      "top_predictions": [
        ["Cardiomegaly", 0.87],
        ["Pleural_Effusion", 0.72],
        ["Edema", 0.45],
        ["Atelectasis", 0.32],
        ["No Finding", 0.21]
      ]
    }
  ],
  "recommendations": "EXAMINATION: Chest Radiograph (X-Ray)\n\nTECHNIQUE: Standard PA view, AI-assisted analysis\n\nFINDINGS:\n- Cardiomegaly: Enlarged cardiac silhouette...\n\nIMPRESSION:\n1. Cardiomegaly - recommend echocardiogram...\n\nRECOMMENDATIONS:\n1. Cardiology referral...",
  "urgency": "semi-urgent",
  "status": "completed"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "files=@chest_xray.dcm"
```

---

#### `POST /api/upload`

Upload DICOM files without immediate analysis.

**Authentication:** Required (user, radiologist, admin)

**Request:** `multipart/form-data`

**Response:**
```json
{
  "study_id": "550e8400-e29b-41d4-a716-446655440000",
  "files_uploaded": 156,
  "filenames": ["slice001.dcm", "slice002.dcm", "..."],
  "uploaded_by": "johndoe"
}
```

---

#### `POST /api/analyze/{study_id}`

Analyze a previously uploaded study.

**Authentication:** Required (radiologist, admin)

**Path Parameters:**
- `study_id`: UUID of the uploaded study

**Response:** Same as `/api/analyze`

---

### Study Management

#### `GET /api/studies`

List all uploaded studies.

**Authentication:** Required (radiologist, admin)

**Response:**
```json
{
  "studies": [
    {
      "study_id": "550e8400-e29b-41d4-a716-446655440000",
      "file_count": 156
    },
    {
      "study_id": "550e8400-e29b-41d4-a716-446655440001",
      "file_count": 1
    }
  ],
  "total": 2
}
```

---

#### `DELETE /api/study/{study_id}`

Delete a study and all associated files.

**Authentication:** Required (admin only)

**Path Parameters:**
- `study_id`: UUID of the study to delete

**Response:**
```json
{
  "status": "deleted",
  "study_id": "550e8400-e29b-41d4-a716-446655440000",
  "deleted_by": "admin"
}
```

---

## Request/Response Formats

### Standard Success Response

```json
{
  "data": {},
  "message": "Operation successful"
}
```

### Standard Error Response

```json
{
  "detail": "Error description"
}
```

### Pagination (where applicable)

```json
{
  "items": [],
  "total": 100,
  "page": 1,
  "per_page": 20
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 413 | Payload Too Large |
| 422 | Unprocessable Entity |
| 429 | Too Many Requests (rate limited) |
| 500 | Internal Server Error |

### Error Response Format

```json
{
  "detail": "Descriptive error message"
}
```

### Validation Error Format

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Rate Limiting

| Endpoint | Limit |
|----------|-------|
| `/api/auth/token` | 10 requests/minute |
| `/api/auth/forgot-password` | 3 requests/minute |
| `/api/analyze` | 20 requests/minute |
| Other endpoints | 100 requests/minute |

When rate limited, you'll receive:
```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

---

## Code Examples

### Python (requests)

```python
import requests

BASE_URL = "http://localhost:8000"

# Login
response = requests.post(f"{BASE_URL}/api/auth/token", data={
    "username": "admin",
    "password": "admin123"
})
token = response.json()["access_token"]

# Headers for authenticated requests
headers = {"Authorization": f"Bearer {token}"}

# Upload and analyze DICOM
with open("chest_xray.dcm", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/api/analyze",
        headers=headers,
        files={"files": f}
    )
    
result = response.json()
print(f"Modality: {result['modality']}")
print(f"Findings: {result['findings']}")
print(f"Urgency: {result['urgency']}")
```

### JavaScript (fetch)

```javascript
const BASE_URL = 'http://localhost:8000';

// Login
async function login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await fetch(`${BASE_URL}/api/auth/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
    });
    
    const data = await response.json();
    return data.access_token;
}

// Analyze DICOM
async function analyzeDicom(file, token) {
    const formData = new FormData();
    formData.append('files', file);
    
    const response = await fetch(`${BASE_URL}/api/analyze`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
    });
    
    return await response.json();
}

// Usage
const token = await login('admin', 'admin123');
const fileInput = document.getElementById('fileInput');
const result = await analyzeDicom(fileInput.files[0], token);
console.log(result);
```

### cURL

```bash
# Login
TOKEN=$(curl -s -X POST "http://localhost:8000/api/auth/token" \
    -d "username=admin&password=admin123" | jq -r '.access_token')

# Check current user
curl -H "Authorization: Bearer $TOKEN" \
    "http://localhost:8000/api/auth/me"

# Upload and analyze
curl -X POST "http://localhost:8000/api/analyze" \
    -H "Authorization: Bearer $TOKEN" \
    -F "files=@chest_xray.dcm"

# List studies
curl -H "Authorization: Bearer $TOKEN" \
    "http://localhost:8000/api/studies"

# Delete study (admin only)
curl -X DELETE "http://localhost:8000/api/study/STUDY_ID" \
    -H "Authorization: Bearer $TOKEN"
```

---

## OpenAPI/Swagger UI

Interactive API documentation is available at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`

---

## WebSocket Support (Future)

Real-time analysis progress updates via WebSocket (planned):

```
ws://localhost:8000/ws/analysis/{study_id}
```

---

## SDK Libraries (Planned)

- Python: `pip install radiology-ai-client`
- JavaScript: `npm install radiology-ai-client`

---

## Support

For API support or issues:
- **Documentation:** This file
- **Interactive Docs:** `/docs`
- **Email:** support@your-domain.com

---

## Changelog

### Version 1.0.0
- Initial release
- Authentication endpoints (signup, login, password reset, email verification)
- DICOM analysis endpoints
- Study management endpoints
- Support for X-ray, CT, and MRI modalities

