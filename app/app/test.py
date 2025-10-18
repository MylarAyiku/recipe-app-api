"""
Sample test
"""

from django.test import SimpleTestCase

from  app import calc


class CalcTests(SimpleTestCase):
    """Tests for calc.py"""

    def test_add_numbers(self):
        """Test adding numbers together"""
        res = calc.add(5, 6)

        self.assertEqual(res, 11)

    def test_subttract_number(self):
        """Test subtraction """
        res = calc.sub(10,15)

        self.assertEqual(res, -5)
