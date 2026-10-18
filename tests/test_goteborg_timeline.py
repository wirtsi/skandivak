from pathlib import Path
import re
import subprocess
import unittest
from test_oslo_timeline import without_monday_dinner

ROOT = Path(__file__).resolve().parents[1]


class GoteborgTimelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / 'index.html').read_text()
        match = re.search(r'<section id="goteborg-timeline".*?</section>', cls.source, re.S)
        cls.timeline = match.group() if match else ''

    def test_three_dated_linkable_days(self):
        self.assertTrue(self.timeline, 'Göteborg timeline missing')
        self.assertEqual(self.timeline.count('<article '), 3)
        for day in range(29, 32):
            self.assertIn(f'id="goteborg-{day}"', self.timeline)
            self.assertIn(f'href="#goteborg-{day}"', self.timeline)
            self.assertIn(f'datetime="2026-10-{day}"', self.timeline)
        self.assertLess(self.source.index('id="goteborg-timeline"'), self.source.index('Göteborg — so sieht es aus'))

    def test_realistic_program_with_unbooked_status(self):
        for text in ['Gothia Towers', 'Universeum', 'Haga', 'Liseberg', 'Universeum &amp; Ocean Dreams sind gebucht', 'Regenplan', 'Rückreise', 'Wisdome', '09:30–19:00']:
            self.assertIn(text, self.timeline)
        self.assertEqual(self.timeline.count('class="oslo-event is-booked"'), 1)
        for text in ['Ocean Dreams', '15:00–15:22', '2026-10-29T15:00:00+01:00', '2026-10-29T15:22:00+01:00', '2 Erwachsene', '2 Kinder', '4 Eintritte', '1.180 SEK', 'separate Einlasszeit ist im Screenshot nicht angegeben']:
            self.assertIn(text, self.timeline)
        for text in ['Eintrittszeit buchen', 'auf Freitagvormittag verschieben', 'Keine Aktivität ist gebucht']:
            self.assertNotIn(text, self.timeline)
        self.assertIn('Abreisezeit ist noch offen', self.timeline)
        self.assertIn('https://www.liseberg.se/kalender', self.timeline)
        self.assertIn('https://www.universeum.se/besok/biljetter', self.timeline)

    def test_children_and_ticket_requirements(self):
        for text in ['11 Jahren', '15 Jahren', 'Flora', 'Lilia', 'Größen', 'Åkpass', '18 Uhr', 'Kaninlandet']:
            self.assertIn(text, self.timeline)

    def test_reuses_component_and_preserves_prior_timelines(self):
        self.assertEqual(self.timeline.count('class="oslo-day goteborg-day"'), 3)
        self.assertEqual(self.timeline.count('<ol class="oslo-events"'), 3)
        previous = subprocess.check_output(['git', 'show', '18bd943:index.html'], cwd=ROOT, text=True)
        for city in ['oslo', 'smogen']:
            pattern = rf'<section id="{city}-timeline".*?</section>'
            old = re.search(pattern, previous, re.S)
            new = re.search(pattern, self.source, re.S)
            self.assertIsNotNone(old)
            self.assertIsNotNone(new)
            assert old is not None and new is not None
            self.assertEqual(without_monday_dinner(old.group()), without_monday_dinner(new.group()))


if __name__ == '__main__':
    unittest.main()
