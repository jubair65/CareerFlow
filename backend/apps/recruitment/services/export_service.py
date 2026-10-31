"""
Export Service for CareerFlow Recruitment Rooms (US-46).
Supports streaming CSV export and styled Excel (.xlsx) workbook generation
for ranked applicant dossiers with query filtering preservation and ATS schemas.
"""

import csv
import io
import re
from datetime import datetime
from typing import Dict, Any, Generator, List, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from django.utils import timezone
from apps.recruitment.models import RecruitmentRoom
from apps.recruitment.services.ranking_service import get_ranked_room_applicants


class Echo:
    """
    An in-memory pseudo-buffer that implements the write interface
    to return written values directly for Django StreamingHttpResponse.
    """
    def write(self, value):
        return value


# Standardized ATS Column Definitions (US-46-T1)
EXPORT_COLUMNS = [
    "Rank",
    "Candidate Name",
    "Email Address",
    "CV Match Score (%)",
    "Video Presentation Score (%)",
    "Final Weighted Score (%)",
    "Shortlisted",
    "Application Status",
    "Applied Date",
]


def sanitize_filename_part(text: str) -> str:
    """Sanitizes text for safe inclusion in download filenames."""
    if not text:
        return "Room"
    clean = re.sub(r'[^\w\-_.]', '_', text.strip())
    clean = re.sub(r'_+', '_', clean)
    return clean[:50]


def get_export_filename(room: RecruitmentRoom, extension: str) -> str:
    """Generates a clean, descriptive attachment filename."""
    clean_title = sanitize_filename_part(room.title)
    ext = extension.lstrip('.')
    return f"CareerFlow_Room_{room.id}_{clean_title}_Applicants.{ext}"


