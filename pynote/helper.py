def expand_dateformat(dateformat):
    """
    Takes the dateformat string from ~/.noterc
    and adds the '%'-signs.

    Y.m.d => %Y.%m.%d

    """
    format_str = ''

    for v in dateformat:
        if v.isalpha():
            format_str += '%' + v
        else:
            format_str += v
    return format_str


def create_tempfile():
    from tempfile import NamedTemporaryFile

    tmp_file = NamedTemporaryFile(delete=False)
    tmp_file.close()
    return tmp_file.name


def exit_not_exists():
    print(_('Error: This note does not exist!'))
    exit(1)


def highlight(data, lang):
    import pygments
    import pygments.lexers as lexers
    import pygments.formatters as formatters
    from pygments.util import ClassNotFound

    from pynote import config

    try:
        lexer = lexers.get_lexer_by_name(lang)
    except ClassNotFound:
        print(_('Lexer not found!'))
        exit(1)

    formatter = formatters.Terminal256Formatter(style=config.PYGMENTS_THEME)
    data = pygments.highlight(data, lexer, formatter)
    return data
