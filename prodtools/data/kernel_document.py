import copy
import logging
import sqlite3

from typing import Optional

from lxml import etree  # type: ignore

from prodtools.utils import fs_utils
from prodtools.utils import xml_utils
from prodtools.db.pid_versions import PIDVersionsManager
from . import scielo_id_gen

LOGGER = logging.getLogger(__name__)


def old_add_article_id_to_received_documents(
    pid_manager: PIDVersionsManager,
    issn_id: str,
    year_and_order: str,
    received_docs: dict,
    documents_in_isis: dict,
    file_paths: dict,
    update_article_with_aop_status: callable,
) -> None:
    """Atualiza article-id (scielo-v2 e scielo-v3) dos documentos recebidos.

    Params:
        pid_manager (PIDVersionsManager): instância de PIDVersionsManager para gerir pid da versão 3
        issn_id (str): ISSN do periódico
        year_and_order (str): Ano e ordem da issue processada
        received_docs (dict): Pacote de documentos recebidos para processar
        documents_in_isis (dict): Documentos já registrados na base isis (acron/volnum)
        file_paths (dict): arquivos do received_docs
        update_article_with_aop_status (callable): Função que recupera o AOP PID e modifica o
            artigo com este dado

    Returns:
        None
    """

    for xml_name, article in received_docs.items():
        pid_v2 = article.get_scielo_pid("v2")
        pid_v3 = article.get_scielo_pid("v3")
        pids_to_append_in_xml = []
        # Compara o artigo com a base de artigos AOP
        # Caso a semelhança entre os artigos seja maior que 80%
        # O artigo recebe o PID de AOP, observável pela
        # propriedade `registered_aop_pid`
        update_article_with_aop_status(article)

        if pid_v2 and pid_v3:
            exists_in_database = pid_manager.pids_already_registered(pid_v2, pid_v3)

            if not exists_in_database:
                pid_manager.register(pid_v2, pid_v3)

            continue

        if pid_v2 is None:
            pid_v2 = get_scielo_pid_v2(issn_id, year_and_order, article.order)
            pids_to_append_in_xml.append((pid_v2, "scielo-v2"))

        if pid_v3 is None:
            pid_v3 = (
                pid_manager.get_pid_v3(article.registered_aop_pid)
                or pid_manager.get_pid_v3(pid_v2)
                or scielo_id_gen.generate_scielo_pid()
            )
            article.registered_scielo_id = pid_v3
            pids_to_append_in_xml.append((pid_v3, "scielo-v3"))

        try:
            pid_manager.register(pid_v2, pid_v3)
        except sqlite3.OperationalError:
            LOGGER.exception(
                "Could not update sql database with pid v2 and v3."
                " The following exception was captured."
            )

        file_path = file_paths.get(xml_name)
        if file_path is None:
            LOGGER.debug("Could not find XML path for '%s' xml.", xml_name)
            return None

        try:
            tree = xml_utils.get_xml_object(file_path)
        except xml_utils.etree.XMLSyntaxError:
            LOGGER.info("%s is not a valid XML", file_path)
        else:
            _tree = add_article_id_to_etree(tree, pids_to_append_in_xml)
            write_etree_to_file(_tree, file_path)


def update_xml_file(file_path, pids_to_append_in_xml):
    if not pids_to_append_in_xml:
        # nada para atualizar
        return None
    if not file_path:
        LOGGER.debug("Could not find XML path")
        return None
    try:
        tree = xml_utils.get_xml_object(file_path)
    except xml_utils.etree.XMLSyntaxError:
        LOGGER.info("%s is not a valid XML", file_path)
    else:
        # atualizar XML com os `pids_to_append_in_xml`
        _tree = add_article_id_to_etree(tree, pids_to_append_in_xml)
        write_etree_to_file(_tree, file_path)


