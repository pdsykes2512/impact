# AI Assistant Integration Plan - IMPACT Database

**Version:** 1.0
**Date:** 2026-01-01
**Status:** Planning Complete - Ready for Implementation

## Overview

This directive provides a comprehensive plan for integrating Claude Sonnet 4.5 as an AI assistant for natural language querying and report generation in the IMPACT surgical outcomes database. The system will provide a conversational interface for data exploration while maintaining strict role-based access control and read-only database access.

## User Requirements

- **Interface:** Chat with conversation history + ability to save final reports
- **Authentication:** Use logged-in user's credentials (respects RBAC)
- **Permissions:** Read-only database access (no modifications)
- **Output Formats:** In-app display, PDF export, Excel/CSV export, saved report library

## Architecture Overview

```
User → Frontend Chat UI → Backend API → Anthropic Claude API → Database Tools → MongoDB (read-only)
                                                                       ↓
                                                              Filter PII → Return Results
```

---

## Implementation Phases

### Phase 1: Backend AI Service Core (Priority: Critical)

**Timeline:** Week 1-2
**Dependencies:** None

#### 1.1 Create AI Service Layer

**File: `/root/impact/backend/app/services/ai_service.py`** (NEW)

Core service handling Claude API integration:
- Initialize Anthropic client with API key
- Manage conversation context and history
- Implement tool calling framework
- Handle streaming responses
- Enforce user role-based tool permissions

Key components:
```python
class AIService:
    def __init__(self, api_key: str, user_role: UserRole):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.user_role = user_role
        self.tools = self._get_available_tools()

    async def chat(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        context: Optional[dict] = None
    ) -> AIResponse:
        """Main chat method - handles conversation flow"""

    async def _execute_tool_call(
        self,
        tool_name: str,
        tool_input: dict
    ) -> dict:
        """Execute tool function and return results"""

    def _get_available_tools(self) -> List[dict]:
        """Return tool definitions based on user role"""
```

System prompt template:
```python
SYSTEM_PROMPT = """You are an AI assistant for the IMPACT surgical outcomes database, specializing in colorectal cancer and general surgery data analysis.

Context:
- Database contains patients, episodes, treatments (surgeries), tumours, and investigations
- All data is UK NHS colorectal surgery outcomes
- You have read-only access via specific query tools
- User role: {user_role}

Your capabilities:
- Answer questions about surgical outcomes, complications, and quality metrics
- Generate reports comparing surgeons, time periods, or procedures
- Analyze data quality and completeness
- Explain NBOCA/COSD compliance metrics
- Provide statistical summaries and trends

Guidelines:
- Always cite specific numbers and data sources
- Explain medical terminology when appropriate
- Respect data privacy - never expose patient identifiable information
- Be precise about sample sizes and statistical significance
- Suggest relevant visualizations when appropriate

Available tools: {tool_list}
"""
```

---

#### 1.2 Create Database Query Tools

**File: `/root/impact/backend/app/services/ai_tools.py`** (NEW)

Implement 10 core tools Claude can call:

1. **`query_patients(filters, limit)`** - Search patients with aggregations
2. **`query_episodes(filters, limit)`** - Search episodes by clinical criteria
3. **`query_treatments(filters, limit)`** - Search surgical treatments
4. **`query_tumours(filters, limit)`** - Search tumour/pathology data
5. **`calculate_outcome_metrics(date_range, surgeon, urgency)`** - Outcome statistics
6. **`calculate_surgeon_performance(surgeon_name)`** - Surgeon-specific metrics
7. **`get_data_quality_metrics()`** - Field completeness analysis
8. **`get_cosd_completeness(year)`** - NBOCA/COSD compliance tracking
9. **`generate_comparison_report(params)`** - Time period/surgeon comparisons
10. **`search_by_clinical_criteria(criteria)`** - Complex clinical queries

