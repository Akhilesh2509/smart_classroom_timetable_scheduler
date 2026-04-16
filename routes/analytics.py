import json
from flask import Blueprint, session, redirect, url_for, jsonify
from models import db, TimetableEntry, Teacher, Classroom, AppConfig
from sqlalchemy import func
from sqlalchemy.orm import joinedload
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


def get_conflict_details():
    conflict_rows = []

    def build_conflict_rows(conflict_type, grouped_rows, field_name):
        for grouped in grouped_rows:
            entries = TimetableEntry.query.options(
                joinedload(TimetableEntry.teacher),
                joinedload(TimetableEntry.classroom),
                joinedload(TimetableEntry.section),
                joinedload(TimetableEntry.subject),
                joinedload(TimetableEntry.course)
            ).filter_by(
                day=grouped.day,
                period=grouped.period,
                **{field_name: getattr(grouped, field_name)}
            ).all()

            entity_label = "Unknown"
            if conflict_type == 'teacher':
                entity_label = entries[0].teacher.full_name if entries and entries[0].teacher else "Unknown Teacher"
            elif conflict_type == 'classroom':
                entity_label = entries[0].classroom.room_id if entries and entries[0].classroom else "Unknown Classroom"
            elif conflict_type == 'section':
                entity_label = entries[0].section.name if entries and entries[0].section else "Unknown Section"

            conflict_rows.append({
                'type': conflict_type,
                'day': grouped.day,
                'period': grouped.period,
                'entity': entity_label,
                'count': grouped.entry_count,
                'entries': [
                    {
                        'section': entry.section.name if entry.section else 'Unknown Section',
                        'teacher': entry.teacher.full_name if entry.teacher else 'Unknown Teacher',
                        'classroom': entry.classroom.room_id if entry.classroom else 'Unknown Classroom',
                        'subject': entry.subject.name if entry.subject else entry.course.name if entry.course else 'Unknown Subject'
                    }
                    for entry in entries
                ]
            })

    teacher_conflicts = db.session.query(
        TimetableEntry.day,
        TimetableEntry.period,
        TimetableEntry.teacher_id,
        func.count(TimetableEntry.id).label('entry_count')
    ).group_by(
        TimetableEntry.day,
        TimetableEntry.period,
        TimetableEntry.teacher_id
    ).having(func.count(TimetableEntry.id) > 1).all()

    classroom_conflicts = db.session.query(
        TimetableEntry.day,
        TimetableEntry.period,
        TimetableEntry.classroom_id,
        func.count(TimetableEntry.id).label('entry_count')
    ).group_by(
        TimetableEntry.day,
        TimetableEntry.period,
        TimetableEntry.classroom_id
    ).having(func.count(TimetableEntry.id) > 1).all()

    section_conflicts = db.session.query(
        TimetableEntry.day,
        TimetableEntry.period,
        TimetableEntry.section_id,
        func.count(TimetableEntry.id).label('entry_count')
    ).group_by(
        TimetableEntry.day,
        TimetableEntry.period,
        TimetableEntry.section_id
    ).having(func.count(TimetableEntry.id) > 1).all()

    build_conflict_rows('teacher', teacher_conflicts, 'teacher_id')
    build_conflict_rows('classroom', classroom_conflicts, 'classroom_id')
    build_conflict_rows('section', section_conflicts, 'section_id')

    conflict_rows.sort(key=lambda item: (item['day'], item['period'], item['type'], item['entity']))
    return conflict_rows


def get_working_days():
    config = AppConfig.query.filter_by(key='working_days').first()
    if not config:
        return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

    raw_value = config.value
    if raw_value.startswith('['):
        try:
            return json.loads(raw_value)
        except Exception:
            pass

    return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']


