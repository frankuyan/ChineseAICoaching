# Admin Lesson Generation Feature

This document describes the new AI-powered lesson generation feature for administrators.

## Overview

Admins can now generate coaching lessons using AI by uploading documents in various formats and providing prompts. The system includes a complete workflow for drafting, reviewing, editing, and publishing lessons to users.

## Features

### 1. AI-Powered Lesson Generation
- Upload multiple documents (PDF, DOCX, TXT, MD, JSON, CSV, XLSX, etc.)
- Provide a prompt describing the desired lesson
- AI analyzes documents and generates comprehensive lesson content
- Supports multiple AI providers (OpenAI, Anthropic Claude, DeepSeek)

### 2. Lesson Workflow States
Lessons progress through the following states:
- **DRAFT** - Initial generated lesson, can be edited and refined
- **IN_REVIEW** - Lesson submitted for review
- **PUBLISHED** - Lesson is live and visible to all users
- **ARCHIVED** - Lesson is no longer active

### 3. Admin-Only Access
- Only users with `is_admin=True` or `is_superuser=True` can access admin endpoints
- Regular users only see published lessons
- Complete separation between admin management and user-facing content

## Database Schema Changes

### User Model
Added field:
- `is_admin` (Boolean) - Designates admin users
- `created_lessons` relationship - Links to lessons created by this admin

### Lesson Model
New fields:
- `status` (LessonStatus enum) - Current workflow state
- `created_by` (Foreign Key to User) - Admin who created the lesson
- `reviewed_by` (Foreign Key to User) - Admin who reviewed/published
- `published_at` (DateTime) - Timestamp of publication
- `generation_prompt` (Text) - Original prompt used for generation
- `source_documents` (JSON) - References to source documents

## API Endpoints

### Admin Lesson Management

#### 1. Generate Lesson from Documents
```
POST /admin/lessons/generate
```
**Auth Required:** Admin only
**Content-Type:** multipart/form-data

**Parameters:**
- `prompt` (required) - Description of the lesson to generate
- `lesson_type` (required) - Type of lesson (business_practice, leadership, etc.)
- `ai_model` (optional) - AI provider to use (default: anthropic)
- `additional_context` (optional) - Extra context for generation
- `files` (required) - One or more document files

**Supported File Formats:**
- Text: `.txt`, `.md`
- PDF: `.pdf`
- Word: `.docx`, `.doc`
- Spreadsheet: `.xlsx`, `.xls`, `.csv`
- Data: `.json`

**Response:**
```json
{
  "lesson_id": 123,
  "title": "Generated Lesson Title",
  "status": "draft",
  "message": "Lesson generated successfully from 3 document(s)"
}
```

**Example Usage:**
```bash
curl -X POST "http://localhost:8000/admin/lessons/generate" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -F "prompt=Create a lesson about effective client communication in consulting" \
  -F "lesson_type=client_interaction" \
  -F "ai_model=anthropic" \
  -F "files=@client_guide.pdf" \
  -F "files=@best_practices.docx"
```

#### 2. Refine Existing Lesson
```
POST /admin/lessons/{lesson_id}/refine
```
**Auth Required:** Admin only

**Request Body:**
```json
{
  "refinement_prompt": "Make the scenario more specific to consulting industry",
  "ai_model": "anthropic"
}
```

**Use Cases:**
- Adjust difficulty level
- Add more specific examples
- Modify tone or style
- Incorporate feedback

#### 3. Update Lesson Status
```
PATCH /admin/lessons/{lesson_id}/status
```
**Auth Required:** Admin only

**Request Body:**
```json
{
  "status": "published",
  "notes": "Reviewed and approved for release"
}
```

**Status Transitions:**
- DRAFT → IN_REVIEW
- IN_REVIEW → PUBLISHED
- Any status → ARCHIVED

When publishing, the system automatically:
- Sets `published_at` timestamp
- Records `reviewed_by` admin

#### 4. Manually Update Lesson
```
PUT /admin/lessons/{lesson_id}
```
**Auth Required:** Admin only

Standard lesson update endpoint for manual edits.

#### 5. Get Draft Lessons
```
GET /admin/lessons/drafts
```
**Auth Required:** Admin only

Returns all lessons in DRAFT status.

#### 6. Get Lessons In Review
```
GET /admin/lessons/in-review
```
**Auth Required:** Admin only

Returns all lessons in IN_REVIEW status.

#### 7. Get All Lessons (Admin View)
```
GET /admin/lessons/all?status_filter=draft
```
**Auth Required:** Admin only

View all lessons regardless of status. Optional status filter.

#### 8. Get Supported Formats
```
GET /admin/lessons/supported-formats
```
**Auth Required:** Admin only