Example tool implementation:
```python
async def query_patients(
    filters: dict,
    limit: int = 100,
    user_role: UserRole = UserRole.VIEWER
) -> dict:
    """
    Query patients collection with filters.

    Args:
        filters: MongoDB filter dict (e.g., {"age": {"$gte": 50}})
        limit: Max results (default 100, max 1000)
        user_role: User's role for permission checking

    Returns:
        {
            "count": int,
            "patients": [
                {
                    "patient_id": str,
                    "age": int,
                    "gender": str,
                    # No NHS number, MRN (encrypted fields)
                }
            ],
            "summary_stats": {
                "avg_age": float,
                "gender_distribution": dict
            }
        }
    """
    db = Database.get_database()
    patients_collection = db.patients

    # Apply limit
    limit = min(limit, 1000)  # Hard limit

    # Execute query
    cursor = patients_collection.find(filters).limit(limit)
    patients = await cursor.to_list(length=limit)

    # Filter PII
    patients = [_filter_pii(p) for p in patients]

    # Calculate summary stats
    summary_stats = {
        "avg_age": sum(p.get("demographics", {}).get("age", 0) for p in patients) / len(patients) if patients else 0,
        "gender_distribution": _calculate_gender_distribution(patients)
    }

    return {
        "count": len(patients),
        "patients": patients,
        "summary_stats": summary_stats
    }

async def calculate_outcome_metrics(
    date_range: Optional[dict] = None,
    surgeon: Optional[str] = None,
    procedure_type: Optional[str] = None,
    urgency: Optional[str] = None
) -> dict:
    """
    Calculate surgical outcome metrics with filters.

    Reuses existing logic from /api/reports/summary endpoint.

    Returns:
        {
            "total_surgeries": int,
            "complication_rate": float,
            "readmission_rate": float,
            "mortality_30d": float,
            "mortality_90d": float,
            "median_los": float,
            "return_to_theatre_rate": float,
            "breakdown": {
                "by_year": {...},
                "by_urgency": {...}
            }
        }
    """
    db = Database.get_database()
    treatments_collection = db.treatments

    # Build query filters
    query = {"treatment_type": "surgery"}

    if date_range:
        query["treatment_date"] = date_range

    if surgeon:
        query["team.primary_surgeon_text"] = surgeon

    if urgency:
        query["classification.urgency"] = urgency

    # Execute query
    treatments = await treatments_collection.find(query).to_list(length=None)

    # Calculate metrics (reuse existing logic from reports.py)
    return _calculate_metrics(treatments)
```

Security features:
- Automatic PII filtering (NHS numbers, MRNs, names, addresses)
- Query result limits (max 1000 records per query)
- Minimum cohort size n≥5 for surgeon-specific queries (prevent re-identification)
- Audit logging of all tool executions

Role-based tool permissions:
```python
ROLE_TOOL_PERMISSIONS = {
    UserRole.ADMIN: [
        "query_patients", "query_episodes", "query_treatments", "query_tumours",
        "calculate_outcome_metrics", "calculate_surgeon_performance",
        "get_data_quality_metrics", "get_cosd_completeness",
        "generate_comparison_report", "search_by_clinical_criteria"
    ],
    UserRole.SURGEON: [
        "query_patients", "query_episodes", "query_treatments", "query_tumours",
        "calculate_outcome_metrics", "calculate_surgeon_performance",
        "get_data_quality_metrics", "get_cosd_completeness",
        "generate_comparison_report", "search_by_clinical_criteria"
    ],
    UserRole.DATA_ENTRY: [
        "query_episodes", "query_treatments",
        "calculate_outcome_metrics", "get_data_quality_metrics",
        "get_cosd_completeness"
    ],
    UserRole.VIEWER: [
        "calculate_outcome_metrics", "get_data_quality_metrics",
        "get_cosd_completeness"
    ]
}
```

---

#### 1.3 Create API Routes

**File: `/root/impact/backend/app/routes/ai.py`** (NEW)

