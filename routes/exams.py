import json
import os
import requests
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, session, redirect, url_for, render_template, g, send_file, make_response
from sqlalchemy.orm import joinedload
from sqlalchemy import exc

from extensions import db
from models import Exam, ExamSeating, Student, Classroom, Subject, Course, Teacher, StudentSection
from utils import log_activity, validate_json_request

exams_bp = Blueprint('exams', __name__, url_prefix='/exams')

@exams_bp.route('/')
def manage_exams():
    """Render the exam management page."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    if session.get('role') != 'admin':
        return redirect(url_for('main.dashboard'))
    return render_template('exams.html')

@exams_bp.route('/api/exams', methods=['GET', 'POST'])
@exams_bp.route('/api/exams/<int:exam_id>', methods=['PUT', 'DELETE'])
def handle_exams(exam_id=None):
    """Handle exam CRUD operations."""
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized"}), 401
    
    try:
        if request.method == 'GET':
            exams = Exam.query.options(
                joinedload(Exam.subject),
                joinedload(Exam.course)
            ).all()
            
            exams_data = []
            for exam in exams:
                exam_data = {
                    'id': exam.id,
                    'name': exam.name,
                    'date': exam.date.isoformat(),
                    'duration': exam.duration,
                    'type': exam.type,
                    'subject_name': exam.subject.name if exam.subject else exam.course.name if exam.course else 'N/A',
                    'subject_code': exam.subject.code if exam.subject else exam.course.code if exam.course else 'N/A'
                }
                exams_data.append(exam_data)
            
            return jsonify({"exams": exams_data})
        
        if request.method in ['POST', 'PUT']:
            data, error_response, status_code = validate_json_request()
            if error_response:
                return error_response, status_code
        
        if request.method == 'POST':
            # Create new exam
            exam_date = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
            
            new_exam = Exam(
                name=data['name'],
                date=exam_date,
                duration=data.get('duration', 180),  # Default 3 hours
                type=data.get('type', 'final'),
                subject_id=data.get('subject_id'),
                course_id=data.get('course_id')
            )
            
            db.session.add(new_exam)
            db.session.commit()
            
            log_activity('info', f"Exam '{data['name']}' created.")
            return jsonify({"message": "Exam created successfully!"})
        
        elif request.method == 'PUT':
            # Update existing exam
            exam = Exam.query.get_or_404(exam_id)
            exam.name = data['name']
            exam.date = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
            exam.duration = data.get('duration', exam.duration)
            exam.type = data.get('type', exam.type)
            exam.subject_id = data.get('subject_id')
            exam.course_id = data.get('course_id')
            
            db.session.commit()
            
            log_activity('info', f"Exam '{exam.name}' updated.")
            return jsonify({"message": "Exam updated successfully!"})
        
        elif request.method == 'DELETE':
            # Delete exam
            exam = Exam.query.get_or_404(exam_id)
            exam_name = exam.name
            
            # Delete associated seating plans
            ExamSeating.query.filter_by(exam_id=exam_id).delete()
            
            db.session.delete(exam)
            db.session.commit()
            
            log_activity('warning', f"Exam '{exam_name}' deleted.")
            return jsonify({"message": "Exam deleted successfully!"})
            
    except exc.IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Database integrity error occurred."}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"An unexpected error occurred: {e}"}), 500

@exams_bp.route('/api/generate_schedule', methods=['POST'])
def generate_exam_schedule():
    """Generate exam schedule and seating plan using Gemini AI."""
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized"}), 401
    
    try:
        data, error_response, status_code = validate_json_request()
        if error_response:
            return error_response, status_code
        
        exam_ids = data.get('exam_ids', [])
        if not exam_ids:
            return jsonify({"message": "No exams selected for scheduling."}), 400
        
        # Get exam data
        exams = Exam.query.filter(Exam.id.in_(exam_ids)).options(
            joinedload(Exam.subject),
            joinedload(Exam.course)
        ).all()
        
        if not exams:
            return jsonify({"message": "No valid exams found."}), 400
        
        # Get students data
        students = Student.query.options(
            joinedload(Student.user),
            joinedload(Student.section)
        ).all()
        
        # Get classrooms data
        classrooms = Classroom.query.all()
        
        if not os.getenv('GEMINI_API_KEY'):
            schedule_data = generate_local_exam_schedule(exams, students, classrooms)
            db.session.commit()
            log_activity('info', f"Local exam schedule generated for {len(exams)} exams.")
            return jsonify({
                "message": "Exam schedule generated successfully.",
                "schedule": schedule_data.get('exam_schedule', []),
                "changes": schedule_data.get('explanation_of_changes', [])
            })

        prompt = generate_exam_schedule_prompt(exams, students, classrooms)
        schedule_data = call_gemini_api(prompt)
        
        if schedule_data and 'exam_schedule' in schedule_data:
            # Save exam schedule and seating plans
            for schedule_item in schedule_data['exam_schedule']:
                # Update exam with schedule
                exam = next((e for e in exams if e.name == schedule_item['subject_id']), None)
                if exam:
                    exam.date = datetime.fromisoformat(schedule_item['date'])
                    exam.duration = schedule_item.get('duration', 180)
            
            # Save seating plans
            if 'seating_plan' in schedule_data:
                for seating_item in schedule_data['seating_plan']:
                    exam = next((e for e in exams if e.name == seating_item['exam_id'].split('-')[0]), None)
                    if exam:
                        # Clear existing seating for this exam
                        ExamSeating.query.filter_by(exam_id=exam.id).delete()
                        
                        # Add new seating plan
                        for row_idx, row in enumerate(seating_item['map']):
                            for col_idx, student_id in enumerate(row):
                                if student_id:
                                    classroom = next((c for c in classrooms if c.room_id == seating_item['room_id']), None)
                                    if classroom:
                                        seating = ExamSeating(
                                            exam_id=exam.id,
                                            student_id=student_id,
                                            classroom_id=classroom.id,
                                            seat_number=f"{row_idx + 1}-{col_idx + 1}"
                                        )
                                        db.session.add(seating)
            
            db.session.commit()
            
            log_activity('info', f"Exam schedule generated for {len(exams)} exams.")
            return jsonify({
                "message": f"Exam schedule generated successfully!",
                "schedule": schedule_data.get('exam_schedule', []),
                "changes": schedule_data.get('explanation_of_changes', [])
            })
        else:
            raise ValueError("Invalid response from Gemini API")
            
    except Exception as e:
        db.session.rollback()
        log_activity('error', f'Exam schedule generation failed: {e}')
        return jsonify({"message": f"Failed to generate exam schedule: {str(e)}"}), 500

def generate_local_exam_schedule(exams, students, classrooms):
    """Generate a deterministic schedule and seating plan without an external AI key."""
    if not classrooms:
        raise ValueError("No classrooms available for exam scheduling.")

    start_date = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
    schedule = []
    seating_plan = []

    for exam_index, exam in enumerate(sorted(exams, key=lambda item: item.id)):
        exam.date = start_date + timedelta(days=exam_index)
        exam.duration = exam.duration or 180

        relevant_students = students_for_exam(exam, students)
        if not relevant_students:
            relevant_students = students

        ExamSeating.query.filter_by(exam_id=exam.id).delete()

        remaining_students = list(relevant_students)
        assigned_rooms = []

        for classroom in sorted(classrooms, key=lambda room: room.room_id):
            if not remaining_students:
                break

            assigned_rooms.append(classroom.room_id)
            room_map = []
            seats_in_room = min(classroom.capacity, len(remaining_students))
            columns = 5
            rows = max(1, (seats_in_room + columns - 1) // columns)

            for row_idx in range(rows):
                row = []
                for col_idx in range(columns):
                    if remaining_students and len(row) + (row_idx * columns) < seats_in_room:
                        student = remaining_students.pop(0)
                        seat_number = f"{row_idx + 1}-{col_idx + 1}"
                        db.session.add(ExamSeating(
                            exam_id=exam.id,
                            student_id=student.id,
                            classroom_id=classroom.id,
                            seat_number=seat_number
                        ))
                        row.append(student.id)
                    else:
                        row.append(None)
                room_map.append(row)

            seating_plan.append({
                "exam_id": exam.id,
                "room_id": classroom.room_id,
                "map": room_map
            })

        schedule.append({
            "exam_id": exam.id,
            "exam_name": exam.name,
            "date": exam.date.isoformat(),
            "duration": exam.duration,
            "rooms_assigned": assigned_rooms
        })

    return {
        "exam_schedule": schedule,
        "seating_plan": seating_plan,
        "explanation_of_changes": [
            "Generated locally because GEMINI_API_KEY is not configured.",
            "Scheduled one exam per day at 10:00 AM and assigned students by classroom capacity."
        ]
    }

def students_for_exam(exam, students):
    """Best-effort class-wise student selection from the current schema."""
    matching_students = []
    course_department_id = exam.course.department_id if exam.course else None

    for student in students:
        section = student.section
        if not section:
            continue

        if course_department_id and section.department_id != course_department_id:
            continue

        if section.name.lower() in exam.name.lower():
            matching_students.append(student)

    if matching_students:
        return matching_students

    if course_department_id:
        return [
            student for student in students
            if student.section and student.section.department_id == course_department_id
        ]

    return students

def generate_exam_schedule_prompt(exams, students, classrooms):
    """Generate prompt for Gemini API to create exam schedule."""
    
    exams_data = []
    for exam in exams:
        exam_info = {
            'id': exam.id,
            'name': exam.name,
            'duration': exam.duration,
            'type': exam.type,
            'subject': exam.subject.name if exam.subject else exam.course.name if exam.course else 'N/A',
            'subject_code': exam.subject.code if exam.subject else exam.course.code if exam.course else 'N/A'
        }
        exams_data.append(exam_info)
    
    students_data = []
    for student in students:
        student_info = {
            'id': student.id,
            'name': student.full_name,
            'section': student.section.name if student.section else 'N/A',
            'friends': []  # Could be populated from a friends table
        }
        students_data.append(student_info)
    
    classrooms_data = []
    for classroom in classrooms:
        classroom_info = {
            'id': classroom.id,
            'room_id': classroom.room_id,
            'capacity': classroom.capacity,
            'features': classroom.features or []
        }
        classrooms_data.append(classroom_info)
    
    prompt = f"""