def get_period_count():
    start_config = AppConfig.query.filter_by(key='start_time').first()
    end_config = AppConfig.query.filter_by(key='end_time').first()
    duration_config = AppConfig.query.filter_by(key='period_duration').first()
    breaks_config = AppConfig.query.filter_by(key='breaks').first()

    if not start_config or not end_config or not duration_config:
        max_period = db.session.query(func.max(TimetableEntry.period)).scalar()
        return max_period or 8

    try:
        start_hour, start_minute = [int(part) for part in start_config.value.split(':')[:2]]
        end_hour, end_minute = [int(part) for part in end_config.value.split(':')[:2]]
        duration = int(duration_config.value)
        total_minutes = ((end_hour * 60) + end_minute) - ((start_hour * 60) + start_minute)

        break_minutes = 0
        if breaks_config and breaks_config.value:
            for item in json.loads(breaks_config.value):
                break_start_hour, break_start_minute = [int(part) for part in item['start_time'].split(':')[:2]]
                break_end_hour, break_end_minute = [int(part) for part in item['end_time'].split(':')[:2]]
                break_minutes += ((break_end_hour * 60) + break_end_minute) - ((break_start_hour * 60) + break_start_minute)

        usable_minutes = max(total_minutes - break_minutes, duration)
        return max(1, usable_minutes // duration)
    except Exception:
        max_period = db.session.query(func.max(TimetableEntry.period)).scalar()
        return max_period or 8


def auto_fix_conflicts():
    entries = TimetableEntry.query.order_by(TimetableEntry.id).all()
    classrooms = Classroom.query.order_by(Classroom.id).all()
    classroom_ids = [room.id for room in classrooms]
    working_days = get_working_days()
    day_order = {day: index for index, day in enumerate(working_days)}
    period_count = get_period_count()

    def slot_key(entry):
        return (entry.day, entry.period)

    teacher_slots = {}
    classroom_slots = {}
    section_slots = {}

    moved_entries = []
    unresolved_entries = []

    ordered_entries = sorted(
        entries,
        key=lambda item: (
            day_order.get(item.day, len(working_days)),
            item.period,
            item.id
        )
    )

    def slot_available(day, period, teacher_id, classroom_id, section_id):
        key = (day, period)
        return (
            key not in teacher_slots.get(teacher_id, set()) and
            key not in classroom_slots.get(classroom_id, set()) and
            key not in section_slots.get(section_id, set())
        )

    def reserve(entry):
        key = slot_key(entry)
        teacher_slots.setdefault(entry.teacher_id, set()).add(key)
        classroom_slots.setdefault(entry.classroom_id, set()).add(key)
        section_slots.setdefault(entry.section_id, set()).add(key)

    def candidate_slots(original_entry):
        same_day = [(original_entry.day, period) for period in range(1, period_count + 1)]
        other_days = [
            (day, period)
            for day in working_days
            if day != original_entry.day
            for period in range(1, period_count + 1)
        ]
        original_slot = (original_entry.day, original_entry.period)
        return [slot for slot in same_day + other_days if slot != original_slot]

    for entry in ordered_entries:
        if slot_available(entry.day, entry.period, entry.teacher_id, entry.classroom_id, entry.section_id):
            reserve(entry)
            continue

        moved = False
        for day, period in candidate_slots(entry):
            preferred_classrooms = [entry.classroom_id] + [room_id for room_id in classroom_ids if room_id != entry.classroom_id]
            for classroom_id in preferred_classrooms:
                if slot_available(day, period, entry.teacher_id, classroom_id, entry.section_id):
                    original = {'day': entry.day, 'period': entry.period, 'classroom_id': entry.classroom_id}
                    entry.day = day
                    entry.period = period
                    entry.classroom_id = classroom_id
                    reserve(entry)
                    moved_entries.append({
                        'entry_id': entry.id,
                        'from_day': original['day'],
                        'from_period': original['period'],
                        'to_day': day,
                        'to_period': period,
                        'from_classroom_id': original['classroom_id'],
                        'to_classroom_id': classroom_id
                    })
                    moved = True
                    break
            if moved:
                break

        if not moved:
            unresolved_entries.append(entry.id)

    db.session.commit()
    return {
        'moved': len(moved_entries),
        'unresolved': len(unresolved_entries),
        'remaining_conflicts': detect_conflicts(),
        'changes': moved_entries[:25]
    }


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


@analytics_bp.route('/conflict-details')
def conflict_details():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    return jsonify({
        "conflicts": get_conflict_details()
    })


@analytics_bp.route('/auto-fix-conflicts', methods=['POST'])
def auto_fix_conflicts_route():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        result = auto_fix_conflicts()
        return jsonify({
            "status": "success",
            **result
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