```python
"""
AI Assistant API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from ..auth import get_current_user
from ..services.ai_service import AIService
from ..config import settings
from ..models.ai_conversation import Conversation, Message
from ..models.ai_report import AIReport
from slowapi import Limiter

router = APIRouter(prefix="/api/ai", tags=["ai"])
limiter = Limiter(key_func=lambda: "global")


@router.post("/chat")
@limiter.limit("10/minute")
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Send message to AI and get response.

    Rate limit: 10 requests/minute per user
    """
    ai_service = AIService(
        api_key=settings.anthropic_api_key,
        user_role=current_user["role"]
    )

    response = await ai_service.chat(
        message=request.message,
        conversation_id=request.conversation_id,
        context=request.context
    )

    # Log to audit trail
    await log_ai_query(
        user_id=current_user["_id"],
        conversation_id=response.conversation_id,
        message=request.message,
        tools_used=[tc.tool for tc in response.tool_calls]
    )

    return response


@router.get("/conversations")
async def list_conversations(
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
) -> List[Conversation]:
    """List user's conversation history"""
    db = Database.get_system_database()
    conversations_collection = db.ai_conversations

    cursor = conversations_collection.find({
        "user_id": str(current_user["_id"]),
        "is_archived": False
    }).sort("updated_at", -1).skip(offset).limit(limit)

    conversations = await cursor.to_list(length=limit)
    return conversations


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
) -> Conversation:
    """Get conversation details"""
    db = Database.get_system_database()
    conversations_collection = db.ai_conversations

    conversation = await conversations_collection.find_one({
        "conversation_id": conversation_id,
        "user_id": str(current_user["_id"])
    })

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete conversation"""
    db = Database.get_system_database()
    conversations_collection = db.ai_conversations

    result = await conversations_collection.delete_one({
        "conversation_id": conversation_id,
        "user_id": str(current_user["_id"])
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"status": "deleted"}


@router.post("/reports/save")
async def save_report(
    request: SaveReportRequest,
    current_user: dict = Depends(get_current_user)
) -> AIReport:
    """Save AI-generated report"""
    db = Database.get_system_database()
    reports_collection = db.ai_reports

    report = {
        "report_id": str(uuid.uuid4()),
        "user_id": str(current_user["_id"]),
        "conversation_id": request.conversation_id,
        "title": request.title,
        "description": request.description,
        "content": request.content,
        "content_type": request.content_type or "custom",
        "metadata": request.metadata or {},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_favorite": False,
        "tags": request.tags or []
    }

    await reports_collection.insert_one(report)
    return report


@router.get("/reports")
async def list_reports(
    limit: int = 20,
    offset: int = 0,
    tags: Optional[List[str]] = None,
    current_user: dict = Depends(get_current_user)
) -> List[AIReport]:
    """List saved reports"""
    db = Database.get_system_database()
    reports_collection = db.ai_reports

    query = {"user_id": str(current_user["_id"])}
    if tags:
        query["tags"] = {"$in": tags}

    cursor = reports_collection.find(query).sort("created_at", -1).skip(offset).limit(limit)
    reports = await cursor.to_list(length=limit)
    return reports


@router.get("/reports/{report_id}")
async def get_report(
    report_id: str,
    current_user: dict = Depends(get_current_user)
) -> AIReport:
    """Get report details"""
    db = Database.get_system_database()
    reports_collection = db.ai_reports

    report = await reports_collection.find_one({
        "report_id": report_id,
        "user_id": str(current_user["_id"])
    })

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return report


@router.get("/reports/{report_id}/export/{format}")
async def export_report(
    report_id: str,
    format: str,  # pdf, xlsx, csv
    current_user: dict = Depends(get_current_user)
):
    """Export report to PDF/Excel/CSV"""
    from ..services.report_generator import ReportGenerator

    # Get report
    db = Database.get_system_database()
    reports_collection = db.ai_reports

    report = await reports_collection.find_one({
        "report_id": report_id,
        "user_id": str(current_user["_id"])
    })

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Generate export
    if format == "pdf":
        content = await ReportGenerator.generate_pdf(
            content=report["content"],
            title=report["title"]
        )
        media_type = "application/pdf"
        filename = f"{report['title']}.pdf"
    elif format == "xlsx":
        content = await ReportGenerator.generate_excel(
            content=report["content"],
            title=report["title"]
        )
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"{report['title']}.xlsx"
    elif format == "csv":
        content = await ReportGenerator.generate_csv(
            data=report["content"]
        )
        media_type = "text/csv"
        filename = f"{report['title']}.csv"
    else:
        raise HTTPException(status_code=400, detail="Invalid format")

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.delete("/reports/{report_id}")
async def delete_report(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete report"""
    db = Database.get_system_database()
    reports_collection = db.ai_reports

    result = await reports_collection.delete_one({
        "report_id": report_id,
        "user_id": str(current_user["_id"])
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")

    return {"status": "deleted"}
```

