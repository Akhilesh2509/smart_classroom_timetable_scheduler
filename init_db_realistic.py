#!/usr/bin/env python3
import os
import sys
from faker import Faker
import random
from datetime import datetime, time, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, Teacher, Student, StudentSection, Department, Semester, Course, Subject, Classroom, TimetableEntry, Grade, SchoolGroup, Stream, Exam, ExamSeating, AppConfig
from werkzeug.security import generate_password_hash
from sqlalchemy import text

fake = Faker()


def get_or_create_student_section(base_name, department, grade, sections, capacity=30):
    matching_sections = [
        section for section in sections
        if section.department_id == department.id and section.name.startswith(base_name)
    ]

    for section in matching_sections:
        if len(section.students) < section.capacity:
            return section

    suffix = "" if not matching_sections else f" - {len(matching_sections) + 1}"
    new_section = StudentSection(
        name=f"{base_name}{suffix}",
        capacity=capacity,
        grade=grade,
        department=department
    )
    db.session.add(new_section)
    db.session.flush()
    sections.append(new_section)
    return new_section

def clear_database():
    """Clear all existing data"""
    print("🧹 Clearing existing database...")
    
    # Delete in correct order to avoid foreign key constraints
    try:
        # First delete all timetable entries
        db.session.query(TimetableEntry).delete()
        
        # Delete exam related data
        db.session.query(ExamSeating).delete()
        db.session.query(Exam).delete()
        
        # Delete students
        db.session.query(Student).delete()
        
        # Delete teacher-course associations first
        from sqlalchemy import text
        try:
            db.session.execute(text("DELETE FROM teacher_college_courses"))
            db.session.execute(text("DELETE FROM teacher_school_subjects"))
        except:
            pass
        
        # Delete teachers
        db.session.query(Teacher).delete()
        
        # Delete sections
        db.session.query(StudentSection).delete()
        
        # Delete classrooms
        db.session.query(Classroom).delete()
        
        # Delete subjects
        db.session.query(Subject).delete()
        
        # Delete courses
        db.session.query(Course).delete()
        
        # Delete streams
        db.session.query(Stream).delete()
        
        # Delete grades
        db.session.query(Grade).delete()
        
        # Delete departments
        db.session.query(Department).delete()
        
        # Delete semesters
        db.session.query(Semester).delete()
        
        # Delete school groups
        db.session.query(SchoolGroup).delete()
        
        # Delete users last
        db.session.query(User).delete()
        
        # Delete AppConfig
        db.session.query(AppConfig).delete()
        db.session.commit()
        
        print("✅ Database cleared")
        
    except Exception as e:
        print(f"⚠️ Error clearing database: {e}")
        db.session.rollback()
        # Try alternative approach - drop and recreate tables
        print("🔄 Trying alternative approach...")
        db.drop_all()
        db.create_all()
        print("✅ Database recreated")

