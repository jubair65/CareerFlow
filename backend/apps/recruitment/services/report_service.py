"""
US-33: Downloadable Applicant & Room Reports Service.
Generates publication-quality PDF reports for individual candidates and recruitment rooms
using ReportLab with crisp vector styling, executive score breakdowns, and graceful missing-data handling.
"""

import io
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from django.utils import timezone
from django.db.models import Avg, Max

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)
from reportlab.pdfgen import canvas

from apps.recruitment.models import CandidateApplication, RecruitmentRoom
from apps.recruitment.services.breakdown_service import get_applicant_score_breakdown
from apps.recruitment.services.scoring_service import resolve_room_weights

logger = logging.getLogger(__name__)

# Brand Color Palette
PRIMARY_COLOR = colors.HexColor('#277254')      # Forest Green
SECONDARY_COLOR = colors.HexColor('#253142')    # Deep Navy
TEXT_MAIN = colors.HexColor('#1f2937')          # Charcoal
TEXT_MUTED = colors.HexColor('#6b7280')         # Neutral Gray
BG_LIGHT = colors.HexColor('#fafaf7')           # Warm light gray
BG_ACCENT = colors.HexColor('#eef0e7')          # Soft green-gray
BORDER_COLOR = colors.HexColor('#d9dbd1')       # Subtle border
SUCCESS_BG = colors.HexColor('#e2f0e9')         # Pale green
SUCCESS_TEXT = colors.HexColor('#277254')       # Dark green
WARNING_BG = colors.HexColor('#fff1c9')         # Pale yellow
WARNING_TEXT = colors.HexColor('#8a6a16')       # Dark amber
DANGER_BG = colors.HexColor('#f7e5e1')          # Pale red
DANGER_TEXT = colors.HexColor('#a33d35')        # Dark red


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and stamp total page count ('Page X of Y')
    along with CareerFlow security and confidentiality running headers/footers.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        # Header rule & title
        self.setFont('Helvetica', 7)
        self.setFillColor(TEXT_MUTED)
        self.drawString(36, 762, "CAREERFLOW AI TALENT PLATFORM  |  CONFIDENTIAL EVALUATION DOSSIER")
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.5)
        self.line(36, 756, 612 - 36, 756)

        # Footer rule & page number
        self.line(36, 38, 612 - 36, 38)
        self.setFont('Helvetica', 8)
        self.drawString(36, 26, "Generated via CareerFlow Multi-Modal AI Assessment Engine  •  All Rights Reserved")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 36, 26, page_str)
        self.restoreState()


def get_custom_styles():
    """
    Constructs a consistent typography hierarchy for CareerFlow PDF reports.
    """
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='ReportHeaderTitle',
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=SECONDARY_COLOR,
    ))

    styles.add(ParagraphStyle(
        name='ReportHeaderSubtitle',
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=TEXT_MUTED,
    ))

    styles.add(ParagraphStyle(
        name='SectionHeading',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=PRIMARY_COLOR,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name='MetaLabel',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=TEXT_MUTED,
    ))

    styles.add(ParagraphStyle(
        name='MetaValue',
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=TEXT_MAIN,
    ))

    styles.add(ParagraphStyle(
        name='MetaValueBold',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=TEXT_MAIN,
    ))

    styles.add(ParagraphStyle(
        name='TableCell',
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=TEXT_MAIN,
    ))

    styles.add(ParagraphStyle(
        name='TableCellBold',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=TEXT_MAIN,
    ))

    styles.add(ParagraphStyle(
        name='TableCellHeader',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.white,
    ))

    styles.add(ParagraphStyle(
        name='ScoreValueLarge',
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=24,
        textColor=PRIMARY_COLOR,
        alignment=1,  # Center
    ))

    styles.add(ParagraphStyle(
        name='ScoreLabelSmall',
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=TEXT_MUTED,
        alignment=1,  # Center
    ))

    styles.add(ParagraphStyle(
        name='WarningBoxText',
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=WARNING_TEXT,
    ))

    return styles


# =============================================================================
# US-33-T3: Data Aggregator Methods
# =============================================================================