---

#### 1.4 Database Schema Additions

**Collection: `ai_conversations`** (in `impact_system` database)
```python
{
    "_id": ObjectId,
    "conversation_id": str,  # UUID
    "user_id": str,
    "title": str,  # Auto-generated from first message
    "messages": [{
        "role": "user" | "assistant",
        "content": str,
        "timestamp": datetime,
        "tool_calls": [{
            "tool": str,
            "input": dict,
            "output": dict,
            "execution_time_ms": int
        }]
    }],
    "created_at": datetime,
    "updated_at": datetime,
    "is_archived": bool
}
```

Indexes:
- `conversation_id` (unique)
- `user_id`
- `created_at` (descending)

**Collection: `ai_reports`** (in `impact_system` database)
```python
{
    "_id": ObjectId,
    "report_id": str,  # UUID
    "user_id": str,
    "conversation_id": str,
    "title": str,
    "description": str | null,
    "content": dict,  # Structured report data
    "content_type": "outcome_analysis" | "surgeon_comparison" | "data_quality" | "custom",
    "metadata": {
        "date_range": dict | null,
        "filters_applied": dict,
        "generated_by": "ai",
        "model": "claude-sonnet-4.5"
    },
    "created_at": datetime,
    "updated_at": datetime,
    "is_favorite": bool,
    "tags": [str]
}
```

Indexes:
- `report_id` (unique)
- `user_id`
- `created_at` (descending)
- `tags`

---

#### 1.5 Configuration Updates

**File: `/root/impact/.env`** (UPDATE)
```bash
# Anthropic API
ANTHROPIC_API_KEY=sk-ant-api03-...
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
```

**File: `/root/impact/backend/app/config.py`** (UPDATE)
Add to Settings class:
```python
class Settings(BaseSettings):
    # ... existing fields ...

    # Anthropic API
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-sonnet-4-5-20250929"

    # AI Settings
    ai_max_tokens: int = 4096
    ai_rate_limit_per_minute: int = 10
    ai_max_conversation_length: int = 50  # messages
```

**File: `/root/impact/backend/requirements.txt`** (UPDATE)
```
anthropic==0.39.0
reportlab==4.0.7
openpyxl==3.1.2
```

**File: `/root/impact/backend/app/main.py`** (UPDATE)
```python
# Add to imports
from .routes import ..., ai

# Add to router registration
app.include_router(ai.router)
```

---

### Phase 2: Report Generation & Export

**Timeline:** Week 3
**Dependencies:** Phase 1

#### 2.1 Report Generator Service

**File: `/root/impact/backend/app/services/report_generator.py`** (NEW)

