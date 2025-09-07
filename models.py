from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'student' or 'teacher'
    password = Column(String, nullable=True)  # plaintext in prototype (do NOT use in production)

class Course(Base):
    __tablename__ = 'courses'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True)
    title = Column(String)
    teacher_id = Column(Integer, ForeignKey('users.id'))
    teacher = relationship('User')

class Curriculum(Base):
    __tablename__ = 'curriculum'
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'))
    title = Column(String)
    completed_percent = Column(Float, default=0.0)
    course = relationship('Course')

class Attendance(Base):
    __tablename__ = 'attendance'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('users.id'))
    course_id = Column(Integer, ForeignKey('courses.id'))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    via_token = Column(Boolean, default=False)
    student = relationship('User')
    course = relationship('Course')

class QRToken(Base):
    __tablename__ = 'qr_tokens'
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'))
    token = Column(String, unique=True)
    valid_until = Column(DateTime)
    course = relationship('Course')
