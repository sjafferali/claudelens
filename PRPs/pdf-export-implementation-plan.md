# PDF Export Implementation Plan

## Overview
Implement PDF export functionality to provide formatted, printable reports of conversation data.

## Technology Choice
**ReportLab** - Industry standard for Python PDF generation
- Open source version available
- Good async support with aiofiles
- Rich formatting capabilities
- Alternative: WeasyPrint (for HTML to PDF)

## Implementation Steps

### Phase 1: Basic PDF Generation (Week 1)

#### 1.1 Install Dependencies
```toml
# backend/pyproject.toml
reportlab = "^4.0.0"
```

#### 1.2 Create PDF Service
```python
# backend/app/services/pdf_service.py

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
from typing import AsyncGenerator

class PDFExportService:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()

    def setup_custom_styles(self):
        """Define custom styles for conversations."""
        self.styles.add(ParagraphStyle(
            name='UserMessage',
            parent=self.styles['Normal'],
            leftIndent=0,
            rightIndent=20,
            backColor=colors.lightblue,
            borderPadding=10,
        ))

        self.styles.add(ParagraphStyle(
            name='AssistantMessage',
            parent=self.styles['Normal'],
            leftIndent=20,
            rightIndent=0,
            backColor=colors.lightgrey,
            borderPadding=10,
        ))

    async def generate_conversation_pdf(
        self,
        sessions: List[Dict],
        options: Dict
    ) -> AsyncGenerator[bytes, None]:
        """Generate PDF from conversation data."""

        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        # Build content
        story = []

        # Title page
        story.append(Paragraph("ClaudeLens Export Report", self.styles['Title']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", self.styles['Normal']))
        story.append(Spacer(1, 24))

        # Summary statistics
        if options.get('includeMetadata', True):
            summary_data = [
                ['Total Sessions', str(len(sessions))],
                ['Date Range', f"{sessions[0]['date']} - {sessions[-1]['date']}"],
                ['Total Cost', f"${sum(s.get('cost', 0) for s in sessions):.2f}"],
            ]

            summary_table = Table(summary_data, colWidths=[2*inch, 3*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 24))

        # Conversations
        for session in sessions:
            # Session header
            story.append(Paragraph(f"Session: {session.get('title', 'Untitled')}", self.styles['Heading2']))
            story.append(Paragraph(f"Date: {session.get('date', 'Unknown')}", self.styles['Normal']))
            story.append(Spacer(1, 12))

            # Messages
            if options.get('includeMessages', True):
                for message in session.get('messages', []):
                    style = 'UserMessage' if message['type'] == 'user' else 'AssistantMessage'

                    # Format message content
                    content = self.format_message_content(message['content'])
                    story.append(Paragraph(content, self.styles[style]))
                    story.append(Spacer(1, 6))

            # Page break between sessions
            story.append(PageBreak())

        # Build PDF
        doc.build(story)

        # Yield PDF content in chunks
        buffer.seek(0)
        while True:
            chunk = buffer.read(8192)
            if not chunk:
                break
            yield chunk

    def format_message_content(self, content: str) -> str:
        """Format message content for PDF rendering."""
        # Escape special characters
        content = content.replace('&', '&amp;')
        content = content.replace('<', '&lt;')
        content = content.replace('>', '&gt;')

        # Convert markdown-style code blocks to monospace
        import re
        content = re.sub(r'```(.*?)```', r'<font name="Courier">\1</font>', content, flags=re.DOTALL)
        content = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', content)

        # Convert line breaks
        content = content.replace('\n', '<br/>')

        return content
```

### Phase 2: Enhanced Formatting (Week 2)

#### 2.1 Add Charts and Visualizations
```python
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie

def create_cost_chart(self, sessions: List[Dict]) -> Drawing:
    """Create cost analysis chart."""
    drawing = Drawing(400, 200)

    chart = VerticalBarChart()
    chart.x = 50
    chart.y = 50
    chart.width = 300
    chart.height = 125

    # Prepare data
    dates = [s['date'] for s in sessions[-7:]]  # Last 7 sessions
    costs = [s.get('cost', 0) for s in sessions[-7:]]

    chart.data = [costs]
    chart.categoryAxis.categoryNames = dates

    drawing.add(chart)
    return drawing
```