You are an expert exam logistics coordinator for an Indian educational institution. Generate an optimal exam schedule and seating plan based on the following data:

EXAMS TO SCHEDULE ({len(exams_data)}):
{json.dumps(exams_data, indent=2)}

STUDENTS ({len(students_data)}):
{json.dumps(students_data, indent=2)}

AVAILABLE CLASSROOMS ({len(classrooms_data)}):
{json.dumps(classrooms_data, indent=2)}

REQUIREMENTS:
1. No student can have two exams at the same time
2. Spread exams out, aiming for maximum one exam per day per student
3. Classroom capacity cannot be exceeded
4. In seating plans, ensure no two students listed as 'friends' are seated adjacent (front, back, left, right)
5. Consider exam duration and type (final, midterm, quiz)
6. Optimize for minimal conflicts and maximum efficiency

OUTPUT FORMAT (JSON):
{{
    "exam_schedule": [
        {{
            "date": "2024-03-15",
            "time": "09:00-12:00",
            "subject_id": "Math-10",
            "duration": 180,
            "rooms_assigned": ["R201", "R202"]
        }}
    ],
    "seating_plan": [
        {{
            "exam_id": "Math-10-2024-03-15",
            "room_id": "R201",
            "map": [
                ["S001", "S015", "S023"],
                ["S002", null, "S045"],
                [null, "S067", "S089"]
            ]
        }}
    ],
    "explanation_of_changes": [
        "Scheduled Math exam for Class 10 on March 15th to avoid conflicts",
        "Assigned classrooms R201 and R202 based on student count"
    ]
}}