```python
"""
Report generation service for PDF, Excel, and CSV exports
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
import csv
import io
from typing import Dict, Any, List


class ReportGenerator:
    @staticmethod
    async def generate_pdf(content: dict, title: str, metadata: dict = None) -> bytes:
        """
        Generate PDF report using ReportLab

        Args:
            content: Structured report data (tables, metrics, text)
            title: Report title
            metadata: Optional metadata (date range, filters, etc.)

        Returns:
            PDF file as bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()

        # Title
        title_para = Paragraph(f"<b>{title}</b>", styles['Title'])
        story.append(title_para)
        story.append(Spacer(1, 0.3 * inch))

        # Metadata section
        if metadata:
            meta_text = f"Generated: {metadata.get('generated_at', 'N/A')}<br/>"
            meta_text += f"Model: {metadata.get('model', 'AI Assistant')}<br/>"
            if metadata.get('date_range'):
                meta_text += f"Date Range: {metadata['date_range']}<br/>"
            meta_para = Paragraph(meta_text, styles['Normal'])
            story.append(meta_para)
            story.append(Spacer(1, 0.2 * inch))

        # Content sections
        if isinstance(content, dict):
            for section_name, section_data in content.items():
                # Section heading
                heading = Paragraph(f"<b>{section_name}</b>", styles['Heading2'])
                story.append(heading)
                story.append(Spacer(1, 0.1 * inch))

                # Handle different content types
                if isinstance(section_data, list) and len(section_data) > 0 and isinstance(section_data[0], dict):
                    # Table data
                    table_data = []
                    # Headers
                    headers = list(section_data[0].keys())
                    table_data.append(headers)
                    # Rows
                    for row in section_data:
                        table_data.append([str(row.get(h, '')) for h in headers])

                    # Create table
                    t = Table(table_data)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(t)
                elif isinstance(section_data, dict):
                    # Key-value pairs
                    for key, value in section_data.items():
                        para = Paragraph(f"<b>{key}:</b> {value}", styles['Normal'])
                        story.append(para)
                else:
                    # Plain text
                    para = Paragraph(str(section_data), styles['Normal'])
                    story.append(para)

                story.append(Spacer(1, 0.2 * inch))

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()


    @staticmethod
    async def generate_excel(content: dict, title: str) -> bytes:
        """
        Generate Excel report using openpyxl

        Args:
            content: Structured report data
            title: Report title

        Returns:
            Excel file as bytes
        """
        wb = openpyxl.Workbook()
        wb.remove(wb.active)  # Remove default sheet

        # Create summary sheet
        summary_sheet = wb.create_sheet(title="Summary")
        summary_sheet['A1'] = title
        summary_sheet['A1'].font = Font(bold=True, size=14)

        row = 3

        # Process content
        if isinstance(content, dict):
            for section_name, section_data in content.items():
                # Section heading
                summary_sheet.cell(row=row, column=1, value=section_name)
                summary_sheet.cell(row=row, column=1).font = Font(bold=True, size=12)
                row += 1

                # Data
                if isinstance(section_data, list) and len(section_data) > 0 and isinstance(section_data[0], dict):
                    # Table data - create new sheet
                    sheet = wb.create_sheet(title=section_name[:31])  # Excel sheet name limit

                    # Headers
                    headers = list(section_data[0].keys())
                    for col_idx, header in enumerate(headers, start=1):
                        cell = sheet.cell(row=1, column=col_idx, value=header)
                        cell.font = Font(bold=True)
                        cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")

                    # Data rows
                    for row_idx, row_data in enumerate(section_data, start=2):
                        for col_idx, header in enumerate(headers, start=1):
                            sheet.cell(row=row_idx, column=col_idx, value=row_data.get(header, ''))

                    # Auto-size columns
                    for column in sheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        sheet.column_dimensions[column_letter].width = adjusted_width

                    # Reference in summary
                    summary_sheet.cell(row=row, column=1, value=f"See '{section_name}' sheet")
                    row += 1

                elif isinstance(section_data, dict):
                    # Key-value pairs
                    for key, value in section_data.items():
                        summary_sheet.cell(row=row, column=1, value=key)
                        summary_sheet.cell(row=row, column=2, value=value)
                        row += 1

                row += 1  # Spacing between sections

        # Save to bytes
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()


    @staticmethod
    async def generate_csv(data: list, filename: str = "export.csv") -> bytes:
        """
        Generate CSV export

        Args:
            data: List of dictionaries (table data)
            filename: Output filename (not used in bytes, for reference)

        Returns:
            CSV file as bytes
        """
        if not data or not isinstance(data, list):
            raise ValueError("Data must be a non-empty list of dictionaries")

        buffer = io.StringIO()

        # Get headers from first row
        headers = list(data[0].keys())

        writer = csv.DictWriter(buffer, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)

        # Convert to bytes
        csv_bytes = buffer.getvalue().encode('utf-8')
        return csv_bytes
```

