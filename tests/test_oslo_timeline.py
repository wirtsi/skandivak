from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def without_monday_dinner(source):
    """Exclude the user-updated Monday dinner from historical snapshots.

    Its current tentative status is asserted by test_monday_tranen_is_tentative.
    """
    pattern = r'<li class="oslo-event(?: is-pending)?">\s*<div class="oslo-event-meta"><span class="oslo-clock">Abends</span>.*?</li>'
    return re.sub(pattern, '', source, flags=re.S)


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
        for text in ['Vorläufig geplant', 'Vorschlag', 'Tøyenbad']:
            self.assertIn(text, self.source)
        self.assertIn('id="oslo-timeline"', self.source)
        self.assertLess(self.source.index('id="oslo-timeline"'), self.source.index('Oslo — so sieht es aus'))

    def test_opera_moved_to_sunday_1230(self):
        saturday = re.search(r'<article[^>]+id="oslo-24".*?</article>', self.source, re.S)
        sunday = re.search(r'<article[^>]+id="oslo-25".*?</article>', self.source, re.S)
        assert saturday is not None and sunday is not None
        self.assertNotIn('Hinter die Kulissen der Oper', saturday.group())
        self.assertIn('Grünerløkka', saturday.group())
        for text in ['2026-10-25T12:30:00+01:00', '12:30', 'Termin bestätigt', 'Hinter die Kulissen der Oper', '12:15', 'The Little Pickle']:
            self.assertIn(text, sunday.group())
        self.assertLess(sunday.group().index('Hinter die Kulissen der Oper'), sunday.group().index('The Little Pickle'))
        oslo = re.search(r'<section id="oslo-timeline".*?</section>', self.source, re.S)
        assert oslo is not None
        for stale in ['13:00 · Wunschzeit', 'Oper noch buchen', 'Nach Anreise und Führung', 'Sonst direkt zur Oper']:
            self.assertNotIn(stale, oslo.group())

    def test_little_pickle_confirmed_two_hour_slot(self):
        sunday = re.search(r'<article[^>]+id="oslo-25".*?</article>', self.source, re.S)
        assert sunday is not None
        dinner = re.search(r'<li class="oslo-event is-booked">(?:(?!</li>).)*The Little Pickle.*?</li>', sunday.group(), re.S)
        self.assertIsNotNone(dinner)
        assert dinner is not None
        for text in ['2026-10-25T17:30:00+01:00', '2026-10-25T19:30:00+01:00', 'Telefonisch bestätigt', '2 Stunden']:
            self.assertIn(text, dinner.group())
        oslo = re.search(r'<section id="oslo-timeline".*?</section>', self.source, re.S)
        assert oslo is not None
        for stale in ['15–17 Uhr', 'Little-Pickle-Uhrzeit', 'Reservierungszeit ist hier noch offen', 'nach Reservierungszeit']:
            self.assertNotIn(stale, oslo.group())
        self.assertIn('Ab 19:30', sunday.group())

    def test_monday_tranen_is_tentative(self):
        monday = re.search(r'<article[^>]+id="oslo-26".*?</article>', self.source, re.S)
        self.assertIsNotNone(monday)
        assert monday is not None
        dinner = re.search(r'<li class="oslo-event is-pending">\s*<div class="oslo-event-meta"><span class="oslo-clock">Abends</span>.*?</li>', monday.group(), re.S)
        self.assertIsNotNone(dinner)
        assert dinner is not None
        for text in ['Tranen', 'Vorläufig geplant', 'Uhrzeit und Reservierung sind noch offen']:
            self.assertIn(text, dinner.group())
        self.assertNotIn('is-booked', dinner.group())

    def test_existing_sections_preserved(self):
        for text in ['Unsere Reise', 'Oslo-Insider', 'Essen in Göteborg', 'Wo wir schlafen']:
            self.assertIn(text, self.source)
        for tag in ['div', 'section', 'article', 'ol', 'nav']:
            self.assertEqual(self.source.count(f'<{tag}>') + self.source.count(f'<{tag} '), self.source.count(f'</{tag}>'), tag)


if __name__ == '__main__':
    unittest.main()