def generate_applicant_report_data(application_id: int) -> Dict[str, Any]:
    """
    US-33-T3: Aggregates candidate metadata, scores, breakdowns, speech transcripts,
    filler frequency, and eye contact percentages for an applicant report.
    """
    application = CandidateApplication.objects.select_related(
        'candidate',
        'room',
        'room__client_company',
        'cv',
        'video',
    ).get(id=application_id)

    breakdown = get_applicant_score_breakdown(application)

    room = application.room
    candidate = application.candidate
    candidate_name = getattr(candidate, 'full_name', '') or candidate.email.split('@')[0].title()

    cv_data = breakdown.get("cv_component", {})
    video_data = breakdown.get("video_component", {})

    # Extract parsed CV details if available
    skills_matched = cv_data.get("skills_matched", [])
    skills_missing = cv_data.get("skills_missing", [])
    education_entries = []
    experience_entries = []

    if application.cv and hasattr(application.cv, 'parsed_data'):
        pd = application.cv.parsed_data
        education_entries = getattr(pd, 'education', []) or []
        experience_entries = getattr(pd, 'experience', []) or []

    # Extract video presentation details if available
    wpm = 0
    filler_count = 0
    clarity_score = None
    eye_contact = None
    posture_score = None
    engagement_score = None

    if application.video:
        if hasattr(application.video, 'speech_analysis'):
            sa = application.video.speech_analysis
            wpm = round(getattr(sa, 'words_per_minute', 0), 1)
            filler_count = getattr(sa, 'filler_word_count', 0)
            clarity_score = getattr(sa, 'clarity_score', None)

        if hasattr(application.video, 'behavioral_analysis'):
            ba = application.video.behavioral_analysis
            eye_contact = getattr(ba, 'eye_contact_score', None)
            posture_score = getattr(ba, 'posture_score', None)
            engagement_score = getattr(ba, 'engagement_score', None)

    # Incompleteness detection (AC#5)
    incompleteness_reasons = []
    if not application.cv:
        incompleteness_reasons.append("CV document not submitted.")
    elif application.cv_score is None:
        incompleteness_reasons.append("CV semantic matching is currently pending or incomplete.")

    if not application.video:
        incompleteness_reasons.append("Video interview presentation not submitted.")
    elif application.video_score is None:
        incompleteness_reasons.append("Video speech and behavioral processing is currently in progress.")

    experience_display = room.get_experience_level_display() if hasattr(room, 'get_experience_level_display') else room.experience_level

    return {
        "application_id": application.id,
        "applied_at": getattr(application, 'applied_at', None),
        "candidate_id": candidate.id,
        "candidate_name": candidate_name,
        "candidate_email": candidate.email,
        "status": application.status,
        "room_id": room.id,
        "room_title": room.title,
        "company_name": room.company_name,
        "client_company_name": room.client_company.name if room.client_company else None,
        "department": room.department or "General Recruitment",
        "role_category": room.role_category or "Engineering",
        "experience_level": experience_display or "Mid Level",
        "cv_weight": room.cv_weight if room.cv_weight is not None else 50,
        "video_weight": room.video_weight if room.video_weight is not None else 50,
        "final_score": application.final_score,
        "cv_score": application.cv_score,
        "video_score": application.video_score,
        "is_partial_score": application.is_partial_score,
        "is_shortlisted": application.is_shortlisted,
        "shortlist_reason": application.shortlist_reason or "N/A",
        "shortlisted_at": application.shortlisted_at,
        "hr_decision": application.hr_decision,
        "hr_decision_display": application.get_hr_decision_display(),
        "hr_decision_notes": getattr(application, 'hr_decision_notes', '') or "No reviewer notes recorded.",
        "skills_matched": skills_matched,
        "skills_missing": skills_missing,
        "education_entries": education_entries,
        "experience_entries": experience_entries,
        "wpm": wpm,
        "filler_count": filler_count,
        "clarity_score": clarity_score,
        "eye_contact": eye_contact,
        "posture_score": posture_score,
        "engagement_score": engagement_score,
        "incompleteness_reasons": incompleteness_reasons,
        "formula_display": breakdown.get("formula_display", ""),
    }


