from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
import enum

from database import db


class LabStatus(enum.Enum):
    ENROLLED = "ENROLLED"
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"


class Base(db.Model):
    __abstract__ = True
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base):
    __tablename__ = 'users'
    
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    google_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    
    labs: Mapped[List["Lab"]] = relationship("Lab", back_populates="user", cascade="all, delete-orphan")
    user_courses: Mapped[List["UserCourse"]] = relationship("UserCourse", back_populates="user", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'google_id': self.google_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Course(Base):
    __tablename__ = 'courses'
    
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    
    user_courses: Mapped[List["UserCourse"]] = relationship("UserCourse", back_populates="course", cascade="all, delete-orphan")
    labs: Mapped[List["Lab"]] = relationship("Lab", back_populates="course", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class UserCourse(Base):
    __tablename__ = 'user_courses'
    
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey('courses.id'), nullable=False)
    
    user: Mapped["User"] = relationship("User", back_populates="user_courses")
    course: Mapped["Course"] = relationship("Course", back_populates="user_courses")


class Lab(Base):
    __tablename__ = 'labs'
    
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey('courses.id'), nullable=False)
    lab_name: Mapped[str] = mapped_column(String(255), nullable=False)
    template_name: Mapped[str] = mapped_column(String(255), nullable=False)
    folder_name: Mapped[str] = mapped_column(String(255), nullable=False)
    folder_path: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[LabStatus] = mapped_column(SQLEnum(LabStatus), default=LabStatus.ENROLLED, nullable=False)
    
    user: Mapped["User"] = relationship("User", back_populates="labs")
    course: Mapped["Course"] = relationship("Course", back_populates="labs")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'lab_name': self.lab_name,
            'template_name': self.template_name,
            'folder_name': self.folder_name,
            'folder_path': self.folder_path,
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class LabTemplate(Base):
    __tablename__ = 'lab_templates'
    
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    folder_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'folder_name': self.folder_name,
            'description': self.description
        }
