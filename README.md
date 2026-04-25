# 💙 Smart Classroom & Timetable Scheduler  

## Overview  
A **Smart Classroom & Timetable Scheduler** designed for Ajeenkya DY Patil University, Pune, India.  

This system automates **timetable generation, classroom allocation, and academic resource management** using intelligent scheduling techniques. It ensures **conflict-free, optimized, and efficient timetable creation** for both school and college environments.

---

## Developed By  
- Aditya Singh  
- Akhilesh Bajaj  
- Kunal Khandepekar  

---

## Key Features  

### Intelligent Scheduling Engine  
- Hybrid scheduling using **constraint validation + backtracking + optimization logic**  
- Automatically detects and resolves **lecture conflicts**  
- Dynamically calculates **accuracy & efficiency**  
- Supports **school structure & college semester system**  
- Suggests **alternate teachers and classrooms** when conflicts arise  

---

### Real-Time Dashboard Analytics  
- Displays live insights:
  - Total students  
  - Teacher–subject mapping  
  - Classroom availability  
  - Lectures per section  
  - Accuracy %  
  - Performance time  
- Smooth UI updates without heavy animations  

---

### Academic Resource Management  
- **Role-Based Access Control**  
  - Admin → Full control  
  - Student → View-only timetable  

- Features:
  - Secure authentication  
  - Batch & section management  
  - Teacher–subject assignment  
  - Classroom capacity tracking  
  - Course & subject management  
  - Exam scheduling  

---

### Accessibility Support  
- High contrast mode  
- Reader-friendly fonts  
- Voice-based navigation  
- Keyboard-only usability  
- Reduced motion interface  

---

### UI/UX Design  
- Modern **dark theme interface**  
- Glass-style dashboard panels  
- Fully responsive (optimized for laptops & presentations)  
- Simplified student view  
- Admin-only dashboard sections:
  - Recent Activity  
  - Quick Actions  

---

## System Architecture  

### Backend  
- Application entry point  
- Data models:
  - Users, Teachers, Students  
  - Classrooms, Departments, Semesters  
  - Sections & Timetable entries  
- Scheduling engine logic  
- REST APIs for:
  - Timetable generation  
  - Resource management  

---

### Frontend  
- Dashboard layout  
- Admin control panel  
- Student timetable view  
- Management modules:
  - Users  
  - Subjects  
  - Classrooms  
  - Exams  
- Initial setup wizard  

---

## Core Database Entities  
- **User** → Authentication & roles  
- **Teacher** → Faculty + subject allocation  
- **Student** → Batch & section mapping  
- **Section** → Lecture grouping  
- **Classroom** → Capacity & availability  
- **Timetable Entry** → Subject + teacher + room mapping  
- **Activity Logs** → Performance tracking  

---

## Configuration  

### Timetable Parameters  
- Working days  
- Lecture duration  
- Break slots  
- Max lectures per day  
- Teacher & classroom availability  

---

### Algorithm Optimization  
- Adaptive schedule population  
- Auto-adjust:
  - Generations  
  - Mutation rate  
  - Crossover logic  

---

### Accessibility Controls  
- UI contrast settings  
- Motion control  
- Navigation preferences  

---

## API Modules  

### Authentication  
- Login / Logout  
- Role-based session access  

### Scheduling  
- Generate timetable  
- Fetch timetable data  
- Dashboard analytics  

### Resource APIs  
- Teachers  
- Sections  
- Subjects  
- Classrooms  
- Exams  

---

## Security  
- Encrypted password storage  
- Secure session handling  
- Input validation  
- Parameterized queries (SQL injection prevention)  

---

## How It Works  

1. Admin logs into the system  
2. Navigates to **Timetable Generation**  
3. System processes all sections  
4. Applies scheduling algorithm  
5. Generates **conflict-free timetable**  
6. Stores accuracy & performance metrics  
7. Updates dashboard automatically  
8. Students can only **view final timetable**  

---

## Testing Workflow  
- Initialize database  
- Add resources (teachers, classrooms, subjects)  
- Generate timetable  
- Validate:
  - No conflicts  
  - Proper allocation  
  - Performance metrics  

---

## Common Issues & Fixes  

- **Database error** → Check DB connection & credentials  
- **Timetable not generating** → Ensure teacher–subject mapping exists  
- **Empty classrooms** → Add classroom data  
- **Dashboard blank** → Verify API response  
- **Login issue** → Check session role handling  

---

## Team Contributions  

| Member            | Contribution                                  |
|-------------------|-----------------------------------------------|
| Aditya Singh      | Database design, semester & subject structure |
| Akhilesh Bajaj    | Scheduling logic & constraints                |
| Kunal Khandepekar | UI integration, student view, dashboard       |

### Collaborative Work  
- System design  
- Feature integration  
- UI structuring  
- Testing & validation  
- Conflict resolution  

---

## Conclusion  
A complete **end-to-end smart scheduling solution** that improves efficiency, reduces manual effort, and ensures optimal academic resource utilization.

---