def generate_room_summary_data(room_id: int) -> Dict[str, Any]:
    """
    US-33-T3: Aggregates room criteria, applicant roster, scores, and ranking distribution.
    """
    room = RecruitmentRoom.objects.select_related(
        'client_company',
        'created_by'
    ).get(id=room_id)

    cv_weight, video_weight = resolve_room_weights(room)

    applications = CandidateApplication.objects.filter(
        room=room
    ).select_related('candidate').order_by('-final_score', 'id')

    total_count = applications.count()
    shortlisted_count = applications.filter(is_shortlisted=True).count()
    completed_apps = applications.filter(status=CandidateApplication.Status.COMPLETED)

    avg_final = completed_apps.aggregate(Avg('final_score'))['final_score__avg']
    top_final = completed_apps.aggregate(Max('final_score'))['final_score__max']
    avg_cv = completed_apps.aggregate(Avg('cv_score'))['cv_score__avg']
    avg_video = completed_apps.aggregate(Avg('video_score'))['video_score__avg']

    roster = []
    for rank, app in enumerate(applications, start=1):
        cand_name = getattr(app.candidate, 'full_name', '') or app.candidate.email.split('@')[0].title()
        roster.append({
            "rank": rank,
            "application_id": app.id,
            "candidate_name": cand_name,
            "candidate_email": app.candidate.email,
            "cv_score": round(app.cv_score, 1) if app.cv_score is not None else None,
            "video_score": round(app.video_score, 1) if app.video_score is not None else None,
            "final_score": round(app.final_score, 1) if app.final_score is not None else None,
            "is_shortlisted": app.is_shortlisted,
            "status": app.status,
            "hr_decision": app.get_hr_decision_display(),
        })

    skills_req = getattr(room, 'skills_list', getattr(room, 'skills_required', []))

    return {
        "room_id": room.id,
        "room_title": room.title,
        "company_name": room.company_name,
        "client_company_name": room.client_company.name if room.client_company else None,
        "department": room.department or "General Recruitment",
        "status": room.get_status_display(),
        "cv_weight": cv_weight,
        "video_weight": video_weight,
        "skills_required": skills_req,
        "min_experience_years": 0,
        "total_applicants": total_count,
        "shortlisted_count": shortlisted_count,
        "avg_final_score": round(avg_final, 1) if avg_final is not None else None,
        "top_final_score": round(top_final, 1) if top_final is not None else None,
        "avg_cv_score": round(avg_cv, 1) if avg_cv is not None else None,
        "avg_video_score": round(avg_video, 1) if avg_video is not None else None,
        "roster": roster,
    }


# =============================================================================
# US-33-T2: PDF Generation Engines
# =============================================================================

