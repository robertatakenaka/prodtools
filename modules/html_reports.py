# coding=utf-8

import os
import shutil

from datetime import datetime

from __init__ import _
from . import validation_status
from . import xml_utils
from . import utils


ENABLE_COMMENTS = False
CURRENT_PATH = os.path.dirname(os.path.realpath(__file__)).replace('\\', '/')


class TabbedReport(object):

    def __init__(self, labels, tabs, tabbed_content, pre_selected, footnote='', style_selected='selected-tab-content', style_not_selected='not-selected-tab-content'):
        self.labels = labels
        self.tabs = tabs
        self.tabbed_content = tabbed_content
        self.style_selected = style_selected
        self.style_not_selected = style_not_selected
        self.pre_selected = pre_selected
        self.footnote = footnote
        self.display_report = display_report

    def save_report(self, report_path, report_filename, report_title, _display_report):
        filename = report_path + '/' + report_filename
        if os.path.isfile(filename):
            bkp_filename = report_path + '/' + report_filename + '-'.join(utils.now()) + '.html'
            shutil.copyfile(filename, bkp_filename)

        save(filename, report_title, self.report_content)
        print(_('Report:\n  {filename}').format(filename=filename))
        if _display_report:
            display_report(filename)

    @property
    def report_content(self):
        # tabs
        content = tabs_items([(tab_id, self.labels[tab_id]) for tab_id in self.tabs if self.tabbed_content.get(tab_id) is not None], self.pre_selected)
        # tabs content
        for tab_id in self.tabs:
            c = self.tabbed_content.get(tab_id)
            if c is not None:
                style = self.style_selected if tab_id == self.pre_selected else self.style_not_selected
                content += tab_block(tab_id, c, style)

        return content + self.footnote


class HideAndShowBlocksReport(object):

    def __init__(self, labels, values, hide_and_show_blocks, html_cell_content=[]):
        self.labels = labels
        self.values = values
        self.hide_and_show_blocks = hide_and_show_blocks
        self.html_cell_content = html_cell_content
        self.html_cell_content.append(labels[-1])

    @property
    def content(self):
        items = []
        for new_name, data in self.values.items():
            data.append(self.hide_and_show_blocks[new_name].links)
            items.append(label_values(self.labels, data))
            items.append({self.labels[-1]: self.hide_and_show_blocks[new_name].block})
        return sheet(self.labels, items, table_style='reports-sheet', html_cell_content=self.html_cell_content)


class HideAndShowBlockItem(object):

    def __init__(self, block_parent_id, label, block_id, block_style, block_content, status=''):
        self.block_parent_id = block_parent_id
        self.block_id = block_id
        self.label = label
        self.block_content = block_content
        self.status = status
        self.block_style = block_style

    @property
    def link(self):
        _link = block_link(self.block_id, self.label, self.block_style, self.block_parent_id)
        if self.status != '':
            _link += tag('span', self.status, 'smaller')
        return _link

    @property
    def block(self):
        return block_element(self.block_id, self.block_content, self.block_style, self.block_parent_id)


class HideAndShowBlock(object):

    def __init__(self, block_parent_id, block_items):
        self.links = '<a name="' + block_parent_id + '"/>'
        self.block = ''
        for item in block_items:
            self.links += item.link
            self.block += item.block


def report_date():
    procdate = datetime.now().isoformat()
    return tag('p', procdate[0:10] + ' ' + procdate[11:19], 'report-date')


def statistics(content, word):
    return len(content.split(word)) - 1


def statistics_numbers(content):
    e = statistics(content, validation_status.STATUS_ERROR)
    f = statistics(content, validation_status.STATUS_FATAL_ERROR)
    w = statistics(content, validation_status.STATUS_WARNING)
    return (f, e, w)


def get_unicode(text):
    if text is None:
        text = u''
    if not isinstance(text, unicode):
        try:
            text = text.decode('utf-8')
        except Exception as e:
            try:
                text = text.decode('utf-8', 'xmlcharrefreplace')
            except Exception as e:
                print(e)
                print(text)
                #text = u''
    return text


def join_texts(texts):
    text = u''.join([get_unicode(t) for t in texts])
    return text


