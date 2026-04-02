import os
import json
from datetime import datetime, timezone
from flask import Flask, request, redirect, url_for, g

from config import Config
from extensions import db
from models import AppConfig, User, Subject, Course, TimetableEntry, SystemMetric


def create_app(config_class=Config):
    # --- App Initialization ---
    app = Flask(__name__)
    app.config.from_object(config_class)

    # --- Initialize Extensions ---
    db.init_app(app)

    # CREATE TABLES ON STARTUP
    with app.app_context():
        db.create_all()

    # --- Import and Register Blueprints ---
    from routes.main import main_bp
    from routes.structure import structure_bp
    from routes.subjects import subjects_bp
    from routes.staff import staff_bp
    from routes.classrooms import classrooms_bp
    from routes.sections import sections_bp
    from routes.timetable import timetable_bp
    from routes.analytics import analytics_bp
    from routes.api import api_bp
    from routes.exams import exams_bp
    from routes.electives import electives_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(structure_bp)
    app.register_blueprint(subjects_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(classrooms_bp)
    app.register_blueprint(sections_bp)
    app.register_blueprint(timetable_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(exams_bp)
    app.register_blueprint(electives_bp)

    # --- Application Hooks ---
    @app.before_request
    def check_setup():
        if request.endpoint and (
            'static' in request.endpoint or 
            'main.setup' in request.endpoint or
            'main.generate_fake_data' in request.endpoint
        ):
            return

        try:
            if not AppConfig.query.filter_by(key='setup_complete', value='true').first():
                return redirect(url_for('main.setup'))

            config = AppConfig.query.filter_by(key='app_mode').first()
            if config:
                g.app_mode = config.value

        except Exception as e:
            # 🔥 IMPORTANT FIX (avoid crash on first run)
            print(f"DB not ready yet: {e}")
            return None

    # --- Global Variables ---
    @app.context_processor
    def inject_global_vars():
        try:
            config = AppConfig.query.filter_by(key='institute_name').first()
            return {'institute_name': config.value if config else 'Scheduler AI'}
        except Exception:
            return {'institute_name': 'Scheduler AI'}

    # OPTIONAL: Metrics safe execution
    with app.app_context():
        try:
            today = datetime.now(timezone.utc).date()

            if not SystemMetric.query.filter_by(date=today).first():
                db.session.add(SystemMetric(
                    key='total_students',
                    value=User.query.filter_by(role='student').count()
                ))
                db.session.add(SystemMetric(
                    key='total_teachers',
                    value=User.query.filter_by(role='teacher').count()
                ))

                total_subjects = Subject.query.count() + Course.query.count()
                db.session.add(SystemMetric(
                    key='total_subjects',
                    value=total_subjects
                ))

                db.session.add(SystemMetric(
                    key='classes_scheduled',
                    value=TimetableEntry.query.count()
                ))

                db.session.commit()

        except Exception as e:
            print(f"Metrics error: {e}")

    return app


# --- Local only ---
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=8000)