def generate_candidate_report_pdf(application_or_id: Union[CandidateApplication, int], request=None) -> bytes:
    """
    US-33-T2: Renders a vector PDF candidate evaluation scorecard.
    """
    if isinstance(application_or_id, int):
        app_id = application_or_id
    else:
        app_id = application_or_id.id

    data = generate_applicant_report_data(app_id)
    styles = get_custom_styles()
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=44,
        bottomMargin=48,
    )

    story = []

    # 1. Header Banner & Branding
    story.append(Paragraph("CAREERFLOW CANDIDATE EVALUATION REPORT", styles['ReportHeaderTitle']))
    company_context = data['company_name']
    if data['client_company_name']:
        company_context += f" (Client: {data['client_company_name']})"

    timestamp_str = timezone.now().strftime("%B %d, %Y - %H:%M UTC")
    story.append(Paragraph(
        f"<b>Opening:</b> {data['room_title']}  •  <b>Organization:</b> {company_context}  •  <b>Generated:</b> {timestamp_str}",
        styles['ReportHeaderSubtitle']
    ))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY_COLOR, spaceBefore=0, spaceAfter=12))

    # 2. Incompleteness Warning Callout (AC#5)
    if data['incompleteness_reasons']:
        warning_text = "<b>EVALUATION INCOMPLETE / PENDING:</b><br/>" + "<br/>".join(
            f"• {reason}" for reason in data['incompleteness_reasons']
        )
        if data['is_partial_score']:
            warning_text += "<br/><i>Note: The displayed composite score is temporarily pro-rated based on available components.</i>"

        warn_table = Table(
            [[Paragraph(warning_text, styles['WarningBoxText'])]],
            colWidths=[540],
        )
        warn_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), WARNING_BG),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#f5c84b')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(warn_table)
        story.append(Spacer(1, 10))

    # 3. Candidate & Opening Metadata Matrix
    meta_table_data = [
        [
            Paragraph("CANDIDATE NAME", styles['MetaLabel']),
            Paragraph(data['candidate_name'], styles['MetaValueBold']),
            Paragraph("APPLICATION ID", styles['MetaLabel']),
            Paragraph(f"#{data['application_id']}", styles['MetaValueBold']),
        ],
        [
            Paragraph("EMAIL ADDRESS", styles['MetaLabel']),
            Paragraph(data['candidate_email'], styles['MetaValue']),
            Paragraph("DEPARTMENT", styles['MetaLabel']),
            Paragraph(data['department'], styles['MetaValue']),
        ],
        [
            Paragraph("TARGET ROLE", styles['MetaLabel']),
            Paragraph(data['role_category'], styles['MetaValue']),
            Paragraph("STATUS", styles['MetaLabel']),
            Paragraph(data['status'], styles['MetaValueBold']),
        ],
    ]
    meta_table = Table(meta_table_data, colWidths=[100, 170, 100, 170])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))

    # 4. Multi-Modal Scorecards (Overall, CV, Video, Decision)
    final_score_str = f"{round(data['final_score'], 1)}%" if data['final_score'] is not None else "Pending"
    cv_score_str = f"{round(data['cv_score'], 1)}%" if data['cv_score'] is not None else "N/A"
    video_score_str = f"{round(data['video_score'], 1)}%" if data['video_score'] is not None else "N/A"
    shortlist_badge = "SHORTLISTED" if data['is_shortlisted'] else "NOT SHORTLISTED"

    scores_table_data = [
        [
            Paragraph(final_score_str, styles['ScoreValueLarge']),
            Paragraph(cv_score_str, styles['ScoreValueLarge']),
            Paragraph(video_score_str, styles['ScoreValueLarge']),
            Paragraph(data['hr_decision_display'], styles['ScoreValueLarge']),
        ],
        [
            Paragraph(f"FINAL WEIGHTED SCORE<br/><font size=6.5>CV: {data['cv_weight']}%  |  Video: {data['video_weight']}%</font>", styles['ScoreLabelSmall']),
            Paragraph(f"CV MATCH SCORE<br/><font size=6.5>Target Weight: {data['cv_weight']}%</font>", styles['ScoreLabelSmall']),
            Paragraph(f"VIDEO PRESENTATION<br/><font size=6.5>Target Weight: {data['video_weight']}%</font>", styles['ScoreLabelSmall']),
            Paragraph(f"HR REVIEW DECISION<br/><font size=6.5>{shortlist_badge}</font>", styles['ScoreLabelSmall']),
        ],
    ]
    scores_table = Table(scores_table_data, colWidths=[135, 135, 135, 135])
    scores_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (0, -1), SUCCESS_BG),
    ]))
    story.append(scores_table)
    story.append(Spacer(1, 14))

    # 5. CV Intelligence & Skill Match Breakdown
    story.append(Paragraph("CV INTELLIGENCE & SKILL MATCHING", styles['SectionHeading']))
    matched_skills_str = ", ".join(data['skills_matched']) if data['skills_matched'] else "None recorded"
    missing_skills_str = ", ".join(data['skills_missing']) if data['skills_missing'] else "None identified"

    cv_breakdown_data = [
        [
            Paragraph("MATCHED SKILLS", styles['MetaLabel']),
            Paragraph(f"<font color='#277254'><b>{matched_skills_str}</b></font>", styles['TableCell']),
        ],
        [
            Paragraph("MISSING / GAP SKILLS", styles['MetaLabel']),
            Paragraph(f"<font color='#a33d35'>{missing_skills_str}</font>", styles['TableCell']),
        ],
    ]
    if data['education_entries']:
        edu_items = [f"• {e.get('degree', 'Degree')} ({e.get('institution', 'Institution')})" for e in data['education_entries'][:3]]
        cv_breakdown_data.append([
            Paragraph("EDUCATION", styles['MetaLabel']),
            Paragraph("<br/>".join(edu_items), styles['TableCell']),
        ])
    if data['experience_entries']:
        exp_items = [f"• {e.get('title', 'Role')} at {e.get('company', 'Company')} ({e.get('duration_years', 1)} yrs)" for e in data['experience_entries'][:3]]
        cv_breakdown_data.append([
            Paragraph("EXPERIENCE", styles['MetaLabel']),
            Paragraph("<br/>".join(exp_items), styles['TableCell']),
        ])

    cv_table = Table(cv_breakdown_data, colWidths=[130, 410])
    cv_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(cv_table)
    story.append(Spacer(1, 14))

    # 6. Video Presentation & Behavioral Intelligence
    story.append(Paragraph("VIDEO INTERVIEW & BEHAVIORAL ANALYTICS", styles['SectionHeading']))
    eye_str = f"{data['eye_contact']}%" if data['eye_contact'] is not None else "Pending"
    posture_str = f"{data['posture_score']}%" if data['posture_score'] is not None else "Pending"
    engagement_str = f"{data['engagement_score']}%" if data['engagement_score'] is not None else "Pending"
    clarity_str = f"{data['clarity_score']}%" if data['clarity_score'] is not None else "Pending"

    video_metrics_data = [
        [
            Paragraph("SPEAKING PACE", styles['MetaLabel']),
            Paragraph(f"{data['wpm']} WPM (Target: 130-160 WPM)", styles['TableCell']),
            Paragraph("CAMERA EYE CONTACT", styles['MetaLabel']),
            Paragraph(eye_str, styles['TableCellBold']),
        ],
        [
            Paragraph("FILLER WORDS", styles['MetaLabel']),
            Paragraph(f"{data['filler_count']} filler occurrences", styles['TableCell']),
            Paragraph("POSTURE ALIGNMENT", styles['MetaLabel']),
            Paragraph(posture_str, styles['TableCellBold']),
        ],
        [
            Paragraph("SPEECH CLARITY", styles['MetaLabel']),
            Paragraph(clarity_str, styles['TableCellBold']),
            Paragraph("FACIAL ENGAGEMENT", styles['MetaLabel']),
            Paragraph(engagement_str, styles['TableCellBold']),
        ],
    ]
    video_table = Table(video_metrics_data, colWidths=[110, 160, 110, 160])
    video_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(video_table)
    story.append(Spacer(1, 14))

    # 7. HR Decision & Audit Box
    story.append(Paragraph("HR HUMAN REVIEW & AUDIT TRAIL", styles['SectionHeading']))
    shortlist_date_str = data['shortlisted_at'].strftime("%B %d, %Y") if data['shortlisted_at'] else "N/A"
    hr_audit_data = [
        [
            Paragraph("SHORTLIST REASON", styles['MetaLabel']),
            Paragraph(data['shortlist_reason'], styles['TableCell']),
            Paragraph("SHORTLISTED DATE", styles['MetaLabel']),
            Paragraph(shortlist_date_str, styles['TableCell']),
        ],
        [
            Paragraph("DECISION NOTES", styles['MetaLabel']),
            Paragraph(data['hr_decision_notes'], styles['TableCell']),
            Paragraph("DECISION STATUS", styles['MetaLabel']),
            Paragraph(data['hr_decision_display'], styles['TableCellBold']),
        ],
    ]
    hr_table = Table(hr_audit_data, colWidths=[110, 160, 110, 160])
    hr_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(hr_table)

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()


