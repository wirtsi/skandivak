from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.ids = []
        self.days = []
        self.times = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'article' and (attrs.get('id') or '').startswith('oslo-') and 'oslo-day' in (attrs.get('class') or '').split():
            self.days.append(attrs)
        if tag == 'time':
            self.times.append(attrs.get('datetime'))


class OsloTimelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / 'index.html').read_text()
        cls.doc = Document(cls.source)

    def test_four_linkable_days(self):
        self.assertEqual(len(self.doc.days), 4)
        for day in range(24, 28):
            self.assertIn(f'oslo-{day}', self.doc.ids)
            self.assertIn(f'href="#oslo-{day}"', self.source)
            self.assertIn(f'2026-10-{day}', self.doc.times)
        self.assertEqual(len(self.doc.ids), len(set(self.doc.ids)))

    def test_confirmed_dinner_exact_time_and_details(self):
        self.assertIn('2026-10-24T19:00:00+02:00', self.doc.times)
        for text in ['Kirkegata 1–3', '4 Personen', '2 × Izakaya Tasting Menu', '2 × à la carte', 'Gebucht']:
            self.assertIn(text, self.source)

    def test_suggestions_are_not_reservations(self):
        for text in ['Wunschzeit', 'Noch buchen', '15–17 Uhr', 'Uhrzeit abgleichen', 'Vorschlag', 'Tøyenbad']:
            self.assertIn(text, self.source)
        self.assertIn('id="oslo-timeline"', self.source)
        self.assertLess(self.source.index('id="oslo-timeline"'), self.source.index('Oslo — so sieht es aus'))

    def test_existing_sections_preserved(self):
        for text in ['Unsere Reise', 'Oslo-Insider', 'Essen in Göteborg', 'Wo wir schlafen']:
            self.assertIn(text, self.source)
        for tag in ['div', 'section', 'article', 'ol', 'nav']:
            self.assertEqual(self.source.count(f'<{tag}>') + self.source.count(f'<{tag} '), self.source.count(f'</{tag}>'), tag)


if __name__ == '__main__':
    unittest.main()
