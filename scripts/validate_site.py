"""Check the small static site for required HTML structure."""

from html.parser import HTMLParser
from pathlib import Path


VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}


class SiteParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []
        self.tags = set()
        self.h1_count = 0
        self.title_parts = []
        self.in_title = False

    def handle_decl(self, decl):
        if decl.lower() != "doctype html":
            self.errors.append("Expected an HTML5 doctype.")

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        self.tags.add(tag)
        if tag == "html" and not attributes.get("lang"):
            self.errors.append("The html element must declare its language.")
        if tag == "meta" and attributes.get("name", "").lower() == "viewport":
            self.has_viewport = True
        if tag == "h1":
            self.h1_count += 1
        if tag == "title":
            self.in_title = True
        if tag not in VOID_ELEMENTS:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID_ELEMENTS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if not self.stack:
            self.errors.append(f"Unexpected closing tag: </{tag}>.")
            return
        if self.stack[-1] != tag:
            self.errors.append(f"Expected </{self.stack[-1]}> before </{tag}>.")
            return
        self.stack.pop()

    def handle_data(self, data):
        if self.in_title:
            self.title_parts.append(data)

    def validate(self):
        if self.stack:
            self.errors.append(f"Unclosed HTML elements: {', '.join(self.stack)}.")
        if not "title" in self.tags or not "".join(self.title_parts).strip():
            self.errors.append("The page must have a non-empty title.")
        if self.h1_count != 1:
            self.errors.append("The page must contain exactly one h1 heading.")
        if "main" not in self.tags:
            self.errors.append("The page must include a main landmark.")
        if not getattr(self, "has_viewport", False):
            self.errors.append("The page must include a responsive viewport meta tag.")
        return self.errors


def main():
    source = Path("index.html").read_text(encoding="utf-8")
    parser = SiteParser()
    parser.has_viewport = False
    parser.feed(source)
    parser.close()
    errors = parser.validate()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print("Website structure is valid.")


if __name__ == "__main__":
    main()