def add_article_id_to_received_documents(
    pid_manager: PIDVersionsManager,
    issn_id: str,
    year_and_order: str,
    received_docs: dict,
    documents_in_isis: dict,
    file_paths: dict,
    update_article_with_aop_status: callable,
) -> None:
    """Atualiza article-id (scielo-v2 e scielo-v3) dos documentos recebidos.

    Params:
        pid_manager (PIDVersionsManager): instância de PIDVersionsManager para gerir pid da versão 3
        issn_id (str): ISSN do periódico
        year_and_order (str): Ano e ordem da issue processada
        received_docs (dict): Pacote de documentos recebidos para processar
        documents_in_isis (dict): Documentos já registrados na base isis (acron/volnum)
        file_paths (dict): arquivos do received_docs
        update_article_with_aop_status (callable): Função que recupera o AOP PID e modifica o
            artigo com este dado

    Returns:
        None
    """

    for xml_name, article in received_docs.items():
        file_path = file_paths.get(xml_name)
        if not file_path:
            LOGGER.debug("Could not find XML path for '%s' xml.", xml_name)

        pids_to_append_in_xml = []

        # Obtém v2 do XML
        pid_v2 = article.get_scielo_pid("v2")
        if pid_v2 is None:
            # se v2 não está presente no XML, gerar a partir dos metadados
            pid_v2 = get_scielo_pid_v2(issn_id, year_and_order, article.order)
            # anotar para ser inserido no XML
            pids_to_append_in_xml.append((pid_v2, "scielo-v2"))

        # Obtém v3 do XML
        pid_v3 = article.get_scielo_pid("v3")

        # Obtém previous do XML
        prev_pid = article.previous_article_pid
        if not prev_pid:
            # Não há previous do XML
            # Obtém previous_pid registrado na base ahead do artigo
            update_article_with_aop_status(article)
            # acessa previous_pid com `article.registered_aop_pid`
            prev_pid = article.registered_aop_pid
            if prev_pid:
                pids_to_append_in_xml.append((prev_pid, "previous-pid"))

        if pid_v3 is None:
            # se v3 não está no presente no XML, consulta no pid manager pelo
            # previous_pid ou pid_v2 ou gera pid v3

            pid_v3 = (
                pid_manager.get_most_recent_pid_v3(prev_pid, pid_v2) or
                scielo_id_gen.generate_scielo_pid()
            )

            article.registered_scielo_id = pid_v3
            # anotar para ser inserido no XML
            pids_to_append_in_xml.append((pid_v3, "scielo-v3"))

        # registra no pid_manager os pares (v2,v3) não registrados
        register_pids(pid_manager, pid_v3, prev_pid, pid_v2)

        # atualizar o XML com pids_to_append_in_xml
        update_xml_file(file_path, pids_to_append_in_xml)


def register_pids(pid_manager, pid_v3, prev_pid, pid_v2):
    for v2 in (prev_pid, pid_v2):
        if not v2:
            continue
        found_in_db = pid_manager.pids_already_registered(v2, pid_v3)
        if not found_in_db:
            try:
                pid_manager.register(v2, pid_v3)
            except Exception as e:
                LOGGER.info(
                    "Could not update sql database with (%s, %s)"
                    " The following exception was captured. %s" %
                    (v2, pid_v3, str(e))
                )


def get_scielo_pid_v2(issn_id, year_and_order, order_in_issue):
    year = year_and_order[:4]
    order_in_year = year_and_order[4:].zfill(4)
    return "".join(("S", issn_id, year, order_in_year, order_in_issue))


def add_article_id_to_etree(
    tree: etree.ElementTree, pid_and_specific_use_items: list
) -> Optional[etree.ElementTree]:
    """Adiciona os pids v2 e v3 a árvore lxml de um documento"""
    if (
        tree is None
        or pid_and_specific_use_items is None
        or len(pid_and_specific_use_items) == 0
    ):
        return None

    _tree = copy.deepcopy(tree)

    article_meta = _tree.find(".//article-meta")

    if article_meta is None:
        LOGGER.debug(
            "Could not insert articles ids because the article-meta isn't found"
        )
        return None

    for id_value, specific_use in pid_and_specific_use_items:
        article_id = etree.Element("article-id")
        article_id.text = id_value
        article_id.set("specific-use", specific_use)
        article_id.set("pub-id-type", "publisher-id")
        article_meta.insert(0, article_id)

    return _tree


def write_etree_to_file(tree: etree.ElementTree, path: str) -> None:
    """Escreve uma árvore lxml em um arquivo de destino. Também
    garante que as entidades não serão modificadas por meio da função
    xml_utils.tostring(etree)."""

    if tree is None or path is None:
        return None

    fs_utils.write_file(path, xml_utils.tostring(tree))
