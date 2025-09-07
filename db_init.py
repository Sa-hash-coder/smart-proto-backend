from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Course, Curriculum

engine = create_engine('sqlite:///smartproto.db', echo=False, future=True)
Session = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
    session = Session()
    # create sample users with simple passwords (prototype only)
    if session.query(User).count() == 0:
        t = User(name='alice', role='teacher', password='teachpass')
        s1 = User(name='bob', role='student', password='studpass1')
        s2 = User(name='carol', role='student', password='studpass2')
        session.add_all([t, s1, s2])
        session.commit()
        # create course
        c = Course(code='MATH101', title='Mathematics 101', teacher_id=t.id)
        session.add(c)
        session.commit()
        # curriculum items
        cur1 = Curriculum(course_id=c.id, title='Algebra', completed_percent=30)
        cur2 = Curriculum(course_id=c.id, title='Trigonometry', completed_percent=0)
        session.add_all([cur1, cur2])
        session.commit()
    session.close()

if __name__ == '__main__':
    init_db()
    print('DB initialized with sample data (smartproto.db)')