def styles():
    css_file = CURRENT_PATH + '/html_reports.css'
    css = '<style>' + open(css_file, 'r').read() + '</style>'
    js = open(CURRENT_PATH + '/html_reports_collapsible.js', 'r').read()
    return css + js + save_report_js()


def body_section(style, anchor_name, title, content, sections=[]):
    anchor = anchor_name if anchor_name == '' else '<a name="' + anchor_name + '"/><a href="#top">^</a>'
    sections = '<ul class="sections">' + ''.join(['<li> [<a href="#' + s + '">' + t + '</a>] </li>' for s, t, d in sections]) + '</ul>'
    return anchor + '<' + style + '>' + title + '</' + style + '>' + sections + content


def attr(name, value):
    return ' ' + name + '="' + value + '"' if value is not None and name is not None else ''


def collapsible_block(section_id, section_title, content, status='ok'):
    r = '<a name="begin_' + section_id + '"/><div id="show' + section_id + '" onClick="openClose(\'' + section_id + '\')" class="collapsiblehidden" style="cursor:hand; cursor:pointer">' + section_title + ' <span class="button">[+]</span></div>'
    r += '<div id="hide' + section_id + '" onClick="openClose(\'' + section_id + '\')" class="collapsibleopen" style="cursor:hand; cursor:pointer">' + section_title + '<span class="button">[-]</span></div>'
    r += '<div id="' + section_id + '" class="collapsibleopen">'
    r += '<div class="embedded-report-' + status + '">' + content + '</div>'
    r += '<div class="endreport">'
    r += '  <div>' + ' ~ '*10 + 'end of report ' + ' ~ '*10 + '</div>'
    r += '  <div onClick="openClose(\'' + section_id + '\')" style="cursor:hand; cursor:pointer"><span class="button"> [ close ] </span></div>'
    r += '</div>'
    r += '</div>'

    return r


def link(href, label):
    return '<a href="' + href + '" target="_blank">' + label + '</a>'


def tag(tag_name, content, style=None, attributes={}):
    if content is None:
        content = ''
    if tag_name == 'p' and '</p>' in content:
        tag_name = 'div'
    style = attr('class', style) if style is not None else ''
    return '<' + tag_name + style + ' '.join([attr(name, val) for name, val in attributes.items()]) + '>' + content + '</' + tag_name + '>'


def html(title, body):
    s = ''
    s += '<html>'
    s += '<head>'
    if title is None:
        title = ''
    if body is None:
        body = ''
    if isinstance(title, list):
        s += '<meta charset="utf-8"/><title>' + ' - '.join(title) + '</title>'
    else:
        s += '<meta charset="utf-8"/><title>' + title + '</title>'
    s += styles()
    s += '</head>'
    s += '<body>'
    s += report_date()
    if isinstance(title, list):
        s += tag('h1', title[0])
        s += tag('h1', title[1])
    else:
        s += tag('h1', title)
    s += body
    s += '</body>'
    s += '</html>'

    return s


def statistics_display(validations_results, inline=True):
    if inline:
        tag_name = 'span'
        stats = ' | '.join([k + ': ' + v for k, v in [('fatal errors', str(validations_results.fatal_errors)), ('errors', str(validations_results.errors)), ('warnings', str(validations_results.warnings))]])
    else:
        tag_name = 'div'
        stats = [('Total of fatal errors', validations_results.fatal_errors), ('Total of errors', validations_results.errors), ('Total of warnings', validations_results.warnings)]
        stats = ''.join([tag('p', display_label_value(l, str(v))) for l, v in stats])
    return tag(tag_name, stats, get_stats_numbers_style(validations_results.fatal_errors, validations_results.errors, validations_results.warnings))


def sheet(table_header, table_data, table_style='sheet', row_style=None, colums_styles={}, html_cell_content=[], default_width=None):
    if ENABLE_COMMENTS is True:
        html_cell_content.append(_('why it is not a valid message?'))
    else:
        if _('why it is not a valid message?') in table_header:
            table_header = [item for item in table_header if item != _('why it is not a valid message?')]
    r = ''
    try:
        r = sheet_build(table_header, table_data, table_style, row_style, colums_styles, html_cell_content, default_width)
    except Exception as e:
        print(e)
        print(table_header)
        print(table_data)
        raise
    return r


