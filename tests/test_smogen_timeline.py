from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SmogenTimelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / 'index.html').read_text()
        match = re.search(r'<section id="smogen-timeline".*?</section>', cls.source, re.S)
        cls.timeline = match.group() if match else ''

    def test_three_dated_linkable_days(self):
        self.assertTrue(self.timeline, 'Smögen timeline missing')
        self.assertEqual(len(re.findall(r'<article\b', self.timeline)), 3)
        for day in range(27, 30):
            self.assertIn(f'id="smogen-{day}"', self.timeline)
            self.assertIn(f'href="#smogen-{day}"', self.timeline)
            self.assertIn(f'datetime="2026-10-{day}"', self.timeline)
        ids = re.findall(r'\bid="([^"]+)"', self.source)
        self.assertEqual(len(ids), len(set(ids)))

    def test_seasonal_rules_and_unbooked_status(self):
        for text in ['09–17 Uhr', '09–13 Uhr', 'unter 13', 'Spa-Zeit anfragen', 'Keine Aktivität ist gebucht', 'Vorschlag', 'Höstlov', 'Öffnung prüfen']:
            self.assertIn(text, self.timeline)
        self.assertNotIn('is-booked', self.timeline)
        self.assertNotIn('status booked', self.timeline)
        self.assertIn('https://www.smogenshafvsbad.se/vara-paket/hostlovspaket/', self.timeline)

    def test_useful_coast_program_and_weather_fallback(self):
        for text in ['Fjällbacka', 'Kungsklyftan', 'Smögenbryggan', 'Ramsvik', 'Smögens Hafvsbad', 'Gothia Towers', 'Regenplan', 'rutschig', 'Fähren']:
            self.assertIn(text, self.timeline)
        self.assertLess(self.source.index('id="smogen-timeline"'), self.source.index('Bohuslän-Schären — so sieht es aus'))

    def test_shared_timeline_component_and_accessible_labels(self):
        self.assertEqual(self.timeline.count('<ol class="oslo-events"'), 3)
        self.assertEqual(self.timeline.count('class="oslo-day smogen-day"'), 3)
        self.assertIn('aria-labelledby="smogen-timeline-title"', self.timeline)
        self.assertIn('aria-label="Direkt zum Smögen-Reisetag"', self.timeline)

    def test_oslo_content_unchanged_from_last_commit(self):
        previous = subprocess.check_output(['git', 'show', '4b8791c:index.html'], cwd=ROOT, text=True)
        def extract(source):
            match = re.search(r'<section id="oslo-timeline".*?</section>', source, re.S)
            self.assertIsNotNone(match)
            assert match is not None
            return match.group()

        self.assertEqual(extract(previous), extract(self.source))


if __name__ == '__main__':
    unittest.main()