#### 2.2 Add Code Syntax Highlighting
```python
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

def format_code_block(self, code: str, language: str = 'python') -> str:
    """Format code with syntax highlighting."""
    try:
        lexer = get_lexer_by_name(language)
        formatter = HtmlFormatter(style='colorful')
        highlighted = highlight(code, lexer, formatter)
        return highlighted
    except:
        # Fallback to plain monospace
        return f'<font name="Courier">{code}</font>'
```

### Phase 3: Export Service Integration (Week 2)

#### 3.1 Update Export Service
```python
# backend/app/services/export_service.py

async def generate_pdf_export(
    self,
    job_id: str,
    session_ids: List[str],
    progress_callback: Optional[Callable] = None,
) -> AsyncGenerator[bytes, None]:
    """Generate PDF export."""

    pdf_service = PDFExportService()

    # Fetch sessions
    sessions = []
    for idx, session_id in enumerate(session_ids):
        session_data = await self._fetch_session_with_messages(session_id)
        sessions.append(session_data)

        if progress_callback:
            await progress_callback(job_id, {
                "current": idx + 1,
                "total": len(session_ids),
                "percentage": round((idx + 1) / len(session_ids) * 100, 2),
                "message": f"Preparing session {idx + 1} of {len(session_ids)}",
            })

    # Generate PDF
    async for chunk in pdf_service.generate_conversation_pdf(
        sessions,
        self.export_job.get("options", {})
    ):
        yield chunk
```

### Phase 4: Frontend Updates (Week 3)

#### 4.1 Enable PDF Format
```typescript
// Remove "Coming soon" or disabled state from PDF option
{ key: 'pdf', label: 'PDF', disabled: false }
```

#### 4.2 Add PDF-Specific Options
```typescript
interface PDFOptions {
  pageSize: 'letter' | 'A4';
  includeCharts: boolean;
  includeTOC: boolean;
  syntaxHighlighting: boolean;
}

// Add to export panel when PDF is selected
{format === 'pdf' && (
  <div className="space-y-2">
    <label>Page Size</label>
    <select value={pdfOptions.pageSize} onChange={...}>
      <option value="letter">Letter</option>
      <option value="A4">A4</option>
    </select>

    <label>
      <input type="checkbox" checked={pdfOptions.includeCharts} />
      Include Analytics Charts
    </label>

    <label>
      <input type="checkbox" checked={pdfOptions.includeTOC} />
      Include Table of Contents
    </label>
  </div>
)}
```

### Testing Requirements

1. **Unit Tests**
   - Test PDF generation with various data sizes
   - Verify content formatting and escaping
   - Test chart generation

2. **Integration Tests**
   - Export sessions as PDF
   - Download and open PDF files
   - Verify PDF content matches source data

3. **Visual Tests**
   - Check PDF rendering in different viewers
   - Verify formatting consistency
   - Test with various message content types

## Advanced Features (Future)

1. **Custom Templates**
   - Allow users to upload custom PDF templates
   - Support for company branding

2. **Interactive PDFs**
   - Clickable table of contents
   - Bookmarks for sessions
   - Hyperlinks in content

3. **Multi-language Support**
   - Handle Unicode characters properly
   - Right-to-left text support

## Benefits
- Professional, printable reports
- Offline viewing capability
- Easy sharing with stakeholders
- Compliance/audit documentation

## Estimated Timeline
- **Week 1**: Basic PDF generation
- **Week 2**: Enhanced formatting and charts
- **Week 3**: Frontend integration and testing
- **Total**: 3 weeks

## Risks & Mitigations

- **Risk**: Large PDFs causing memory issues
- **Mitigation**: Stream generation, pagination for large exports

- **Risk**: Complex formatting causing rendering issues
- **Mitigation**: Progressive enhancement, fallback to simple formatting

- **Risk**: Font/encoding issues with international characters
- **Mitigation**: Use Unicode fonts, test with various languages
