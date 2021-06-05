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

    def manage(self, v2, v3, prev, v3_gen):
        """
        Gerencia o registro dos pids v2, v3, prev no `pid_manager`.

        Se no artigo XML há v3, vale todos os pids "presentes" no XML
        (v2 e previous_pid se aplicável) e desconsidera o que estiver
        registrado no `pid_manager`, pois esta abordagem permite a correção dos
        dados.

        Se no artigo não há v3, consulta os registros pelo `previous_pid`
        ou `v2`.

        Se detectar registros repetidos, apaga.
        """
        self.session = self.Session()
        q = self.session.query(PidVersion)
        ret = (
            self._search_by_v3(q, v2, v3, prev) or
            self._search_by_v2_and_prev(q, v2, prev, v3_gen)
        )
        if not ret:
            return None
        try:
            self.session.commit()
        except Exception as e:
            logging.debug("%s" % str(e))
            self.session.rollback()
        else:
            return ret

    def _search_by_v3(self, q, v2, v3, prev):
        """
        Se no artigo XML há v3, vale todos os pids "presentes" no XML
        (v2 e previous_pid se aplicável) e desconsidera o que estiver
        registrado no `pid_manager`, pois esta abordagem permite a correção dos
        dados.
        """
        # obtém os registros em que há `v3` igual a `v3`
        v3_records = [] or v3 and q.filter_by(v3=v3).all()
        if v3_records:
            for rec in v3_records:
                # apaga os registros
                self.session.delete(rec)
            # registra os pares (v2, v3) e (prev, v3), se existir
            for pid_v2 in (v2, prev):
                if pid_v2:
                    # adicionar registros com o par (pid_v2, v3)
                    self.session.add(PidVersion(v2=pid_v2, v3=v3))
            # finaliza
            return (v2, v3, prev)

    def _search_by_v2_and_prev(self, q, v2, prev, v3_gen):
        """
        Se no artigo não há v3, consulta os registros pelo `previous_pid`
        ou `v2`.
        """
        # obtém os registros em que `v2` é igual a `prev`
        prev_records = [] or prev and q.filter_by(v2=prev).all()

        # obtém os registros em que `v2` é igual a `v2`
        v2_records = [] or v2 and q.filter_by(v2=v2).all()

        # obtém os `v3` encontrados no resultado da consulta
        v3_values = set([record.v3 for record in prev_records + v2_records])

        return (
            self._search_by_v2_and_prev__no_record_found(
                v2, prev, v3_values, v3_gen) or
            self._search_by_v2_and_prev__one_v3_found(
                v2, prev, v3_values, v2_records, prev_records) or
            self._search_by_first_of_prev_or_v2(
                q, v2, prev, v2_records, prev_records)
        )

    def _search_by_v2_and_prev__no_record_found(
            self, v2, prev, v3_values, v3_gen):
        """
        Consulta os registros pelo `previous_pid` ou `v2`.
        Mas nenhum registro foi encontrado.
        """
        if not v3_values:
            # gera um v3
            v3 = v3_gen()
            # registra os pares (v2, v3) e/ou (prev, v3)
            for pid_v2 in (v2, prev):
                if pid_v2:
                    # adicionar registros com o par (pid_v2, v3)
                    self.session.add(PidVersion(v2=pid_v2, v3=v3))
            # finaliza
            return (v2, v3, prev)

    def _search_by_v2_and_prev__one_v3_found(
            self, v2, prev, v3_values, v2_records, prev_records):
        """
        Consulta os registros pelo `previous_pid` ou `v2`.
        Todos os registros encontrados contém o mesmo valor para `v3`.
        Possível encontrar de 1 a n registros.
        """
        if len(v3_values) == 1:
            v3 = v3_values.pop()

            # pelo menos 1 registro encontrado, de prev ou de v2 ou de ambos
            if len(prev_records) == len(v2_records) == 1:
                # ambos
                # finaliza
                return (v2, v3, prev)

            # apaga os registros excedentes, se existirem
            self._remove_exceding_records((prev_records[1:], v2_records[1:]))

            # cria registro, se não existir
            if prev and len(prev_records) == 0:
                # adicionar registro com o par (prev, v3), se não existir
                self.session.add(PidVersion(v2=prev, v3=v3))
            if v2 and len(v2_records) == 0:
                # adicionar registro com o par (v2, v3), se não existir
                self.session.add(PidVersion(v2=v2, v3=v3))
            # finaliza
            return (v2, v3, prev)

    def _search_by_first_of_prev_or_v2(
            self, q, v2, prev, v2_records, prev_records):
        """
        Consulta os registros pelo `previous_pid` ou `v2`.
        Mas os registros encontrados contém mais de um valor para `v3`.

        Obtém o primeiro registro,
        considerando a sequencia de prioridade `previous_pid` ou `v2`,
        valem os dados do primeiro encontrado.
        """
        record = (
            prev and q.filter_by(v2=prev).first() or
            v2 and q.filter_by(v2=v2).first()
        )
        if record:
            self._remove_exceding_records((prev_records, v2_records), [record])
            return (v2, record.v3, prev)

    def _remove_exceding_records(self, group_of_records, valid_records=None):
        """
        Apaga os registros excedentes, se existirem
        """
        valid_records = valid_records or []
        for records in group_of_records:
            for rec in records:
                if rec not in valid_records:
                    self.session.delete(rec)

    def close(self):
        self.__exit__()
