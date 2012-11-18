"""Various document classes."""

import os.path
import re
import shutil

try:
    import markdown
except ImportError:
    pass

from weblib.conf import config

class Document(object):
    """Basic document class.

    A document is anything that can be rendered. All attributes of a
    document instance are made available to a template when being
    rendered.

    This class is safe to use as a mix-in.
    """

    def render(self, target, template, extra_context=None, **kwargs):
        env = config.jinja_environment
        template = env.get_or_select_template(template)
        target = self.format(target)
        target_base = getattr(config, "target_base", ".")
        target_path = os.path.join(target_base, target)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        context = {
            "rel_base": os.path.relpath(target_base,
                                        os.path.dirname(target_path)),
            "document": self,
        }
        context.update(self.__dict__)
        if extra_context:
            context.update(extra_context)
        context.update(kwargs)
        fp = open(target_path, mode="w", encoding="utf-8")
        template.stream(context).dump(fp)

    def format(self, text):
        return text.format_map(self.__dict__)


class StaticDocument(Document):
    """A static file that can't only be copied."""
    def __init__(self, path, **kwargs):
        super().__init__(**kwargs)
        self._path = os.path.join(getattr(config, "source_base", "."), path)

    def install(self, target):
        target = self.format(target)
        target_base = getattr(config, "target_base", ".")
        target_path = os.path.join(target_base, target)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        shutil.copy(self._path, target_path)


class ParsedDocument(Document):
    """Base class for documents parsed from files."""
    def __init__(self, path, **kwargs):
        super().__init__(**kwargs)
        path = os.path.join(getattr(config, "source_base", "."), path)
        self.parse(path)

    def parse(self, path):
        """Parse the file at *path* into the document.

        The path is already the correct absolute path.
        """
        raise NotImplementedError


class PythonDocument(ParsedDocument):
    """A document parsed from a Python file.

    The file is executed and the resulting local variables are the
    values of the document.  The file will receive a clean set of globals,
    so nothing is carried over from the build environment.
    """
    def parse(self, path):
        fp = open(path, "r", encoding="utf-8")
        code = compile(fp.read(), path, "exec")
        res = { }
        exec(code, { }, res)
        for key, value in res.items():
            setattr(self, key, value)


class MarkdownDocument(ParsedDocument):
    """A document parsed from a markdown file.

    The file must be a markdown document with the meta-data extension of
    the python-markdown library, ie., it must start with a series of
    headers separated from the actual content by a blank line.

    The file will be parsed and the parsed markdown content will be placed
    into a value ``"content"``. The meta-data will be added as document
    values.  Meta values with only a single element will be turned into
    that element instead of keeping the list.
    """
    def parse(self, path):
        try:
            md = markdown.Markdown(extensions=("meta",))
        except NameError:
            raise RuntimeError("missing python-markdown library")
        fp = open(path, "r", encoding="utf-8")
        content = md.convert(fp.read())
        for key, value in md.Meta.items():
            if len(value) == 1:
                value = value[0]
            setattr(self, key, value)
        self.content = content


DOCTYPES = {
    '.py': PythonDocument,
    '.md': MarkdownDocument,
}


class Sequence(object):
    """Access to neighbouring elements in a sequence."""
    def __init__(self, index, sequence):
        self.index = index
        self.index1 = index + 1
        self.revindex1 = len(sequence) - index
        self.revindex = self.revindex1 - 1
        self.first = index == 0
        self.last = index == len(sequence) - 1
        self.length = len(sequence)
        if not self.last:
            self.next = sequence[index + 1]
        if not self.first:
            self.prev = sequence[index - 1]


class DocumentList(list, Document):
    def __init__(self, pattern, doc_type=None, sort_key=None):
        super().__init__()
        self.add_by_pattern(pattern, doc_type)
        self.sort(key=sort_key)

    def add_by_pattern(self, pattern, doc_type=None):
        for m in self.find_by_pattern(pattern):
            if not doc_type:
                for suffix, type in DOCTYPES.items():
                    if m.string.endswith(suffix):
                        doc_type = type
                        break
                else:
                    raise RuntimeError("no document type for '%s'" % m.string)
            doc = doc_type(m.string)
            for key, value in m.groupdict().items():
                setattr(doc, key, value)
            doc.source_path = m.string
            self.append(doc)

    def sort(self, key=None, reverse=False):
        if key is None:
            key = lambda x: x.source_path
        super().sort(key=key, reverse=reverse)
        for idx, item in enumerate(self):
            item.sequence = Sequence(idx, self)

    def find_by_pattern(self, pattern):
        """Return an iterator with match objects over all matching files."""
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
        for f in self.get_file_list():
            m = pattern.search(f)
            if m is not None:
                yield m

    def get_file_list(self):
        try:
            return config.file_cache
        except AttributeError:
            pass
        config.file_cache = []
        source_base = getattr(config, "source_base", ".")
        if not source_base.endswith(os.sep):
            source_base += os.sep
        source_len = len(source_base)
        for dirpath, dirnames, filenames in os.walk(config.source_base):
            dirpath = dirpath[source_len:]
            config.file_cache.extend(os.path.join(dirpath, f)
                                            for f in filenames)
        return config.file_cache


class StaticList(DocumentList):
    def __init__(self, pattern, **kwargs):
        super().__init__(pattern, doc_type=StaticDocument, **kwargs)