def generate_room_summary_pdf(room_or_id: Union[RecruitmentRoom, int], request=None) -> bytes:
    """
    US-33-T2: Renders a vector PDF room summary report with candidate ranking roster.
    """
    if isinstance(room_or_id, int):
        room_id = room_or_id
    else:
        room_id = room_or_id.id

    data = generate_room_summary_data(room_id)
    styles = get_custom_styles()
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=44,
        bottomMargin=48,
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("RECRUITMENT ROOM SUMMARY REPORT", styles['ReportHeaderTitle']))
    company_context = data['company_name']
    if data['client_company_name']:
        company_context += f" (Client: {data['client_company_name']})"

    timestamp_str = timezone.now().strftime("%B %d, %Y - %H:%M UTC")
    story.append(Paragraph(
        f"<b>Opening:</b> {data['room_title']}  •  <b>Organization:</b> {company_context}  •  <b>Generated:</b> {timestamp_str}",
        styles['ReportHeaderSubtitle']
    ))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY_COLOR, spaceBefore=0, spaceAfter=12))

    # 2. Key Metrics Cards Table
    avg_score_str = f"{data['avg_final_score']}%" if data['avg_final_score'] is not None else "N/A"
    top_score_str = f"{data['top_final_score']}%" if data['top_final_score'] is not None else "N/A"

    metrics_table_data = [
        [
            Paragraph(str(data['total_applicants']), styles['ScoreValueLarge']),
            Paragraph(str(data['shortlisted_count']), styles['ScoreValueLarge']),
            Paragraph(avg_score_str, styles['ScoreValueLarge']),
            Paragraph(top_score_str, styles['ScoreValueLarge']),
        ],
        [
            Paragraph("TOTAL APPLICANTS<br/><font size=6.5>Registered submissions</font>", styles['ScoreLabelSmall']),
            Paragraph("SHORTLISTED<br/><font size=6.5>Met qualifying criteria</font>", styles['ScoreLabelSmall']),
            Paragraph("AVERAGE SCORE<br/><font size=6.5>Completed evaluations</font>", styles['ScoreLabelSmall']),
            Paragraph("TOP SCORE<br/><font size=6.5>Peak candidate result</font>", styles['ScoreLabelSmall']),
        ],
    ]
    metrics_table = Table(metrics_table_data, colWidths=[135, 135, 135, 135])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (1, 0), (1, -1), SUCCESS_BG),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 14))

    # 3. Room Configuration & Evaluation Weights
    skills_req_str = ", ".join(data['skills_required']) if data['skills_required'] else "General requirements"
    config_data = [
        [
            Paragraph("EVALUATION WEIGHTING", styles['MetaLabel']),
            Paragraph(f"CV Match: <b>{data['cv_weight']}%</b>  |  Video Presentation: <b>{data['video_weight']}%</b>", styles['TableCell']),
            Paragraph("ROOM STATUS", styles['MetaLabel']),
            Paragraph(data['status'], styles['TableCellBold']),
        ],
        [
            Paragraph("REQUIRED SKILLS", styles['MetaLabel']),
            Paragraph(skills_req_str, styles['TableCell']),
            Paragraph("MIN EXPERIENCE", styles['MetaLabel']),
            Paragraph(f"{data['min_experience_years']} year(s)", styles['TableCell']),
        ],
    ]
    config_table = Table(config_data, colWidths=[120, 200, 90, 130])
    config_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(config_table)
    story.append(Spacer(1, 14))

    # 4. Ranked Candidate Roster Table
    story.append(Paragraph(f"APPLICANT RANKING ROSTER ({len(data['roster'])})", styles['SectionHeading']))

    if not data['roster']:
        empty_table = Table(
            [[Paragraph("No applicant submissions have been recorded for this recruitment opening.", styles['TableCell'])]],
            colWidths=[540],
        )
        empty_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
            ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
            ('PADDING', (0, 0), (-1, -1), 16),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(empty_table)
    else:
        roster_table_data = [
            [
                Paragraph("RANK", styles['TableCellHeader']),
                Paragraph("CANDIDATE", styles['TableCellHeader']),
                Paragraph("EMAIL", styles['TableCellHeader']),
                Paragraph("CV SCORE", styles['TableCellHeader']),
                Paragraph("VIDEO", styles['TableCellHeader']),
                Paragraph("FINAL", styles['TableCellHeader']),
                Paragraph("SHORTLIST", styles['TableCellHeader']),
                Paragraph("HR DECISION", styles['TableCellHeader']),
            ]
        ]

        for item in data['roster']:
            rank_str = f"#{item['rank']}"
            cv_str = f"{item['cv_score']}%" if item['cv_score'] is not None else "-"
            vid_str = f"{item['video_score']}%" if item['video_score'] is not None else "-"
            final_str = f"<b>{item['final_score']}%</b>" if item['final_score'] is not None else "-"
            short_str = "YES" if item['is_shortlisted'] else "NO"

            roster_table_data.append([
                Paragraph(rank_str, styles['TableCellBold']),
                Paragraph(item['candidate_name'], styles['TableCellBold']),
                Paragraph(item['candidate_email'], styles['TableCell']),
                Paragraph(cv_str, styles['TableCell']),
                Paragraph(vid_str, styles['TableCell']),
                Paragraph(final_str, styles['TableCell']),
                Paragraph(short_str, styles['TableCellBold']),
                Paragraph(item['hr_decision'], styles['TableCell']),
            ])

        roster_table = Table(
            roster_table_data,
            colWidths=[35, 110, 135, 50, 45, 50, 50, 65],
            repeatRows=1,
        )

        roster_style = [
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            ('PADDING', (0, 0), (-1, -1), 4.5),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]

        # Alternating row colors
        for i in range(1, len(roster_table_data)):
            if i % 2 == 0:
                roster_style.append(('BACKGROUND', (0, i), (-1, i), BG_LIGHT))

        roster_table.setStyle(TableStyle(roster_style))
        story.append(roster_table)

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()