def old_sheet_build(table_header, table_data, table_style='sheet', row_style=None, colums_styles={}, html_cell_content=[], default_width=None):
    r = ''
    if not table_header is None:
        width = 70 if len(table_header) > 4 else int(float(140) / len(table_header))
        if default_width is not None:
            width = default_width
        th = ''.join([tag('th', label, 'th') for label in table_header])
        if len(table_data) == 0:
            tr_items = [tag('tr', ''.join(['<td>-</td>' for label in table_header]))]
        else:
            tr_items = []
            for row in table_data:
                td_items = []
                if len(row) == 1 and len(table_header) > 1:
                    # hidden tr
                    td_items.append('<td colspan="' + str(len(table_header)) + '" class="' + label + '-hidden-block">' + row.get(label, '') + '</td>')
                elif len(table_header) <= len(row):
                    for label in table_header:
                        td_content = row.get(label, '')
                        td_style = None
                        if label == _('why it is not a valid message?'):
                            if 'ERROR' in row.get('status', '') or 'WARNING' in row.get('status', ''):
                                td_content = '<textarea rows="5" cols="40"> </textarea>'
                            else:
                                td_content = ' - '
                        else:
                            # cell style
                            td_style = colums_styles.get(label)
                            if td_style is None:
                                if label in ['label', 'message', 'status', 'xml']:
                                    td_style = 'td_' + label
                            if td_style is None:
                                td_style = 'td_regular'
                            if not label in html_cell_content:
                                td_content = format_html_data(td_content, width)
                                if table_style == 'sheet':
                                    td_content = color_text(td_content)
                        td_items.append(tag('td', td_content, td_style))

                # row style
                tr_style = None
                if row_style is None:
                    if 'status' in table_header:
                        row_style = 'status'
                if row_style is not None:
                    tr_style = get_message_style(row.get(row_style))

                tr_items.append(tag('tr', ''.join(td_items), tr_style))
        r = tag('p', tag('table', tag('thead', tag('tr', th)) + tag('tbody', ''.join(tr_items)), table_style))
    return r


def sheet_column(data, _tag='td', style=None, width=None):
    _style = ''
    if style is not None:
        _style = ' class="' + style + '"'
    _width = ''
    if width is not None:
        _width = ' width="' + width + '%"'
    return '<' + _tag + _style + _width + '>' + data + '</' + _tag + '>'


def sheet_row(data, style=None):
    _style = ''
    if style is not None:
        _style = ' class="' + style + '"'
    return '<tr' + _style + '>' + data + '</tr>'


def sheet_row_style(table_header, row_style, row_content):
    tr_style = None
    if row_style is None:
        if 'status' in table_header:
            row_style = 'status'
    if row_style is not None:
        tr_style = get_message_style(row_content)
    return tr_style


def hidden_row(columns_number, label, data):
    return '<td colspan="' + columns_number + '" class="' + label + '-hidden-block">' + data + '</td>'


def sheet_col_style(label, colums_styles):
    style = colums_styles.get(label)
    if style is None:
        if label in ['label', 'message', 'status', 'xml']:
            style = 'td_' + label
    if style is None:
        style = 'td_regular'
    return style


def sheet_column_value(data, width, is_html_format, _color_text=False):
    value = data
    if not is_html_format:
        value = format_html_data(data, width)
        if _color_text:
            value = color_text(value)
    return value


