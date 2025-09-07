from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Course, Curriculum, Attendance, QRToken
from datetime import datetime, timedelta
import uuid, qrcode, io, base64, jwt

# SECRET for JWT (prototype). In production, store safely in env variables.
JWT_SECRET = 'replace_this_with_a_real_secret'

engine = create_engine('sqlite:///smartproto.db', echo=False, future=True)
Session = sessionmaker(bind=engine)

app = Flask(__name__)
CORS(app)

def create_token(user):
    payload = {
        'user_id': user.id,
        'name': user.name,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(hours=8)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    return token

def decode_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except Exception as e:
        return None

def auth_required(roles=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            auth = request.headers.get('Authorization', '')
            if not auth.startswith('Bearer '):
                return jsonify({'error':'missing token'}), 401
            token = auth.split(' ',1)[1]
            payload = decode_token(token)
            if not payload:
                return jsonify({'error':'invalid token'}), 401
            if roles and payload.get('role') not in roles:
                return jsonify({'error':'forbidden'}), 403
            # attach user info to request context
            request.user = payload
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    name = data.get('name')
    password = data.get('password')
    session = Session()
    user = session.query(User).filter_by(name=name, password=password).first()
    session.close()
    if not user:
        return jsonify({'error':'invalid credentials'}), 401
    token = create_token(user)
    return jsonify({'token': token, 'user': {'id': user.id, 'name': user.name, 'role': user.role}})

@app.route('/courses')
def get_courses():
    session = Session()
    courses = session.query(Course).all()
    out = []
    for c in courses:
        out.append({'id': c.id, 'code': c.code, 'title': c.title, 'teacher': c.teacher.name})
    session.close()
    return jsonify(out)

@app.route('/curriculum/<int:course_id>')
def get_curriculum(course_id):
    session = Session()
    items = session.query(Curriculum).filter_by(course_id=course_id).all()
    out = [{'id': it.id, 'title': it.title, 'completed_percent': it.completed_percent} for it in items]
    session.close()
    return jsonify(out)

@app.route('/update_curriculum', methods=['POST'])
@auth_required(roles=['teacher'])
def update_curriculum():
    data = request.json
    session = Session()
    item = session.get(Curriculum, data['id'])
    if not item:
        session.close()
        return jsonify({'error': 'not found'}), 404
    item.completed_percent = float(data['completed_percent'])
    session.commit()
    out = {'id': item.id, 'completed_percent': item.completed_percent}
    session.close()
    return jsonify(out)

@app.route('/generate_qr', methods=['POST'])
@auth_required(roles=['teacher'])
def generate_qr():
    data = request.json
    course_id = data.get('course_id')
    valid_seconds = int(data.get('valid_seconds', 300))
    token = str(uuid.uuid4())[:8]
    session = Session()
    qt = QRToken(course_id=course_id, token=token, valid_until=datetime.utcnow() + timedelta(seconds=valid_seconds))
    session.add(qt)
    session.commit()
    session.close()
    return jsonify({'token': token, 'valid_seconds': valid_seconds})

@app.route('/generate_qr_image', methods=['POST'])
@auth_required(roles=['teacher'])
def generate_qr_image():
    data = request.json
    course_id = data.get('course_id')
    valid_seconds = int(data.get('valid_seconds', 300))
    token = str(uuid.uuid4())[:8]
    session = Session()
    qt = QRToken(course_id=course_id, token=token, valid_until=datetime.utcnow() + timedelta(seconds=valid_seconds))
    session.add(qt)
    session.commit()
    session.close()

    payload = token
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return jsonify({'token': token, 'valid_seconds': valid_seconds, 'image_base64': b64})

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    data = request.json
    session = Session()
    token = data.get('token')
    if token:
        qt = session.query(QRToken).filter_by(token=token).first()
        if not qt or qt.valid_until < datetime.utcnow():
            session.close()
            return jsonify({'status': 'failed', 'reason': 'invalid or expired token'}), 400
        student_id = data.get('student_id')
        rec = Attendance(student_id=student_id, course_id=qt.course_id, via_token=True)
        session.add(rec)
        session.commit()
        session.close()
        return jsonify({'status': 'success', 'via': 'token'})
    student_id = data.get('student_id')
    course_id = data.get('course_id')
    if not student_id or not course_id:
        session.close()
        return jsonify({'status': 'failed', 'reason': 'missing student_id/course_id'}), 400
    rec = Attendance(student_id=student_id, course_id=course_id, via_token=False)
    session.add(rec)
    session.commit()
    session.close()
    return jsonify({'status': 'success', 'via': 'manual'})

@app.route('/attendance_report/<int:course_id>')
def attendance_report(course_id):
    session = Session()
    total_students = session.query(User).filter_by(role='student').count()
    attendances = session.query(Attendance).filter_by(course_id=course_id).count()
    percent = (attendances / (total_students or 1)) * 100
    session.close()
    return jsonify({'course_id': course_id, 'attendance_records': attendances, 'students_total': total_students, 'attendance_percent': percent})

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
