# coding=utf-8

from datetime import datetime

from __init__ import _
import article_utils


SPS_MIN_DATE = datetime(2012, 06, 01)
SPS_MIN_DATEISO = 20120601

SPS_versions_expiration_dates = {'sps-1.3': '20160901',
                'sps-1.2': '20160301',
                'sps-1.1': '20150901',
                'sps-1.0': '20150301',
                'pre-sps': '20140901',
}

# pre-sps: 2012-06 a 2014-09
# sps-1.0: 2014-03 a 2015-03
# sps-1.1: 2014-09 a 2015-09
# sps-1.2: 2015-03 a 2016-03
# sps-1.3: 2015-09 a 2016-09


SPS_expiration_dates_versions = {v: k for k, v in SPS_versions_expiration_dates.items()}

REFTYPE_AND_TAG_ITEMS = {'aff': ['aff'], 'app': ['app'], 'author-notes': ['fn'], 'bibr': ['ref'], 'boxed-text': ['boxed-text'], 'contrib': ['fn'], 'corresp': ['corresp'], 'disp-formula': ['disp-formula'], 
            'fig': ['fig', 'fig-group'], 
            'fn': ['fn'], 'list': ['list'], 'other': ['?'], 'supplementary-material': ['supplementary-material'], 
            'table': ['table-wrap', 'table-wrap-group']
            }

DOCTOPIC = {
                'research-article': 'oa',
                'editorial': 'ed',
                'abstract': 'ab',
                'announcement': 'zz',
                'article-commentary': 'co',
                'case-report': 'cr',
                'letter': 'le',
                'review-article': 'ra',
                'rapid-communication': 'sc',
                'addendum': 'zz',
                'book-review': 'rc',
                'books-received': 'zz',
                'brief-report': 'rn',
                'calendar': 'zz',
                'clinical-trial': 'ct',
                'collection': 'zz',
                'correction': 'er',
                'discussion': 'em',
                'dissertation': 'em',
                'editorial-material': 'em',
                'in-brief': 'pr',
                'introduction': 'em',
                'meeting-report': 'zz',
                'news': 'zz',
                'obituary': 'zz',
                'oration': 'zz',
                'partial-retraction': 're',
                'product-review': 'rc',
                'reply': 'zz',
                'reprint': 'zz',
                'retraction': 're',
                'translation': 'zz',
                'other': 'zz',
}

DOCTOPIC_IN_USE = [
    'article-commentary', 
    'book-review', 
    'brief-report', 
    'case-report', 
    'clinical-trial', 
    'correction', 
    'editorial', 
    'editorial-material', 
    'in-brief', 
    'letter', 
    'other', 
    'rapid-communication', 
    'research-article', 
    'retraction', 
    'review-article', 
    'technical-report', 
    ]

AUTHORS_REQUIRED_FOR_DOCTOPIC = [
    'article-commentary', 
    'book-review', 
    'brief-report', 
    'case-report', 
    'editorial', 
    'letter', 
    'rapid-communication', 
    'research-article', 
    'retraction', 
    'reply', 
    'review-article', 
    ]

ABSTRACT_REQUIRED_FOR_DOCTOPIC = [
    'article-commentary', 
    'brief-report', 
    'case-report', 
    'clinical-trial', 
    'rapid-communication', 
    'research-article', 
    'review-article', 
    'technical-report', 
    ]

REFS_REQUIRED_FOR_DOCTOPIC = [
    'article-commentary', 
    'brief-report', 
    'case-report', 
    'clinical-trial', 
    'rapid-communication', 
    'research-article', 
    'review-article', 
    'technical-report', 
    ]

TOC_SECTIONS = { 
    u'carta': u'letter', 
    u'revisão': u'review', 
    u'resenha': u'review', 
    u'reseña': u'review', 
    u'origin': u'research', 
    u'informe': u'report', 
    u'revisión': u'review', 
    u'relato': u'report', 
    u'artigo': u'article', 
    u'artículo': u'article', 
    u'errata': u'correction', 
    u'erratum': u'correction'
}


ROLE = {
    'author': 'ND',
    'editor': 'ED',
    'assignee': 'assignee',
    'compiler': 'compiler',
    'director': 'director',
    'guest-editor': 'guest-editor',
    'inventor': 'inventor',
    'transed': 'transed',
    'translator': 'TR',    
}


