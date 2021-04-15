# coding=utf-8

from prodtools.reports import validation_status
from prodtools.validations.article_data_reports import ArticlesComparison


ACTION_DELETE = 'delete'
ACTION_REJECT = 'reject'
ACTION_SOLVE_TITAUT_CONFLICTS = 'TITAUT_CONFLICTS'
ACTION_UPDATE = 'update'
ACTION_CHECK_ORDER_AND_NAME = 'CHECK_ORDER_AND_NAME'

HISTORY_REGISTERED = 'registered article'
HISTORY_PACKAGE = 'package'
HISTORY_DELETED = 'excluded article'
HISTORY_ACCEPTED = 'accepted'
HISTORY_SOLVED = 'solved'
HISTORY_REJECTED = 'rejected'

HISTORY_TITAUT_CONFLICTS = 'detected different titles/authors'
HISTORY_CHECK_ORDER_AND_NAME = 'need to check order and/or name'
HISTORY_PKG_ORDER_CONFLICTS = 'detected order conflict in package'
HISTORY_CREATED = 'created'
HISTORY_ORDER_AND_NAME_CONFLICTS = 'order and name conflicts'
HISTORY_ORDER_CHANGED = 'order changed'
HISTORY_UNMATCHED = 'unmatched data'
HISTORY_REPLACE = 'replace'
HISTORY_NAME_CHANGED = 'name changed'
HISTORY_REPLACED_BY = 'replaced by'


class GroupedDocuments(object):
    """
    Representa o grupo de documentos após a junção dos documentos registrados +
    documentos do pacote.
    Tem como propósito computar os dados para serem gerados os relatórios de
    coerência entre os documentos (GroupCoherenceReports), ou seja, verificar
    se os dados esperados como únicos, como IDs, são únicos, se os dados em
    comum como título do periódicos são iguais entre todos os documentos entre
    outras verificações no contexto do grupo.
    """
    def __init__(self, grouped_docs: dict, is_db_generation: bool):
        """
        grouped_docs.keys: nome base dos arquivos sem extensão
        grouped_docs.values: article.Article
        """
        self.grouped_docs = grouped_docs

        self.ERROR_LEVEL_FOR_UNIQUE_VALUES = {
            'order': validation_status.STATUS_BLOCKING_ERROR,
            'doi': validation_status.STATUS_FATAL_ERROR,
            'elocation id': validation_status.STATUS_BLOCKING_ERROR,
            'fpage-lpage-seq-elocation-id': validation_status.STATUS_ERROR,
        }
        if not is_db_generation:
            self.ERROR_LEVEL_FOR_UNIQUE_VALUES['order'] = validation_status.STATUS_WARNING
        self.IGNORE_NONE = ['journal-id (nlm-ta)', 'e-ISSN', 'print ISSN', ]
        self.EXPECTED_COMMON_VALUES_LABELS = ['journal-title', 'journal-id (nlm-ta)', 'e-ISSN', 'print ISSN', 'issue label', 'issue pub date', 'license']
        self.REQUIRED_DATA = ['journal-title', 'journal ISSN', 'publisher name', 'issue label', 'issue pub date', ]
        self.EXPECTED_UNIQUE_VALUE_LABELS = ['order', 'doi', 'elocation id', 'fpage-lpage-seq-elocation-id']

    @property
    def articles(self):
        l = sorted([(article.order, xml_name) for xml_name, article in self.grouped_docs.items()])
        l = [(xml_name, self.grouped_docs[xml_name]) for order, xml_name in l]
        return l

    @property
    def is_aop_issue(self):
        return any([a.is_ahead for a in self.grouped_docs.values()])

    @property
    def is_rolling_pass(self):
        return all([a for a in self.grouped_docs.values() if a.is_rolling_pass])

    @property
    def common_data(self):
        data = {}
        for label in self.EXPECTED_COMMON_VALUES_LABELS:
            values = {}
            for xml_name, article in self.grouped_docs.items():
                value = article.summary[label]
                if label in self.IGNORE_NONE and value is None:
                    pass
                else:
                    if value not in values:
                        values[value] = []
                    values[value].append(xml_name)

            data[label] = values
        return data

    @property
    def missing_required_data(self):
        required_items = {}
        for label in self.REQUIRED_DATA:
            if label in self.common_data.keys():
                if None in self.common_data[label].keys():
                    required_items[label] = self.common_data[label][None]
        return required_items

    @property
    def conflicting_values(self):
        data = {}
        for label, values in self.common_data.items():
            if len(values) > 1:
                data[label] = values
        return data

    @property
    def duplicated_values(self):
        duplicated_labels = {}
        for label, values in self.unique_values.items():
            if len(values) > 0 and len(values) != len(self.articles):
                duplicated = {value: xml_files for value, xml_files in values.items() if len(xml_files) > 1}
                if len(duplicated) > 0:
                    duplicated_labels[label] = duplicated
        return duplicated_labels

    @property
    def unique_values(self):
        data = {}
        for label in self.EXPECTED_UNIQUE_VALUE_LABELS:
            values = {}
            for xml_name, article in self.grouped_docs.items():
                value = article.summary[label]
                if value is not None:
                    if value not in values:
                        values[value] = []
                    values[value].append(xml_name)

            data[label] = values
        return data