def sheet_build(table_header, table_rows_data, table_style='sheet', style4row=None, columns_styles={}, html_cell_content=[], default_width=None):
    _color_text = (table_style == 'sheet')
    th = ''.join([tag('th', label, 'th') for label in table_header])
    if len(table_rows_data) == 0:
        table_rows_data = [{table_header[-1]: '-' for item in table_header}]
    width = str(50 if len(table_header) > 4 else int(float(140) / len(table_header)))
    rows = ''
    for row_data in table_rows_data:
        if len(row_data) == 1 and len(table_header) > 1:
            # hidden row
            columns = hidden_row(str(len(table_header)), table_header[-1], row_data.get(table_header[-1]))
        elif len(table_header) <= len(row_data):
            columns = ''
            for label in table_header:
                
                col_style = sheet_col_style(label, columns_styles)

                if label == _('why it is not a valid message?'):
                    if 'ERROR' in row_data.get('status', '') or 'WARNING' in row_data.get('status', ''):
                        col_value = '<textarea rows="5" cols="40"> </textarea>'
                    else:
                        col_value = ' - '
                else:
                    col_value = sheet_column_value(row_data.get(label), width, (label in html_cell_content), _color_text)
                columns += sheet_column(col_value, style=col_style, width=width)
        row_style = sheet_row_style(table_header, style4row, columns)
        rows += sheet_row(columns, row_style)
    return tag('p', tag('table', tag('thead', tag('tr', th)) + tag('tbody', rows), table_style))


def break_words(value, width=40):
    parts = []
    for line in value.split('\n'):
        left = line
        while len(left) > 0:
            part = left[0:width]
            parts.append(part)
            left = left[len(part):]

    value = '\n'.join(parts)
    return value


def display_xml(value, width=40):
    if '<' in value or '>' in value:
        value = xml_utils.format_text_as_xml(value)
    #value = break_words(value, width)
    value = value.replace('<', '&lt;')
    value = value.replace('>', '&gt;')
    value = value.replace('\t', '&nbsp;'*2)
    value = value.replace(' ', ' <font color="#F56991">&#183;</font> ').replace('\n', '<br/>')

    return '<code>' + value + '</code>'


def p_message(value, display_justification_input=True):
    style = get_message_style(value, '')
    justification_input = ''
    if display_justification_input is True and ENABLE_COMMENTS is True:
        if style in ['error', 'fatalerror', 'warning']:
            justification_input = tag('p', tag('textarea', ' ', attributes={'cols': '100', 'rows': '5'}))
    return tag('p', value, style) + justification_input


def color_text(value):
    return tag('span', value, get_message_style(value, 'ok'))


def format_list(label, list_type, list_items, style=''):
    if isinstance(list_items, dict):
        list_items = format_html_data_dict(list_items, list_type)
    elif isinstance(list_items, list):
        li_items = format_html_data_list(list_items, list_type)
    return tag('div', tag('p', label, 'label') + li_items, style)


def format_html_data_dict(value, list_type='ul'):
    r = ''
    if len(value) == 1:
        for k in sorted(value.keys()):
            v = value[k]
            r += display_label_value(k, v)
    else:
        r = '<' + list_type + '>'
        for k in sorted(value.keys()):
            v = value[k]
            r += tag('li', display_label_value(k, v))
        r += '</' + list_type + '>'
    return r


def format_html_data_list(value, list_type='ol'):
    r = '<' + list_type + '>'
    for v in value:
        r += tag('li', format_html_data(v))
    r += '</' + list_type + '>'
    return r


def format_html_data(value, width=70):
    r = '-'
    if isinstance(value, list):
        r = format_html_data_list(value)
    elif isinstance(value, dict):
        r = format_html_data_dict(value)
    elif value is None:
        # str or unicode
        r = '-'
    elif isinstance(value, int):
        r = str(value)
    elif '<OPTIONS/>' in value:
        msg, value = value.split('<OPTIONS/>')
        value = value.split('|')
        r = msg + '<select size="10">' + '\n'.join(['<option>' + op + '</option>' for op in sorted(value)]) + '</select>'
    elif '<img' in value or '</a>' in value:
        r = value
    #elif '<' in value and '>' in value and ('</' in value or '/>' in value):
    elif value.strip().startswith('<') and value.strip().endswith('>'):
        r = display_xml(value, width)
    elif '<' in value or '>' in value:
        r = value.replace('<', '&lt;').replace('>', '&gt;')
    else:
        r = value
    r = r.replace(' **', ' <strong>').replace('** ', '</strong> ')

    return r


def save(filename, title, body):
    r = html(title, body)
    if isinstance(r, unicode):
        r = r.encode('utf-8')
    open(filename, 'w').write(r)