BIBLIOMETRICS_USE = ['journal', 'book', 'thesis', 'confproc']

scholars_level1 = ['journal', 'book']
scholars_level2 = ['thesis', 'confproc']

PUBLICATION_TYPE = []
PUBLICATION_TYPE.append('journal')
PUBLICATION_TYPE.append('book')
PUBLICATION_TYPE.append('thesis')
PUBLICATION_TYPE.append('patent')
PUBLICATION_TYPE.append('report')
PUBLICATION_TYPE.append('software')
PUBLICATION_TYPE.append('webpage')
PUBLICATION_TYPE.append('database')
PUBLICATION_TYPE.append('confproc')
PUBLICATION_TYPE.append('legal-doc')
PUBLICATION_TYPE.append('newspaper')
PUBLICATION_TYPE.append('other')


REFERENCE_REQUIRED_SUBELEMENTS = {}
REFERENCE_REQUIRED_SUBELEMENTS['journal'] = ['article-title', 'person-group', 'year', 'source']
REFERENCE_REQUIRED_SUBELEMENTS['book'] = ['year', 'source']
REFERENCE_REQUIRED_SUBELEMENTS['confproc'] = ['conf-name', 'source', 'year']
REFERENCE_REQUIRED_SUBELEMENTS['thesis'] = ['comment', 'source', 'year']
REFERENCE_REQUIRED_SUBELEMENTS['webpage'] = ['ext-link', 'date-in-citation[@content-type="access-date"]', 'source']


REFERENCE_NOT_ALLOWED_SUBELEMENTS = {}
REFERENCE_NOT_ALLOWED_SUBELEMENTS['journal'] = ['chapter-title', 'conf-date', 'conf-loc', 'conf-name', 'conf-num', 'conf-sponsor', 'conf-theme', 'conference', 'patent']
REFERENCE_NOT_ALLOWED_SUBELEMENTS['book'] = ['article-title', 'conf-date', 'conf-loc', 'conf-name', 'conf-num', 'conf-sponsor', 'conf-theme', 'conference', 'patent']
REFERENCE_NOT_ALLOWED_SUBELEMENTS['thesis'] = ['article-title', 'conf-date', 'conf-loc', 'conf-name', 'conf-num', 'conf-sponsor', 'conf-theme', 'conference', 'patent']
REFERENCE_NOT_ALLOWED_SUBELEMENTS['webpage'] = ['article-title', 'chapter-title']
REFERENCE_NOT_ALLOWED_SUBELEMENTS['confproc'] = ['chapter-title', 'patent']

LANGUAGES = {
    'en': _('English'),
    'pt': _('Portuguese'),
    'es': _('Spanish'),
    'af': _('Afrikaans'),
    'ar': _('Arabic'),
    'bg': _('Bulgarian'),
    'zh': _('Chinese'),
    'cs': _('Czech'),
    'da': _('Danish'),
    'nl': _('Dutch'),
    'eo': _('Esperanto'),
    'fr': _('French'),
    'de': _('German'),
    'gr': _('Greek'),
    'he': _('Hebrew'),
    'hi': _('Hindi'),
    'hu': _('Hungarian'),
    'in': _('Indonesian'),
    'ia': _('Interlingua'),
    'ie': _('Interlingue'),
    'it': _('Italian'),
    'ja': _('Japanese'),
    'ko': _('Korean'),
    'la': _('Latin'),
    'no': _('Norwergian'),
    'pl': _('Polish'),
    'ro': _('Romanian'),
    'ru': _('Russian'),
    'sa': _('Sanskrit'),
    'sh': _('Serbo-Croat'),
    'sk': _('Slovak'),
    'sn': _('Slovenian'),
    'sv': _('Swedish'),
    'tr': _('Turkish'),
    'uk': _('Ukrainian'),
    'ur': _('Urdu'),
    'zz': _('Other'),
    'gl': _('Galician'),
    'eu': _('Basque'),
    'ca': _('Catalan'),
}


def is_required(publication_type, label):
    return label in REFERENCE_REQUIRED_SUBELEMENTS.get(publication_type, [])


def is_allowed_element(publication_type, label):
    if is_required(publication_type, label):
        r = True
    else:
        r = not label in REFERENCE_NOT_ALLOWED_SUBELEMENTS.get(publication_type, [])
    return r