---

#### 2.2 Pydantic Models

**File: `/root/impact/backend/app/models/ai_conversation.py`** (NEW)

```python
"""
AI Conversation Models
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class ToolCall(BaseModel):
    """Tool call details"""
    tool: str
    input: dict
    output: dict
    execution_time_ms: int


class Message(BaseModel):
    """Chat message"""
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime
    tool_calls: Optional[List[ToolCall]] = None


class ConversationBase(BaseModel):
    """Base conversation model"""
    conversation_id: str
    user_id: str
    title: str
    messages: List[Message]


class ConversationInDB(ConversationBase):
    """Conversation model in database"""
    created_at: datetime
    updated_at: datetime
    is_archived: bool = False


class Conversation(ConversationInDB):
    """Conversation response model"""
    pass


class ChatRequest(BaseModel):
    """Chat request"""
    message: str
    conversation_id: Optional[str] = None
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    """Chat response"""
    response: str
    conversation_id: str
    tool_calls: List[ToolCall]
    metadata: dict
```

**File: `/root/impact/backend/app/models/ai_report.py`** (NEW)

```python
"""
AI Report Models
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class ReportMetadata(BaseModel):
    """Report metadata"""
    date_range: Optional[dict] = None
    filters_applied: dict = {}
    generated_by: str = "ai"
    model: str


class ReportBase(BaseModel):
    """Base report model"""
    report_id: str
    user_id: str
    conversation_id: str
    title: str
    description: Optional[str] = None
    content: dict
    content_type: Literal["outcome_analysis", "surgeon_comparison", "data_quality", "custom"]
    metadata: ReportMetadata


class ReportInDB(ReportBase):
    """Report model in database"""
    created_at: datetime
    updated_at: datetime
    is_favorite: bool = False
    tags: List[str] = []


class AIReport(ReportInDB):
    """Report response model"""
    pass


class SaveReportRequest(BaseModel):
    """Save report request"""
    conversation_id: str
    title: str
    description: Optional[str] = None
    content: dict
    content_type: Optional[str] = None
    metadata: Optional[dict] = None
    tags: Optional[List[str]] = None
```

---

### Phase 3: Frontend Chat Interface

**Timeline:** Week 4
**Dependencies:** Phase 1, Phase 2

#### 3.1 Main AI Assistant Page

**File: `/root/impact/frontend/src/pages/AIAssistantPage.tsx`** (NEW)

See full implementation in the detailed plan. Key features:
- Two-column layout (sidebar + chat)
- Responsive design (mobile/tablet/desktop)
- Message input with Enter to send
- Loading states during AI response
- Error handling and retry
- Conversation management

---

#### 3.2 Chat Components

**File: `/root/impact/frontend/src/components/ai/ChatMessage.tsx`** (NEW)
**File: `/root/impact/frontend/src/components/ai/ConversationSidebar.tsx`** (NEW)
**File: `/root/impact/frontend/src/components/ai/SaveReportModal.tsx`** (NEW)

See detailed specifications in main plan document.

---

#### 3.3 Saved Reports Page

**File: `/root/impact/frontend/src/pages/SavedReportsPage.tsx`** (NEW)

Report library with search, filtering, export capabilities.

---

#### 3.4 API Service & Types

**File: `/root/impact/frontend/src/services/api.ts`** (UPDATE)
**File: `/root/impact/frontend/src/types/ai.ts`** (NEW)

See detailed specifications in main plan document.

---

#### 3.5 Routing & Navigation

**File: `/root/impact/frontend/src/App.tsx`** (UPDATE)
**File: `/root/impact/frontend/src/components/layout/Layout.tsx`** (UPDATE)

