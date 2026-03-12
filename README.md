## 💙 Smart Classroom & Timetable Scheduler

## 🎓 Smart Classroom & Timetable Scheduler</span>
A smart scheduling and classroom automation system built for Ajeenkya DY Patil University, Pune, India

Developed by Team:

--- Aditya Singh

--- Akhilesh Bajaj

--- Kunal Khandepekar

## 🌟 Key Features
### 🧠 Intelligent Scheduling System

Uses a hybrid approach that combines smart planning, constraint validation, and backtracking mechanisms
Calculates timetable accuracy and technique efficiency dynamically
Detects and avoids lecture conflicts automatically
Supports both school structure and college semester–department structure
Reassigns alternative teacher and classroom options when required

## 📊 Real-Time Dashboard Analytics

Displays live insights on:
Total students
Teacher and subject mapping
Classrooms availability
Lectures scheduled per section
Accuracy percentage
Performance duration
Provides smooth activity updates without overwhelming animations

## 👥 Academic Resource Management

User Access:
Admin gets full control, students get only timetable access
Secure account authentication
Batch-wise student section grouping
Teacher subject assignment panel
Classroom capacity tracking
Subjects and courses management
Exam scheduling interface

## ♿ Accessibility Support

High contrast mode
Reader-friendly fonts
Voice-based navigation support
Keyboard-only interface usability
Controlled motion effects for better readability

## 🎨 UI Design Structure

Dark theme interface
Professional glass-style panels
Fully responsive layout for laptops and desktops used in college presentations
Simplified student view interface
Dashboard sections like Recent Activity and Quick Actions visible only in admin login
Section Timetables panel hidden for students and also hidden for admin home view unless accessed separately

## 🏗 System Overview
### Backend Includes

Application entry point
Data models for users, teachers, classrooms, semesters, departments, sections, and timetable entries
Scheduling utilities
API routing for timetable generation and resource handling

### Frontend Includes

A base dashboard layout
Student timetable view
Admin scheduling panel
Users, subjects, classrooms, batches and exam management pages
Initial setup UI wizard

## Core Database Entities

User: login role and access
Teacher: faculty details and subject allocation
Student: batch and section mapping
Section: lecture division
Classroom: room capacity and availability
Timetable Entry: lecture schedule with subjects, teacher, and room mapping
Activity Logs and Metrics: system performance and activity tracking

## ⚙ Project Configuration
### Timetable Parameters

Working days setup
Period durations
Break slots management
Max lectures per day per section
Teacher and classroom availability validation

### Algorithm Tuning

Schedule population size adapts based on number of sections
Generations, mutation, and crossover parameters adjust automatically

### Accessibility Controls

UI contrast
Motion strength
Navigation mode

## 🛠 API Functions
### User Login & Session

Login authentication
Logout
Role-based session access

### Scheduling & Performance

Timetable generation call
Retrieve timetable data
Dashboard statistics fetch
Teachers, sections, classrooms, subjects, exams API routing

## 🔒 System Security

Encrypted password storage
Secure session handling
Input validation
Parameterized database queries

## 🎯 Timetable Generation Guide

Login as Admin
Open Timetable page
Generate Timetable
System processes sections
Accuracy and performance measured and stored
Timetables mapped with subject, teacher and classroom
Display updates automatically on dashboard
Students view only timetable, not generation panel

## 🧪 Testing Flow

Run database initializer
Generate timetable
Observe dashboard updates
Ensure no conflicts and good accuracy
Validate resource usage statistics

## 🐛 Common Issues & Fix Areas

Database connection → ensure DB is running and credentials are correct
Timetable not generating → ensure subject-teacher mapping exists
Classroom empty → ensure classroom data is added
Dashboard blank → check if API response is reaching UI properly
Login not redirecting → ensure session role is passed correctly

## 🤝 Team Contribution Summary
Team Member Names --- Major Focus
Aditya Singh -------- UI integration + student login view + dashboard layout
Akhilesh Bajaj ------ Database design + semester & subject structure
Kunal Khandepekar --- Lecture scheduling and constraint mapping

## Collaborative Work Done Together:

System planning
Feature integration
UI organization
Data testing
Conflict validation

### ❤️ Made with teamwork at Ajeenkya DY Patil University
