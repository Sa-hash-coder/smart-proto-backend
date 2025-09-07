# Backend (Flask) with JWT login (prototype)

1. Create virtualenv, install requirements:

   python -m venv venv
   source venv/bin/activate   # Windows: venv\\Scripts\\activate
   pip install -r requirements.txt

2. Initialize DB with sample data:
   python db_init.py

3. Run backend:
   python app.py

Sample users created in DB:
- alice / teachpass (teacher)
- bob   / studpass1 (student)
- carol / studpass2 (student)

APIs:
- POST /login {name, password} -> returns JWT token
- GET /courses
- GET /curriculum/<course_id>
- POST /update_curriculum {id, completed_percent} [teacher auth required]
- POST /generate_qr {course_id, valid_seconds} [teacher auth required]
- POST /generate_qr_image {course_id, valid_seconds} [teacher auth required]
- POST /mark_attendance {token OR student_id+course_id}
- GET /attendance_report/<course_id>