def create_realistic_data():
    """Create realistic school/college data"""
    print("🏗️ Creating realistic data...")
    teacher_password_hash = generate_password_hash("teacher123")
    student_password_hash = generate_password_hash("student123")
    admin_password_hash = generate_password_hash("admin123")
    
    # Create school group
    school_group = SchoolGroup(name="ADYPU")
    db.session.add(school_group)
    
    # Create semesters
    semesters = []
    for i in range(1, 9):  # 8 semesters
        semester = Semester(name=f"SEM {i}")
        db.session.add(semester)
        semesters.append(semester)
    
    # Create departments with realistic names
    department_names = [
        "Computer Science Engineering",
        "Electronics and Communication Engineering", 
        "Information Technology",
        "Mechanical Engineering",
        "Civil Engineering",
        "Electrical Engineering",
        "Aerospace Engineering",
        "Chemical Engineering"
    ]
    
    departments = []
    for i, name in enumerate(department_names):
        # Assign each department to 2 semesters
        dept = Department(name=name, semester=semesters[i % len(semesters)])
        db.session.add(dept)
        departments.append(dept)
    
    # Create realistic subjects for each department
    subjects_data = {
        "Computer Science Engineering": [
            ("Data Structures", "CSE_DS101", 4, False),
            ("Algorithms", "CSE_ALG102", 4, False),
            ("Object Oriented Programming", "CSE_OOP103", 3, False),
            ("Database Management Systems", "CSE_DBMS201", 4, False),
        ],
        "Electronics and Communication Engineering": [
            ("Digital Electronics", "ECE_DE101", 4, False),
            ("Analog Electronics", "ECE_AE102", 4, False),
            ("Signals and Systems", "ECE_SS103", 4, False),
            ("Communication Systems", "ECE_CS201", 4, False),
        ],
        "Information Technology": [
            ("Programming Fundamentals", "IT_PF101", 4, False),
            ("Data Structures and Algorithms", "IT_DSA102", 4, False),
            ("Database Systems", "IT_DBS103", 4, False),
            ("Web Technologies", "IT_WT201", 3, False),
        ],
        "Mechanical Engineering": [
            ("Engineering Mechanics", "ME_EM101", 4, False),
            ("Thermodynamics", "ME_TD102", 4, False),
            ("Fluid Mechanics", "ME_FM103", 4, False),
            ("Machine Design", "ME_MD201", 4, False),
        ],
        "Civil Engineering": [
            ("Structural Analysis", "CE_SA101", 4, False),
            ("Concrete Technology", "CE_CT102", 4, False),
            ("Soil Mechanics", "CE_SM103", 4, False),
            ("Transportation Engineering", "CE_TE201", 3, False),
        ],
        "Electrical Engineering": [
            ("Circuit Analysis", "EE_CA101", 4, False),
            ("Electromagnetic Fields", "EE_EMF102", 4, False),
            ("Power Systems", "EE_PS103", 4, False),
            ("Control Systems", "EE_CS201", 3, False),
        ],
        "Aerospace Engineering": [
            ("Aerodynamics", "AE_AD101", 4, False),
            ("Flight Mechanics", "AE_FM102", 4, False),
            ("Aircraft Structures", "AE_AS103", 4, False),
            ("Propulsion Systems", "AE_PS201", 3, False),
        ],
        "Chemical Engineering": [
            ("Chemical Process Calculations", "CHE_CPC101", 4, False),
            ("Thermodynamics", "CHE_TD102", 4, False),
            ("Mass Transfer", "CHE_MT103", 4, False),
            ("Heat Transfer", "CHE_HT201", 3, False),
        ]
    }
    
    # Create subjects for each department
    subjects = []
    for dept in departments:
        dept_name = dept.name
        if dept_name in subjects_data:
            for subject_name, code, hours, is_elective in subjects_data[dept_name]:
                stream = Stream(name=f"{dept_name} Stream", group=school_group)
                db.session.add(stream)
                
                subject = Subject(
                    name=subject_name,
                    code=code,
                    weekly_hours=hours,
                    is_elective=is_elective,
                    stream=stream
                )
                db.session.add(subject)
                subjects.append(subject)
    
    
    # Create courses for each department
    courses = []
    for dept in departments:
        dept_name = dept.name
        if dept_name in subjects_data:
            for subject_name, code, hours, is_elective in subjects_data[dept_name]:
                course = Course(
                    name=subject_name,
                    code=code,
                    credits=hours,
                    course_type="Core" if not is_elective else "Elective",
                    department=dept
                )
                db.session.add(course)
                courses.append(course)
    
    db.session.flush()
    
    # Create grades
    grades = []
    for i in range(1, 9):  # 8 grades
        grade = Grade(name=f"Grade {i}", group=school_group)
        db.session.add(grade)
        grades.append(grade)
    
    # Create sections for each department
    sections = []
    section_labels = ['Section A', 'Section B']
    for dept in departments:
        for section_name in section_labels:  # 2 sections per department
            section = StudentSection(
                name=section_name,
                capacity=30,
                grade=grades[len(sections) % len(grades)],
                department=dept
            )
            db.session.add(section)
            sections.append(section)
    
    db.session.flush()
    
    # Create classrooms
    classrooms = []
    building_names = ['A', 'B']
    for building in building_names:
        for floor in range(1, 3):  # 2 floors
            for room in range(1, 4):  # 3 rooms per floor
                room_id = f"{building}{floor}{room:02d}"
                capacity = random.randint(25, 50)
                features = random.choice([
                    "Projector, Whiteboard, AC",
                    "Smart Board, Projector, AC",
                    "Whiteboard, AC",
                    "Projector, Whiteboard",
                    "Smart Board, AC"
                ])
                
                classroom = Classroom(
                    room_id=room_id,
                    capacity=capacity,
                    features=features
                )
                db.session.add(classroom)
                classrooms.append(classroom)
    
    db.session.flush()
    
    # Create users and teachers
    teachers = []
    for i in range(60):  # 60 teachers
        user = User(
            username=f"teacher{i+1:02d}",
            email=f"teacher{i+1:02d}@adypu.edu.in",
            password=teacher_password_hash,
            role="teacher"
        )
        teacher = Teacher(
            user=user,
            full_name=fake.name(),
            max_weekly_hours=random.randint(20, 30)
        )
        db.session.add_all([user, teacher])
        teachers.append(teacher)
    
    db.session.flush()
    
    # Assign teachers to courses (ensure proper subject-department matching)
    teacher_course_assignments = []
    teacher_loads = {teacher.id: 0 for teacher in teachers}
    for course in courses:
        available_teachers = [teacher for teacher in teachers if teacher_loads[teacher.id] < 5]
        if available_teachers:
            teacher = random.choice(available_teachers)
            teacher_course_assignments.append((teacher.id, course.id))
            teacher_loads[teacher.id] += 1
    
    # Insert teacher-course assignments into database
    if teacher_course_assignments:
        print(f"🔗 Assigning {len(teacher_course_assignments)} teacher-course relationships...")
        for teacher_id, course_id in teacher_course_assignments:
            db.session.execute(text(
                "INSERT INTO teacher_college_courses (teacher_id, course_id) VALUES (:teacher_id, :course_id)"
            ), {"teacher_id": teacher_id, "course_id": course_id})
        db.session.commit()
        print("✅ Teacher-course assignments completed!")
    
    # Create students beyond the initial section capacity so overflow sections are generated.
    students = []
    target_student_count = 720
    for i in range(target_student_count):
        user = User(
            username=f"student{i+1:03d}",
            email=f"student{i+1:03d}@adypu.edu.in",
            password=student_password_hash,
            role="student"
        )
        department = random.choice(departments)
        base_section_name = random.choice(section_labels)
        grade = grades[i % len(grades)]
        section = get_or_create_student_section(base_section_name, department, grade, sections)
        student = Student(
            user=user,
            full_name=fake.name(),
            section=section
        )
        db.session.add_all([user, student])
        students.append(student)
    
    db.session.flush()

    # Create class-wise exams so generated fake data can be scheduled immediately.
    exams = []
    exam_start = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=7)
    for section in sections:
        section_courses = [course for course in courses if course.department_id == section.department_id]
        for course_index, course in enumerate(section_courses[:3]):
            exam = Exam(
                name=f"{section.name} - {course.name} Final",
                date=exam_start + timedelta(days=course_index),
                duration=180,
                type="final",
                course_id=course.id
            )
            db.session.add(exam)
            exams.append(exam)
    
    # Create admin user
    if not User.query.filter_by(username="admin").first():
        admin_user = User(
            username="admin",
            email="admin@adypu.edu.in",
            password=admin_password_hash,
            role="admin"
        )
        db.session.add(admin_user)
    
    # Add AppConfig
    configs = [
        ('institute_name', 'ADYPU'),
        ('app_mode', 'college'),
        ('working_days', '["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]'),
        ('start_time', '09:00'),
        ('end_time', '17:00'),
        ('period_duration', '60'),
        ('breaks', '[{"name": "Lunch Break", "start_time": "13:00", "end_time": "14:00"}]'),
        ('setup_complete', 'true'),
        ('last_schedule_accuracy', '95.0'),
        ('last_generation_time', '2.5')
    ]
    
    for key, value in configs:
        config = AppConfig(key=key, value=value)
        db.session.add(config)
    
    db.session.commit()
    
    print(f"✅ Created realistic data:")
    print(f"   📚 Semesters: {len(semesters)}")
    print(f"   🏢 Departments: {len(departments)}")
    print(f"   📖 Subjects: {len(subjects)}")
    print(f"   📚 Courses: {len(courses)}")
    print(f"   👥 Sections: {len(sections)}")
    print(f"   🏫 Classrooms: {len(classrooms)}")
    print(f"   👨‍🏫 Teachers: {len(teachers)}")
    print(f"   👨‍🎓 Students: {len(students)}")
    print(f"   📊 Total capacity: {sum(section.capacity for section in sections)} students")
    
    return {
        'semesters': semesters,
        'departments': departments,
        'subjects': subjects,
        'courses': courses,
        'sections': sections,
        'classrooms': classrooms,
        'teachers': teachers,
        'students': students,
        'exams': exams
    }

def main():
    """Main function to initialize the database"""
    app = create_app()
    
    with app.app_context():
        try:
            clear_database()
            data = create_realistic_data()
            print("\n🎉 Database initialization completed successfully!")
            print("\n📋 Login credentials:")
            print("   Admin: admin / admin123")
            print("   Teachers: teacher01-teacher80 / teacher123")
            print(f"   Students: student001-student{len(data['students']):03d} / student123")
            
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    main()