def fetch_export_dataset(room: RecruitmentRoom, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Fetches room applicants using the ranking service with all specified query filters.
    Preserves: min_score, max_score, search query, status, ordering, and shortlisted_only.
    """
    filters = filters or {}
    
    min_score = filters.get('min_score')
    max_score = filters.get('max_score')
    search = filters.get('search')
    status_filter = filters.get('status')
    ordering = filters.get('ordering', '-final_score')
    include_unranked = filters.get('include_unranked', True)
    shortlisted_only = filters.get('shortlisted_only', False)

    return get_ranked_room_applicants(
        room_or_id=room,
        min_score=min_score,
        max_score=max_score,
        search=search,
        status_filter=status_filter,
        ordering=ordering,
        include_unranked=include_unranked,
        shortlisted_only=shortlisted_only,
    )


def extract_row_values(item: Dict[str, Any], is_ranked: bool) -> List[Any]:
    """
    Transforms a candidate data dictionary into a standardized ATS row.
    Handles None/pending values, formatting, and date serialization cleanly.
    """
    rank_str = str(item.get("rank", "")) if is_ranked else "Pending"
    cand_name = item.get("candidate_name") or "Unnamed Candidate"
    cand_email = item.get("candidate_email") or ""

    # Score formatting
    cv_score = item.get("cv_score")
    cv_str = f"{cv_score:.1f}%" if cv_score is not None else "Pending"

    video_score = item.get("video_score")
    video_str = f"{video_score:.1f}%" if video_score is not None else "Pending"

    final_score = item.get("final_score")
    final_str = f"{final_score:.1f}%" if final_score is not None else "Pending"

    # Shortlisted indicator
    is_shortlisted = item.get("is_shortlisted", False)
    shortlist_str = "Yes" if is_shortlisted else "No"

    # Status & Date
    status_str = str(item.get("status", "SUBMITTED")).upper()

    applied_at = item.get("applied_at")
    if isinstance(applied_at, datetime):
        applied_str = applied_at.strftime("%Y-%m-%d %H:%M:%S UTC")
    elif applied_at:
        applied_str = str(applied_at)
    else:
        applied_str = "—"

    return [
        rank_str,
        cand_name,
        cand_email,
        cv_str,
        video_str,
        final_str,
        shortlist_str,
        status_str,
        applied_str,
    ]


def stream_applicants_csv(room: RecruitmentRoom, filters: Optional[Dict[str, Any]] = None) -> Generator[str, None, None]:
    """
    US-46-T2: Streaming generator yielding CSV content line-by-line.
    Prepends UTF-8 BOM (\ufeff) for seamless Excel UTF-8 compatibility.
    Uses csv.writer to guarantee compliant quoting and escaping for commas and quotes.
    Memory complexity: O(1) chunks, preventing timeouts on large candidate batches.
    """
    data = fetch_export_dataset(room, filters)
    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)

    # 1. Yield UTF-8 Byte Order Mark (BOM) for Excel compatibility
    yield '\ufeff'

    # 2. Yield Table Header Row
    yield writer.writerow(EXPORT_COLUMNS)

    # 3. Yield Ranked Applicants (Ordered by current leaderboard sort)
    for applicant in data.get("results", []):
        row = extract_row_values(applicant, is_ranked=True)
        yield writer.writerow(row)

    # 4. Yield Unranked / Pending Applicants (if included)
    for applicant in data.get("unranked", []):
        row = extract_row_values(applicant, is_ranked=False)
        yield writer.writerow(row)


def generate_applicants_excel(room: RecruitmentRoom, filters: Optional[Dict[str, Any]] = None) -> io.BytesIO:
    """
    US-46-T3: Generates a professionally formatted Excel (.xlsx) workbook.
    Includes branded title header, room metadata, styled table columns,
    zebra-striped data rows, and auto-adjusted column dimensions.
    """
    data = fetch_export_dataset(room, filters)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ranked Applicants"

    # Enable grid lines for clear visibility
    ws.views.sheetView[0].showGridLines = True

    # Styling Palettes (CareerFlow Brand: Forest Green / Slate Theme)
    FONT_TITLE = Font(name="Calibri", size=14, bold=True, color="1E293B")
    FONT_META = Font(name="Calibri", size=10, italic=True, color="64748B")
    FONT_HEADER = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    FONT_DATA = Font(name="Calibri", size=10, color="0F172A")
    FONT_BOLD = Font(name="Calibri", size=10, bold=True, color="0F172A")

    FILL_HEADER = PatternFill(start_color="277254", end_color="277254", fill_type="solid")
    FILL_ZEBRA_EVEN = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    FILL_ZEBRA_ODD = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    FILL_SHORTLISTED = PatternFill(start_color="E2F0E9", end_color="E2F0E9", fill_type="solid")

    ALIGN_LEFT = Alignment(horizontal="left", vertical="center")
    ALIGN_CENTER = Alignment(horizontal="center", vertical="center")
    ALIGN_RIGHT = Alignment(horizontal="right", vertical="center")

    BORDER_THIN = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0')
    )

    # 1. Metadata Header Block
    now_str = timezone.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    ws.append([f"CareerFlow Applicant Leaderboard Dossier — {room.title}"])
    ws.cell(row=1, column=1).font = FONT_TITLE
    ws.row_dimensions[1].height = 24

    ws.append([f"Company: {room.company_name} | Department: {room.department or 'N/A'}"])
    ws.cell(row=2, column=1).font = FONT_META

    weights_info = f"Evaluation Formula: {room.cv_weight}% CV / {room.video_weight}% Video"
    total_apps = data.get("total_applicants", len(data.get("results", [])) + len(data.get("unranked", [])))
    ws.append([f"{weights_info} | Total Candidates in Export: {total_apps} | Generated: {now_str}"])
    ws.cell(row=3, column=1).font = FONT_META

    # Blank separator row
    ws.append([])

    # 2. Table Column Headers (Row 5)
    ws.append(EXPORT_COLUMNS)
    header_row_idx = 5
    ws.row_dimensions[header_row_idx].height = 26

    for col_idx, col_name in enumerate(EXPORT_COLUMNS, start=1):
        cell = ws.cell(row=header_row_idx, column=col_idx)
        cell.font = FONT_HEADER
        cell.fill = FILL_HEADER
        cell.border = BORDER_THIN
        cell.alignment = ALIGN_CENTER if col_name in ["Rank", "Shortlisted", "Application Status"] else ALIGN_LEFT

    # 3. Data Rows
    current_row = 6
    all_applicants = []
    for app in data.get("results", []):
        all_applicants.append((app, True))
    for app in data.get("unranked", []):
        all_applicants.append((app, False))

    for item, is_ranked in all_applicants:
        row_values = extract_row_values(item, is_ranked)
        ws.append(row_values)
        ws.row_dimensions[current_row].height = 20

        is_even = (current_row % 2 == 0)
        default_fill = FILL_ZEBRA_EVEN if is_even else FILL_ZEBRA_ODD
        is_shortlisted = item.get("is_shortlisted", False)

        for col_idx, val in enumerate(row_values, start=1):
            cell = ws.cell(row=current_row, column=col_idx)
            cell.font = FONT_DATA
            cell.border = BORDER_THIN
            cell.fill = FILL_SHORTLISTED if (col_idx == 7 and is_shortlisted) else default_fill

            # Formatting & alignment per column type
            col_name = EXPORT_COLUMNS[col_idx - 1]
            if col_name in ["Rank", "Shortlisted", "Application Status"]:
                cell.alignment = ALIGN_CENTER
                if col_name == "Rank" and is_ranked:
                    cell.font = FONT_BOLD
            elif "Score" in col_name:
                cell.alignment = ALIGN_RIGHT
                if "Final" in col_name and is_ranked:
                    cell.font = FONT_BOLD
            else:
                cell.alignment = ALIGN_LEFT

        current_row += 1

    # 4. Auto-fit column widths with safety padding
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            # Skip title row from width calculation to prevent excessive column widening
            if cell.row < header_row_idx:
                continue
            if cell.value:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    # 5. Save workbook to BytesIO stream
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output