Add routes and navigation items for AI assistant pages.

---

## Security & Compliance

### Role-Based Access Control

Tool permissions by role:

| Tool | Admin | Surgeon | Data Entry | Viewer |
|------|-------|---------|------------|--------|
| query_patients | ✓ | ✓ | ✓ | Summary only |
| query_episodes | ✓ | ✓ | ✓ | Summary only |
| query_treatments | ✓ | ✓ | ✓ | Summary only |
| calculate_outcome_metrics | ✓ | ✓ | ✓ | ✓ |
| calculate_surgeon_performance | ✓ | ✓ | ✗ | ✗ |
| get_data_quality_metrics | ✓ | ✓ | ✓ | ✓ |
| get_cosd_completeness | ✓ | ✓ | ✓ | ✓ |

### PII Protection

All AI responses automatically filter:
- NHS numbers (encrypted)
- MRNs (encrypted)
- Patient names
- Addresses
- Phone/email

Minimum cohort size n≥5 for surgeon queries to prevent re-identification.

### Audit Logging

All AI interactions logged to `audit_logs`:
```python
{
    "event_type": "ai_query",
    "user_id": str,
    "conversation_id": str,
    "message": str,
    "tools_used": [str],
    "data_accessed": {
        "collections": [str],
        "record_count": int
    },
    "timestamp": datetime,
    "ip_address": str
}
```

Retention: 1 year minimum

---

## Testing Strategy

### Backend Tests
- Unit tests for AI service and tools
- Integration tests for API routes
- PII filtering tests
- Permission enforcement tests

### Frontend Tests
- Component tests (message rendering, markdown, tables)
- Integration tests (full chat flow)
- Export functionality tests

### E2E Tests
- User query → AI response → export to Excel
- Multi-turn conversation
- Permission-restricted queries

---

## Cost Estimates

**Anthropic API Pricing:**
- Input: ~$3 per million tokens
- Output: ~$15 per million tokens

**Estimated Monthly Cost:**
- 100 users
- 10 queries/day average
- ~$50-150/month

Implement token usage tracking and alerts.

---

## Implementation Order

1. **Week 1-2:** Backend core (AI service, tools, routes, DB schema)
2. **Week 3:** Report generation (PDF/Excel export)
3. **Week 4:** Frontend UI (chat interface, components)
4. **Week 5:** Saved reports (library, search, export)
5. **Week 6:** Security hardening (rate limiting, audit, testing)

**Total Timeline:** 6 weeks for complete implementation

---

## Dependencies & Prerequisites

### External
- Anthropic API key (https://console.anthropic.com/)
- ReportLab (included in requirements.txt)

### Internal
- JWT authentication ✓
- RBAC implementation ✓
- MongoDB collections ✓
- Existing report logic ✓

---

## Success Criteria

- [ ] Users can ask natural language questions
- [ ] AI provides accurate responses with citations
- [ ] Export to PDF/Excel/CSV works
- [ ] Reports can be saved and retrieved
- [ ] Conversation history persists
- [ ] All queries respect user permissions
- [ ] No PII exposure
- [ ] All interactions logged
- [ ] Handles 50+ concurrent users
- [ ] Response time < 10 seconds
- [ ] Works on mobile and desktop

---

## Future Enhancements

- Voice input
- Scheduled reports
- Email alerts
- Interactive dashboards
- Natural language to SQL
- Multi-model support
- Collaborative reports
- External API integration

---

## Notes for Implementation

1. **Start with Phase 1:** Backend AI service is foundation
2. **Test PII filtering thoroughly:** Critical for GDPR/NHS compliance
3. **Monitor API costs:** Set up alerts for usage spikes
4. **Follow existing patterns:** Match architecture of current routes
5. **Reference STYLE_GUIDE.md:** For all frontend components
6. **Update RECENT_CHANGES.md:** Document all changes
7. **Create user documentation:** Help dialog with example queries

---

**End of Directive**