def validate_element(publication_type, label, value):
    problem = ''
    compl = ''
    items = []
    if value is None or value == '':
        if is_required(publication_type, label):
            problem = '@publication-type="' + publication_type + '" ' + _('requires') + ' ' + label
            items = ['@publication-type', _('the elements of this reference')]
            compl = '. ' + _('If the reference has no ') + label + ', ' + _('ignore this message')
    else:
        if not is_allowed_element(publication_type, label):
            problem = label + _(' is not allowed for ') + '@publication-type=' + publication_type
            items = ['@publication-type', label, value]
    if len(problem) > 0:
        problem += _('. Be sure that you have correctly identified: ') + _(' or ').join(items)
        problem += compl
    return problem


def doctopic_label(code):
    label = [k for k, v in DOCTOPIC.items() if v == code]
    if len(label) == 0:
        label = None
    else:
        label = label[0]
    return label


def normalize_section_title(text):
    if text is None:
        text = ''

    text = text.lower().replace('-', ' ')
    text = text.replace('update article', 'rapid communication')
    text = text.replace(u'artículo de actualización', 'rapid communication')
    text = text.replace(u'artigo de atualização', 'rapid communication')
    text = text.replace(u'comunicação breve', 'rapid communication')
    text = text.replace(u'comunicación breve', 'rapid communication')
    text = text.replace(u'nota técnica', 'brief report')
    text = text.replace(u'nota de pesquisa', 'brief report')
    text = text.replace(u'nota de investigación', 'brief report')
    text = text.replace(u'research note', 'brief report')
    text = text.replace(u'relato breve', 'brief report')
    text = text.replace(u'informe breve', 'brief report')

    text = ' '.join([item for item in text.split(' ') if len(item) > 2])

    text = ' '.join([item for item in sorted(text.split(' '))])
    if text is not None:
        for term, transl in TOC_SECTIONS.items():
            text = text.replace(term, transl)
    return text


def check_lang(lang):
    if lang in LANGUAGES.keys():
        return (True, LANGUAGES.get(lang))
    else:
        return (False, lang + ': ' + _('Invalid value for ') + '@xml:lang. ' + _('Expected values') + ': ' + ', '.join(sorted(LANGUAGES.keys())) + '. ' + '|'.join(sorted([k + '(' + v + ')' for k, v in LANGUAGES.items()])))


def expected_sps_versions(article_dateiso):
    sps_dateiso_items = sorted(SPS_expiration_dates_versions.keys())
    sps_datetime_items = [article_utils.dateiso2datetime(item) for item in sps_dateiso_items]
    article_datetime = article_utils.dateiso2datetime(article_dateiso)
    min_version = str(None)
    max_version = SPS_expiration_dates_versions.get(sps_dateiso_items[len(sps_dateiso_items)-1])
    valid_versions = [min_version, max_version]

    if article_datetime is not None:
        diff = SPS_MIN_DATE - article_datetime
        if diff.days > 0:
            # data do artigo é antiga, anterior a 2012
            # permitido qualquer versão
            valid_versions = [item for item in SPS_expiration_dates_versions.values() if item != 'pre-sps']
        else:
            i = 0
            k = 0
            for sps_datetime in sps_datetime_items:
                diff = article_datetime - sps_datetime
                if diff.days < 0:
                    valid_versions = []
                    for k in range(i, len(sps_dateiso_items)):
                        valid_versions.append(SPS_expiration_dates_versions.get(sps_dateiso_items[k]))
                    break
                i += 1
    return list(set(sorted(valid_versions)))


def sps_current_versions():
    sps_dateiso_items = sorted(SPS_expiration_dates_versions.keys())
    sps_dateiso_items.reverse()
    currents = []
    for item in sps_dateiso_items[:2]:
        currents.append(SPS_expiration_dates_versions.get(item))
    return list(set(sorted(currents)))


def sps_version_expiration_days(sps_version):
    days = None
    if sps_version is None:
        sps_version = 'pre-sps'
    sps_version_datetime = SPS_versions_expiration_dates.get(sps_version)
    if sps_version_datetime is not None:
        sps_version_datetime = article_utils.dateiso2datetime(sps_version_datetime)
        now = datetime.now()
        diff = sps_version_datetime - now
        days = diff.days
    return days
