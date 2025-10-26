from datetime import datetime
from app import db
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint

# Required tables for Replit Auth
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    enrollments = db.relationship('Enrollment', back_populates='user', cascade='all, delete-orphan')
    user_labs = db.relationship('UserLab', back_populates='user', cascade='all, delete-orphan')

class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.String, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)

    __table_args__ = (UniqueConstraint(
        'user_id',
        'browser_session_key',
        'provider',
        name='uq_user_browser_session_key_provider',
    ),)

# Course and Lab models
class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

    labs = db.relationship('Lab', back_populates='course', cascade='all, delete-orphan')
    enrollments = db.relationship('Enrollment', back_populates='course', cascade='all, delete-orphan')

class Lab(db.Model):
    __tablename__ = 'labs'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    name = db.Column(db.String, nullable=False)
    template_folder = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

    course = db.relationship('Course', back_populates='labs')
    user_labs = db.relationship('UserLab', back_populates='lab', cascade='all, delete-orphan')

class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship('User', back_populates='enrollments')
    course = db.relationship('Course', back_populates='enrollments')

    __table_args__ = (UniqueConstraint('user_id', 'course_id', name='uq_user_course'),)

class UserLab(db.Model):
    __tablename__ = 'user_labs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    lab_id = db.Column(db.Integer, db.ForeignKey('labs.id'), nullable=False)
    folder_name = db.Column(db.String, nullable=False)
    status = db.Column(db.String, default='ENROLLED')
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_accessed = db.Column(db.DateTime)

    user = db.relationship('User', back_populates='user_labs')
    lab = db.relationship('Lab', back_populates='user_labs')

    __table_args__ = (UniqueConstraint('user_id', 'lab_id', name='uq_user_lab'),)