Return ONLY the JSON object, no additional text.
"""
    
    return prompt

def call_gemini_api(prompt, max_retries=3):
    """Call Gemini API to generate exam schedule with retry logic for rate limits."""
    import time
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {
        'Content-Type': 'application/json',
    }
    
    data = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            
            # Handle rate limit specifically
            if response.status_code == 429:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 5  # Exponential backoff: 5s, 10s, 20s
                    log_activity('warning', f'Rate limit hit, retrying in {wait_time} seconds (attempt {attempt + 1}/{max_retries})')
                    time.sleep(wait_time)
                    continue
                else:
                    raise ValueError("Rate limit exceeded. Please wait a few minutes before trying again.")
            
            response.raise_for_status()
            result = response.json()
            
            if 'candidates' in result and len(result['candidates']) > 0:
                content = result['candidates'][0]['content']['parts'][0]['text']
                # Clean up the response to extract JSON
                content = content.strip()
                if content.startswith('```json'):
                    content = content[7:]
                if content.endswith('```'):
                    content = content[:-3]
                
                return json.loads(content)
            else:
                raise ValueError("No valid response from Gemini API")
                
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 2  # Shorter wait for network errors
                log_activity('warning', f'Network error, retrying in {wait_time} seconds: {e}')
                time.sleep(wait_time)
                continue
            else:
                log_activity('error', f'Gemini API call failed after {max_retries} attempts: {e}')
                raise ValueError(f"Failed to generate exam schedule: {e}")
        except Exception as e:
            log_activity('error', f'Gemini API call failed: {e}')
            raise ValueError(f"Failed to generate exam schedule: {e}")

@exams_bp.route('/api/seating/<int:exam_id>')
def get_seating_plan(exam_id):
    """Get seating plan for a specific exam."""
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized"}), 401
    
    try:
        exam = Exam.query.get_or_404(exam_id)
        seating_plans = ExamSeating.query.filter_by(exam_id=exam_id).options(
            joinedload(ExamSeating.student),
            joinedload(ExamSeating.classroom)
        ).all()
        
        # Group by classroom
        classrooms = {}
        for seating in seating_plans:
            room_id = seating.classroom.room_id
            if room_id not in classrooms:
                classrooms[room_id] = {
                    'room_id': room_id,
                    'capacity': seating.classroom.capacity,
                    'seats': {}
                }
            
            row, col = seating.seat_number.split('-')
            classrooms[room_id]['seats'][f"{row}-{col}"] = {
                'student_id': seating.student_id,
                'student_name': seating.student.full_name,
                'seat_number': seating.seat_number
            }
        
        return jsonify({
            "exam_name": exam.name,
            "exam_date": exam.date.isoformat(),
            "classrooms": classrooms
        })
        
    except Exception as e:
        return jsonify({"message": f"Error fetching seating plan: {str(e)}"}), 500

@exams_bp.route('/api/export/<int:exam_id>')
def export_exam_schedule(exam_id):
    """Export exam schedule and seating plan as PDF."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    # This would integrate with a PDF generation library like ReportLab
    # For now, return a placeholder response
    return jsonify({"message": "Export functionality will be implemented with PDF generation library"})

