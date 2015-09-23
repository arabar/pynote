from datetime import datetime
import json
import os.path
import re
import unicodedata
import click
from babel.dates import format_timedelta, format_datetime
from . import config
from .utils import error, die


def load_notes(path=config.DATA_PATH):
    """
    Scans the given path and returns a list of notes
    which is sorted by the modification time. Any directory
    and the tagfile is ignored. Die path argument has to be
    an instance of pathlib.Path.
    """
    if path.exists():
        data = [Note(f) for f in path.iterdir()
                if f.is_file() and (f.suffix not in
                config.IGNORE_EXTENSIONS and f != Note.tagfile)]
        return sorted(data, key=lambda n: n.age)
    else:
        error('The directory {} does not exist!'.format(path))
        click.echo('Creating new directory {}.'.format(path))
        path = config.TRASH_PATH
        path.mkdir(parents=True)
        exit(1)


def get_note(data, key):
    """A wrapper for getting a note out of a list of notes."""
    if key < len(data):
        note = data[key]
        return note
    else:
        die('This note does not exist!')


def filter_tags(data, tag_list):
    """
    Filter out notes depending on given taglist. The
    taglist is a python list. This function just returns
    the notes whose tags match the tags in the taglist.
    It returns a tuple with the index and the note (i, note).
    """
    # Avoid duplicates!
    # http://stackoverflow.com/a/4230131/2587286
    seen = set()
    for i, note in enumerate(data):
        for tag in tag_list:
            if tag in note.tags and note not in seen:
                yield (i, note)
                seen.add(note)


class Note:
    """
    Represents a note. A note object maps to a textfile
    somewhere in the filesystem. The note's title is maps
    to the filename and the updated attribute to the modification
    time.
    """
    tagfile = config.DATA_PATH / 'tags.json'

    def __init__(self, path):
        self.path = path
        self.title = path.stem
        self.slug = self._slugify(self.title)
        # If the file is not present create an empty one.
        if not path.exists():
            path.touch()
        self.updated = self._getmtime()
        self.age = self._calc_age()

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self.path)

    @property
    def content(self):
        with self.path.open('r') as f:
            return f.read()

    @content.setter
    def content(self, value):
        with self.path.open('w') as f:
            return f.write(value)

    @property
    def tags(self):
        if self.tagfile.exists():
            with self.tagfile.open() as f:
                tags = json.load(f)
            if self.title in tags:
                return tags[self.title]
            else:
                return []
        else:
            return []

    @tags.setter
    def tags(self, value):
        if self.tagfile.exists():
            with self.tagfile.open() as f:
                tags = json.load(f)
        else:
            self.tagfile.touch()
            tags = []
        # Check if tags are valid, see #18.
        for tag in value:
            if ' ' in tag:
                raise AttributeError('No spaces in tags allowed!')
        tags[self.title] = value

        with self.tagfile.open('w') as f:
            json.dump(tags, f, indent=4)

    @tags.deleter
    def tags(self):
        if self.tagfile.exists():
            with self.tagfile.open('r') as f:
                tags = json.load(f)
            # Check if there are any tags assigned, see #23.
            if self.title in tags:
                del tags[self.title]
                with self.tagfile.open('w') as f:
                    json.dump(tags, f, indent=4)

    @classmethod
    def create(cls, title, encrypted=False):
        if config.EXTENSION:
            filename = title + config.EXTENSION
        else:
            filename = title

        path = config.DATA_PATH / filename
        if path.exists():
            raise FileExistsError('Note already exists!')
        else:
            return cls(path)

    def update_path(self, path):
        """
        When self.path is updated the note object needs to
        be reinitialized. So let's wrap the constructor!
        """
        self.__init__(path)

    def format_header(self, colors=config.COLORS):
        header = '{} @ {}, {} ago'.format(
            self.title,
            self.format_updated(),
            self.format_age()
        )
        header = click.style(header, bold=True) if colors else header
        if self.tags:
            header += '\n'
            header += ' / '.join(self.tags)
        return header

    def format_age(self):
        return format_timedelta(self.age, locale=config.LOCALE)

    def format_updated(self):
        return format_datetime(
            self.updated,
            format=config.DATEFORMAT,
            locale=config.LOCALE
        )

    def _getmtime(self):
        updated = os.path.getmtime(str(self.path))
        return datetime.fromtimestamp(updated)

    def _calc_age(self):
        return datetime.now() - self.updated

    @staticmethod
    def _slugify(value):
        # stolen from Django: django/utils/text.py
        value = unicodedata.normalize('NFKD', value)
        value = value.encode('ascii', 'ignore').decode('ascii')
        value = re.sub('[^\w\s-]', '', value).strip().lower()
        return re.sub('[-\s]+', '-', value)