def get_message_style(value, default=''):
    if value is None:
        value = ''
    if validation_status.STATUS_FATAL_ERROR in value:
        r = 'fatalerror'
    elif validation_status.STATUS_ERROR in value:
        r = 'error'
    elif validation_status.STATUS_WARNING in value:
        r = 'warning'
    elif validation_status.STATUS_OK in value:
        r = 'ok'
    elif validation_status.STATUS_INFO in value:
        r = 'info'
    elif validation_status.STATUS_VALID in value:
        r = 'valid'
    else:
        r = default
    return r


def get_stats_numbers_style(f, e, w):
    r = 'success'
    if f > 0:
        r = 'fatalerror'
    elif e > 0:
        r = 'error'
    elif w > 0:
        r = 'warning'
    return r


def display_labeled_value(label, value, style=''):
    if label is None:
        label = 'None'
    return tag('p', tag('span', '[' + label + '] ', 'discret') + format_html_data(value), style)


def display_label_value(label, value):
    return tag('span', label, 'label') + ': ' + format_html_data(value)


def thumb_image(path, width='auto', height='auto'):
    return link(path, image(path, width, height, style='thumb'))


def image(path, width='auto', height='auto', style='graphic'):
    dim = ''
    if width is not None:
        dim += ' width="' + width + '"'
    if height is not None:
        dim += ' height="' + height + '"'

    return '<img class="' + style + '" src="' + path + '" ' + dim + '/>'


def section(title, content):
    r = '<div class="report-section">'
    r += '<h2>' + title + '</h2>'
    r += content
    r += '</div>'
    return r


def tab_block(tab_id, content, status='not-selected-tab-content'):
    if content is None:
        content = ''
    r = '<div id="tab-content-' + tab_id + '" class="' + status + '">'
    r += content
    r += '</div>'
    return r


def tabs_items(tabs, selected):
    r = ''
    for tab_id, tab_label in tabs:
        style = 'not-selected-tab'
        if tab_id == selected:
            style = 'selected-tab'
        r += '<span id="tab-label-' + tab_id + '"  onClick="display_tab_content(\'' + tab_id + '\', \'' + selected + '\')" class="' + style + '">' + tab_label + '</span>'
    return '<div class="tabs">' + r + '</div>'


def block_link(block_id, block_label, style, location):
    return '<a name="begin_label-' + block_id + '"/>&#160;<p id="label-' + block_id + '" onClick="display_article_report(\'' + block_id + '\', \'label-' + block_id + '\', \'' + location + '\')" class="report-link-' + style + '">' + block_label.replace(' ', '&#160;') + '</p>'


def block_element(block_id, content, style, location):
    r = '<div id="' + block_id + '" class="report-block-' + style + '">'
    r += content
    r += '<div class="endreport"><span class="button" onClick="display_article_report(\'' + block_id + '\', \'label-' + block_id + '\', \'' + location + '\')"> ' + _('close') + ' </span></div>'
    r += '</div>'
    return r


def save_report_js():
    s = []
    s.append('<script type="text/javascript">')
    s.append('function save_report(filename) {')
    s.append(' var a = document.getElementById("download_file");')
    s.append(' var file = new Blob([document.innerHTML], {type: \'text/html\'});')
    s.append(' a.href = URL.createObjectURL(file);')
    s.append(' a.download = filename;')
    s.append(' a.click();')
    s.append('}')
    s.append('</script>')
    return ''.join(s)


def save_form(display, filename):
    r = ''
    if display:
        s = []
        #s.append('<p class="selected-tab" onclick="save_report(' + "'" + filename + "'" + ')">[ {message} ]</p>'.format(message=_('save report with my comments')))
        s.append('<a id="download_file"></a>')

        r = tag('div', ''.join(s), 'tabs')
    return r


def label_values(labels, values):
    r = {}
    for i in range(0, len(labels)):
        r[labels[i]] = values[i]
    return r


def display_report(report_filename):
    try:
        webbrowser.open('file:///' + report_filename.replace('//', '/').encode(encoding=sys.getfilesystemencoding()), new=2)
    except:
        pass