@exams_bp.route('/api/export')
def export_all_exams():
    """Export all exams and seating summaries as a PDF."""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    try:
        exams = Exam.query.options(
            joinedload(Exam.subject),
            joinedload(Exam.course),
            joinedload(Exam.seating_plans).joinedload(ExamSeating.student),
            joinedload(Exam.seating_plans).joinedload(ExamSeating.classroom)
        ).order_by(Exam.date, Exam.id).all()

        pdf_bytes = build_exam_pdf(exams)
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=exam-schedule.pdf'
        return response
    except Exception as e:
        return jsonify({"message": f"Failed to export exams: {e}"}), 500

def build_exam_pdf(exams):
    """Build a dependency-free PDF for exam schedules."""

    def pdf_text(value):
        value = str(value or "")
        value = value.encode('latin-1', 'replace').decode('latin-1')
        return value.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')

    def text_cmd(x, y, text, size=9):
        return f"BT /F1 {size} Tf {x:.1f} {y:.1f} Td ({pdf_text(text)}) Tj ET\n"

    def line_cmd(x1, y1, x2, y2):
        return f"{x1:.1f} {y1:.1f} m {x2:.1f} {y2:.1f} l S\n"

    def rect_cmd(x, y, w, h):
        return f"{x:.1f} {y:.1f} {w:.1f} {h:.1f} re S\n"

    def fill_rect_cmd(x, y, w, h, color):
        r, g, b = color
        return f"{r:.3f} {g:.3f} {b:.3f} rg\n{x:.1f} {y:.1f} {w:.1f} {h:.1f} re f\n0 0 0 rg\n"

    def clip(value, max_chars):
        value = str(value or "")
        return value if len(value) <= max_chars else value[:max_chars - 3] + "..."

    def exam_subject(exam):
        return exam.subject.name if exam.subject else exam.course.name if exam.course else "N/A"

    page_width = 842
    page_height = 595
    margin = 34
    pages = []

    if not exams:
        exams = []

    def add_exam_page(exam, seating_rows, page_number, total_pages):
        commands = []
        commands.append("0.965 0.975 1 rg\n")
        commands.append(f"0 0 {page_width} {page_height} re f\n")
        commands.append("0 0 0 RG\n0 0 0 rg\n")
        commands.append(fill_rect_cmd(margin, 520, page_width - (margin * 2), 44, (0.231, 0.322, 0.627)))
        commands.append("1 1 1 rg\n")
        commands.append(text_cmd(margin + 18, 547, "Exam Schedule", 20))
        commands.append(text_cmd(page_width - 150, 542, f"Page {page_number}/{total_pages}", 9))
        commands.append("0 0 0 rg\n")

        if not exam:
            commands.append(text_cmd(margin + 18, 480, "No exams available.", 14))
            return "".join(commands)

        date_text = exam.date.strftime("%d %b %Y, %I:%M %p") if exam.date else "Not scheduled"
        commands.append(text_cmd(margin + 18, 492, clip(exam.name, 72), 15))
        commands.append(text_cmd(margin + 18, 468, f"Subject/Course: {clip(exam_subject(exam), 55)}", 10))
        commands.append(text_cmd(margin + 18, 450, f"Date & Time: {date_text}", 10))
        commands.append(text_cmd(margin + 18, 432, f"Duration: {exam.duration} minutes    Type: {exam.type.title()}", 10))

        table_x = margin + 18
        table_y = 390
        table_w = page_width - (margin * 2) - 36
        row_h = 22
        commands.append(fill_rect_cmd(table_x, table_y, table_w, row_h, (0.890, 0.910, 0.965)))
        commands.append("0.68 0.72 0.82 RG\n")
        commands.append(rect_cmd(table_x, table_y - (row_h * max(len(seating_rows), 1)), table_w, row_h * (max(len(seating_rows), 1) + 1)))
        commands.append(text_cmd(table_x + 12, table_y + 9, "Room", 10))
        commands.append(text_cmd(table_x + 90, table_y + 9, "Seat", 10))
        commands.append(text_cmd(table_x + 160, table_y + 9, "Student", 10))
        commands.append(text_cmd(table_x + 380, table_y + 9, "Class / Section", 10))
        commands.append(text_cmd(table_x + 560, table_y + 9, "Subject", 10))

        if seating_rows:
            for index, row in enumerate(seating_rows, start=1):
                y = table_y - (index * row_h)
                if index % 2 == 0:
                    commands.append(fill_rect_cmd(table_x, y, table_w, row_h, (0.985, 0.988, 1)))
                commands.append(line_cmd(table_x, y, table_x + table_w, y))
                commands.append(text_cmd(table_x + 12, y + 7, row["room"], 8))
                commands.append(text_cmd(table_x + 90, y + 7, row["seat"], 8))
                commands.append(text_cmd(table_x + 160, y + 7, clip(row["student"], 32), 8))
                commands.append(text_cmd(table_x + 380, y + 7, clip(row["section"], 25), 8))
                commands.append(text_cmd(table_x + 560, y + 7, clip(row["subject"], 25), 8))
        else:
            commands.append(text_cmd(table_x + 12, table_y - 16, "No seating plan generated yet. Click Generate Schedule first.", 9))

        return "".join(commands)

    if not exams:
        pages.append(add_exam_page(None, [], 1, 1))
    else:
        for exam in exams:
            rows = []
            for seating in sorted(exam.seating_plans, key=lambda item: (
                item.classroom.room_id if item.classroom else "",
                item.seat_number or ""
            )):
                student = seating.student
                section = student.section.name if student and student.section else "N/A"
                rows.append({
                    "room": seating.classroom.room_id if seating.classroom else "Unknown",
                    "seat": seating.seat_number or "-",
                    "student": student.full_name if student else f"Student {seating.student_id}",
                    "section": section,
                    "subject": exam_subject(exam)
                })

            if not rows:
                pages.append(add_exam_page(exam, [], 1, 1))
                continue

            rows_per_page = 15
            chunks = [rows[index:index + rows_per_page] for index in range(0, len(rows), rows_per_page)]
            for page_index, chunk in enumerate(chunks, start=1):
                pages.append(add_exam_page(exam, chunk, page_index, len(chunks)))

    objects = []
    objects.append("<< /Type /Catalog /Pages 2 0 R >>")
    page_objects = []
    content_start_obj = 3 + len(pages)

    for index in range(len(pages)):
        page_obj_num = 3 + index
        content_obj_num = content_start_obj + index
        page_objects.append(page_obj_num)
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_width} {page_height}] "
            f"/Resources << /Font << /F1 {content_start_obj + len(pages)} 0 R >> >> "
            f"/Contents {content_obj_num} 0 R >>"
        )

    kids = " ".join(f"{obj_num} 0 R" for obj_num in page_objects)
    objects.insert(1, f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>")

    for page in pages:
        stream = page.encode('latin-1', 'replace')
        objects.append(f"<< /Length {len(stream)} >>\nstream\n{page}endstream")

    objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n{obj}\nendobj\n".encode('latin-1', 'replace'))

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode('latin-1'))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode('latin-1'))
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode('latin-1')
    )
    return bytes(pdf)