class DocumentsMerger(object):
    """
    Avalia cada documento do pacote se pode ou não ser incluído no sistema.
    Mescla os documentos registrados com os documentos do pacote, se permitido.
    """
    def __init__(self, registered_articles, articles, is_db_generation):
        self.is_db_generation = is_db_generation
        self.registered_articles = registered_articles
        self.articles = articles
        self.titaut_conflicts = {}
        self.name_order_conflicts = {}
        self.name_changes = {}
        self.order_changes = {}
        self.excluded_items = {}
        self.excluded_orders = []
        self.accepted_articles = {}
        self.rejected_articles = []
        self.history_items = {}
        self.merged_articles = {}
        self.merge_articles()

    def get_similar_registered_docs(self, article):
        similar_items = {}
        for name, registered in self.registered_articles.items():
            comparison = ArticlesComparison(registered, article)
            if comparison.are_similar:
                similar_items.update({name: registered})
        return similar_items

    @property
    def pkg_articles_by_order_and_name(self):
        return {a.order + name: name for name, a in self.articles.items()}

    @property
    def registered_articles_by_order_and_name(self):
        if self.is_db_generation:
            return {a.order + name: name for name, a in self.registered_articles.items()}
        return {}

    @property
    def registered_articles_by_order(self):
        if self.is_db_generation:
            return {a.order: name for name, a in self.registered_articles.items()}
        return {}

    @property
    def pkg_order_conflicts(self):
        # pkg order conflicts
        if self.is_db_generation:
            pkg_orders = {a.order: [] for name, a in self.articles.items() if a.marked_to_delete is False}
            for name, a in self.articles.items():
                if not a.marked_to_delete:
                    pkg_orders[a.order].append(name)
            return {order: names for order, names in pkg_orders.items() if len(names) > 1}
        return {}

    def _update_history(self, names, status):
        for name in names or []:
            if name not in self.history_items.keys():
                self.history_items[name] = []
            self.history_items[name].append(status)

    def _delete_articles(self, names):
        for name in names or []:
            del self.merged_articles[name]
            self.history_items[name].append(HISTORY_DELETED)

    def _update_articles(self, names):
        for name in names or []:
            self.history_items[name].append(HISTORY_ACCEPTED)
            self.accepted_articles[name] = self.articles.get(name)
            self.merged_articles[name] = self.articles.get(name)

    def _reject_or_resolve_title_and_authors_conflicts(self, names):
        conflicts = self._resolve_title_and_authors_conflicts(names)
        for name in names or []:
            self.history_items[name].append(HISTORY_TITAUT_CONFLICTS)
            if conflicts[name]:
                self.titaut_conflicts[name] = conflicts[name]
                self.history_items[name].append(HISTORY_REJECTED)
            else:
                self.history_items[name].append(HISTORY_SOLVED)
                self.accepted_articles[name] = self.articles.get(name)
                self.merged_articles[name] = self.articles.get(name)

    def _resolve_order_and_name_issues(
            self, names_to_check_name_and_order, names_to_delete):
        names_to_check_name_and_order = names_to_check_name_and_order or []
        names_to_delete = names_to_delete or []

        # need to check name/order
        for name in names_to_check_name_and_order:
            self.history_items[name].append(HISTORY_CHECK_ORDER_AND_NAME)

        # solve name/order
        solved = self._evaluate_check_order_and_name(
            names_to_check_name_and_order, names_to_delete)
        for name in solved:
            self.merged_articles[name] = self.articles[name]
            self.history_items[name].append(HISTORY_SOLVED)
            self.accepted_articles[name] = self.articles.get(name)

        # delete name changed
        for name in self.name_changes.values():
            del self.merged_articles[name]

        for name in names_to_delete:
            self.excluded_items[name] = self.articles[name].order
            self.excluded_orders.append(self.articles[name].order)
        self.excluded_orders.extend(
            [previous for previous, current in self.order_changes.values()])

    def merge_articles(self):
        # registered
        self._update_history(
            self.registered_articles.keys(), HISTORY_REGISTERED)
        # package
        self._update_history(self.articles.keys(), HISTORY_PACKAGE)
        # analyze package
        tasks = self._analyze_what_to_do_with_the_package_articles()
        #
        self.merged_articles = self.registered_articles.copy()
        # reject
        self.rejected_articles = tasks.get(ACTION_REJECT)
        self._update_history(tasks.get(ACTION_REJECT), HISTORY_REJECTED)
        # delete
        self._delete_articles(tasks.get(ACTION_DELETE))
        # update
        self._update_articles(tasks.get(ACTION_UPDATE))
        # reject or try to solve conflicts
        self._reject_or_resolve_title_and_authors_conflicts(
            tasks.get(ACTION_SOLVE_TITAUT_CONFLICTS))

        self._resolve_order_and_name_issues(
            tasks.get(ACTION_CHECK_ORDER_AND_NAME), tasks.get(ACTION_DELETE))

    def _analyze_what_to_do_with_the_package_articles(self):
        tasks = {}
        for k, a_name in self.pkg_articles_by_order_and_name.items():
            registered_name = self.registered_articles_by_order_and_name.get(k)
            task_id = self._get_task_id(registered_name)
            if task_id not in tasks.keys():
                tasks[task_id] = []
            tasks[task_id].append(a_name)
        return tasks

    def _get_task_id(self, registered_name):
        if not registered_name:
            return ACTION_CHECK_ORDER_AND_NAME

        registered_doc = self.registered_articles[registered_name]
        package_doc = self.articles[registered_name]

        # nao funciona usar:
        # if package_doc.is_ahead and not registered_doc.is_ahead
        # `is_ahead` é um atributo computado baseado no volume e número
        # enquanto `is_ex_aop` é retornado se o registro foi encontrado
        # na base `ex-*nahead`
        if package_doc.is_ahead and registered_doc.is_ex_aop:
            return ACTION_REJECT

        article_comparison = ArticlesComparison(
            registered_doc, package_doc)
        if not article_comparison.are_similar:
            task_id = ACTION_SOLVE_TITAUT_CONFLICTS
        elif package_doc.marked_to_delete:
            task_id = ACTION_DELETE
        else:
            task_id = ACTION_UPDATE
        return task_id

    def _resolve_title_and_authors_conflicts(self, names):
        """
        Compara cada documento da lista de `names` como todos os documentos
        registrados
        """
        conflicts = {}
        for name in names or []:
            similars = self.get_similar_registered_docs(
                self.articles.get(name))
            if len(similars) == 0:
                # nenhum registrado na base é similar ao documento do pacote
                conflicts[name] = None
            elif len(similars) == 1 and name in similars.keys():
                conflicts[name] = None
            else:
                conflicts[name] = similars
        return conflicts

    def _evaluate_check_order_and_name(self, names, deleted):
        solved = []
        self.name_order_conflicts = {}
        self.order_changes = {}
        self.name_changes = {}
        if names is not None:
            for name in names:
                order = self.articles.get(name).order
                if order in self.pkg_order_conflicts.keys():
                    # order conflicts; duplicity of order in pkg
                    self.name_order_conflicts[name] = {_name: self.articles.get(_name) for _name in self.pkg_order_conflicts[order] if name != _name}
                    self.history_items[name].append(HISTORY_PKG_ORDER_CONFLICTS)
                else:
                    # valid order
                    found = [registered_name for registered_name, a in self.registered_articles.items() if a.order == order]
                    found_by_order = found[0] if len(found) == 1 else None
                    found_by_name = name if self.registered_articles.get(name) is not None else None
                    if found_by_name in deleted:
                        found_by_name = None
                    if found_by_order in deleted:
                        found_by_order = None
                    if found_by_name is None and found_by_order is None:
                        solved.append(name)
                        self.history_items[name].append(HISTORY_CREATED)
                    elif all([found_by_name, found_by_order]):
                        # found both in different records
                        self.name_order_conflicts[name] = {found_by_name: self.registered_articles.get(found_by_name), found_by_order: self.registered_articles.get(found_by_order)}
                        self.history_items[name].append(HISTORY_ORDER_AND_NAME_CONFLICTS)
                    elif found_by_name is not None:
                        # order not found
                        if self.are_similar(found_by_name, name, False, True):
                            # order changed
                            solved.append(name)
                            self.order_changes[name] = (self.registered_articles.get(name).order, order)
                            self.history_items[name].append(HISTORY_ORDER_CHANGED)
                        else:
                            # only name is identical
                            self.name_order_conflicts[name] = {found_by_name: self.registered_articles.get(found_by_name)}
                            self.history_items[name].append(HISTORY_UNMATCHED)
                    elif found_by_order is not None:
                        # name not found
                        if self.are_similar(found_by_order, name, True, False):
                            # name changed
                            solved.append(name)
                            self.name_changes[name] = found_by_order
                            self.history_items[name].append(HISTORY_NAME_CHANGED)
                            self.history_items[name].append(HISTORY_REPLACE + ' ' + found_by_order)
                            self.history_items[found_by_order].append(HISTORY_REPLACED_BY + ' ' + name)
                        else:
                            # only order is identical
                            self.name_order_conflicts[name] = {found_by_order: self.registered_articles.get(found_by_order)}
                            self.history_items[name].append(HISTORY_UNMATCHED)
        return solved

    def are_similar(self, registered_name, pkg_name, ign_name, ign_order):
        article_comparison = ArticlesComparison(
                self.registered_articles.get(registered_name),
                self.articles.get(pkg_name),
                ign_name,
                ign_order)
        return article_comparison.are_similar
