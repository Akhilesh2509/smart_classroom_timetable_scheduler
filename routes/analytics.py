from flask import Blueprint, session, redirect, url_for, jsonify
from models import db, TimetableEntry, Teacher, Classroom
from sqlalchemy import func
import time

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')


# Page Route
@analytics_bp.route('/')
def analytics_page():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    return "<h1>Analytics Page</h1>"


# Conflict Detection Function
def detect_conflicts():
    # Teacher conflicts
    teacher_conflicts = db.session.query(
        TimetableEntry.day,
        TimetableEntry.period,
        TimetableEntry.teacher_id,
        func.count(TimetableEntry.id)
    ).group_by(
        TimetableEntry.day,
        TimetableEntry.period,
        TimetableEntry.teacher_id
    ).having(func.count(TimetableEntry.id) > 1).count()

    # Classroom conflicts
    classroom_conflicts = db.session.query(
        TimetableEntry.day,
        TimetableEntry.period,
        TimetableEntry.classroom_id,
        func.count(TimetableEntry.id)
    ).group_by(
        TimetableEntry.day,
        TimetableEntry.period,
        TimetableEntry.classroom_id
    ).having(func.count(TimetableEntry.id) > 1).count()

    # Section conflicts
    section_conflicts = db.session.query(
        TimetableEntry.day,
        TimetableEntry.period,
        TimetableEntry.section_id,
        func.count(TimetableEntry.id)
    ).group_by(
        TimetableEntry.day,
        TimetableEntry.period,
        TimetableEntry.section_id
    ).having(func.count(TimetableEntry.id) > 1).count()

    return teacher_conflicts + classroom_conflicts + section_conflicts


# System Performance API
@analytics_bp.route('/system-performance')
def system_performance():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    start_time = time.time()

    # Basic metrics
    total_classes = TimetableEntry.query.count()
    total_teachers = Teacher.query.count()
    total_classrooms = Classroom.query.count()

    avg_load = total_classes / total_teachers if total_teachers else 0

    # Conflict detection
    conflicts = detect_conflicts()

    # Response time
    response_time = round(time.time() - start_time, 4)

    return jsonify({
        "total_classes": total_classes,
        "total_teachers": total_teachers,
        "total_classrooms": total_classrooms,
        "avg_teacher_load": round(avg_load, 2),
        "conflicts": conflicts,
        "response_time": response_time
    })