Returns list of supported document formats for upload.

### User-Facing Endpoints (Modified)

#### Get Lessons
```
GET /lessons
```
**Changed:** Now only returns lessons with `status=PUBLISHED`

Regular users cannot see draft, in-review, or archived lessons.

#### Get Single Lesson
```
GET /lessons/{lesson_id}
```
**Changed:** Only returns if `status=PUBLISHED`

Returns 404 if lesson exists but is not published.

## Admin User Management

### Creating Admin Users

Use the provided utility script:

```bash
# Create a new admin user
python create_admin.py create admin_user admin@example.com SecurePassword123 "Admin Name"

# Promote existing user to admin
python create_admin.py promote existing_username

# List all admin users
python create_admin.py list
```

### Manual Database Update
```sql
UPDATE users SET is_admin = TRUE WHERE username = 'username';
```

## Installation & Setup

### 1. Install New Dependencies
```bash
cd backend
pip install -r requirements.txt
```

New packages added:
- `pypdf==4.0.1` - PDF parsing
- `python-docx==1.1.0` - Word document parsing
- `openpyxl==3.1.2` - Excel file parsing

### 2. Update Database Schema

Since the app auto-creates tables, simply restart the backend:
```bash
python -m app.main
```

Or if using Docker:
```bash
docker-compose restart backend
```

### 3. Create Admin User
```bash
python create_admin.py create your_admin admin@yourcompany.com YourPassword "Admin Name"
```

## Workflow Example

### Complete Lesson Creation Process

1. **Upload Documents & Generate**
   ```bash
   POST /admin/lessons/generate
   # Upload company training materials
   # Result: Lesson created with status=DRAFT
   ```

2. **Review Generated Content**
   ```bash
   GET /admin/lessons/drafts
   # Review the generated lesson
   ```

3. **Refine if Needed**
   ```bash
   POST /admin/lessons/123/refine
   # "Add more examples about remote work scenarios"
   ```

4. **Submit for Review**
   ```bash
   PATCH /admin/lessons/123/status
   # Change status to IN_REVIEW
   ```

5. **Final Review & Publish**
   ```bash
   PATCH /admin/lessons/123/status
   # Change status to PUBLISHED
   # Lesson now visible to all users
   ```

6. **Users Access Lesson**
   ```bash
   GET /lessons
   # Regular users see the published lesson
   ```

## Best Practices

### Document Preparation
- Use clear, well-formatted documents
- Combine multiple related documents for richer context
- Include examples and case studies in source materials

### Prompt Writing
- Be specific about learning objectives
- Mention target audience/skill level
- Specify desired format or structure
- Include any constraints (duration, difficulty)

**Good Prompt Example:**
```
Create an intermediate-level lesson about handling difficult client conversations
in consulting. Target audience: consultants with 1-3 years experience.
Focus on de-escalation techniques and maintaining professional relationships.
Duration: 30-45 minutes. Include 3-4 practice scenarios.
```

### AI Model Selection
- **Anthropic Claude**: Best for nuanced, professional content
- **OpenAI GPT-4**: Good general-purpose generation
- **DeepSeek**: Cost-effective alternative

### Review Process
1. Check factual accuracy
2. Verify learning objectives are clear
3. Ensure scenarios are realistic
4. Test difficulty level appropriateness
5. Review for bias or inappropriate content

## Troubleshooting

### "Admin access required" Error
- Verify your user has `is_admin=True`
- Check JWT token is valid
- Confirm you're using correct authentication header

### Document Parsing Failures
- Ensure file format is supported
- Check file is not corrupted
- Verify file size is reasonable (<50MB recommended)
- For password-protected files, remove protection first

### AI Generation Issues
- Check API keys are configured in `.env`
- Verify AI provider API quota/limits
- Try with smaller document set
- Simplify prompt if too complex

## Security Considerations

1. **Admin Authorization**: All admin endpoints check `is_admin` or `is_superuser`
2. **Input Validation**: File types validated before processing
3. **Content Review**: Human review step before publishing
4. **Audit Trail**: Tracks who created and reviewed each lesson
5. **File Upload Safety**: Only processes supported, validated formats

## Future Enhancements

Potential additions:
- Bulk lesson generation
- Template-based generation
- Version control for lessons
- Collaborative review workflows
- Analytics on lesson effectiveness
- Auto-translation to multiple languages
- Custom AI model fine-tuning

## Support

For issues or questions:
1. Check this documentation
2. Review API error messages
3. Check logs in `/backend/logs/`
4. Contact development team

---

**Version:** 1.0
**Last Updated:** 2025-01-19
