import sqlite3
import logging

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, UniqueConstraint, create_engine
from sqlalchemy.orm import sessionmaker


Base = declarative_base()


class PidVersion(Base):
    __tablename__ = 'pid_versions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    v2 = Column(String(23))
    v3 = Column(String(255))
    __table_args__ = (
        UniqueConstraint('v2', 'v3', name='_v2_v3_uc'),
    )

    def __repr__(self):
        return '<PidVersion(v2="%s", v3="%s")>' % (self.v2, self.v3)


class PIDVersionsManager:
    def __init__(self, name, timeout=None):
        engine_args = {"pool_timeout": timeout} if timeout else {}
        self.engine = create_engine(name, **engine_args)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def __enter__(self):
        return self

    def __exit__(self, excution_type, excution_value, traceback):

        if hasattr(self, "session") and self.session:
            if isinstance(excution_value, Exception):
                self.session.rollback()
            else:
                self.session.commit()
            self.session.close()

    def register(self, v2, v3):
        self.session = self.Session()
        self.session.add(PidVersion(v2=v2, v3=v3))
        try:
            self.session.commit()
        except:
            logging.debug("this item already exists in database")
            self.session.rollback()
            return False
        else:
            return True

    def get_pid_v3(self, v2):
        self.session = self.Session()
        pid_register = self.session.query(PidVersion).filter_by(v2=v2).first()
        if pid_register:
            return pid_register.v3

    def pids_already_registered(self, v2, v3):
        """Verifica se a chave composta (v2 e v3) existe no banco de dadoss"""
        self.session = self.Session()
        return self.session.query(PidVersion).filter_by(v2=v2, v3=v3).count() == 1

    def close(self):
        self.__exit__()
