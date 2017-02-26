import unittest
import re
import datetime
import pandas as pd
import numpy as np

from querygraph.evaluation import expr_funcs


uppercase = expr_funcs.Uppercase()
lowercase = expr_funcs.Lowercase()
capitalize = expr_funcs.Capitalize()
to_date = expr_funcs.ToDate()
regex_sub = expr_funcs.RegexSub()


class UppercaseTests(unittest.TestCase):

    def test_str_execute(self):
        test_str = 'abc'
        self.assertEquals('ABC', uppercase(test_str))

    def test_list_execute(self):
        test_list = ['abc', 'abc']
        self.assertEquals(['ABC', 'ABC'], uppercase(test_list))

    def test_series_execute(self):
        test_series = pd.Series(['abc', 'abc'])
        self.assertEquals(True, pd.Series(['ABC', 'ABC']).equals(uppercase(test_series)))

    def _test_np_array(self):
        test_np_array = np.array(['abc', 'abc'])
        self.assertEquals(True, np.array_equal(uppercase(test_np_array), np.array(['ABC', 'ABC'])))


class LowercaseTests(unittest.TestCase):

    def test_str_execute(self):
        test_str = 'ABC'
        self.assertEquals('abc', lowercase(test_str))

    def test_list_execute(self):
        test_list = ['ABC', 'ABC']
        self.assertEquals(['abc', 'abc'], lowercase(test_list))

    def test_series_execute(self):
        test_series = pd.Series(['ABC', 'ABC'])
        self.assertEquals(True, pd.Series(['abc', 'abc']).equals(lowercase(test_series)))

    def _test_np_array(self):
        test_np_array = np.array(['ABC', 'ABC'])
        self.assertEquals(True, np.array_equal(lowercase(test_np_array), np.array(['abc', 'abc'])))


class CapitalizeTests(unittest.TestCase):

    def test_str_execute(self):
        test_str = 'abc'
        self.assertEquals('Abc', capitalize(test_str))

    def test_list_execute(self):
        test_list = ['abc', 'abc']
        self.assertEquals(['Abc', 'Abc'], capitalize(test_list))

    def test_series_execute(self):
        test_series = pd.Series(['abc', 'abc'])
        self.assertEquals(True, pd.Series(['Abc', 'Abc']).equals(capitalize(test_series)))


class ToDateTests(unittest.TestCase):

    def test_str_execute(self):
        test_str = '2009-01-06'
        expected_value = datetime.datetime(2009, 1, 6).date()
        self.assertEquals(expected_value, to_date(test_str, format='%Y-%m-%d'))

    def test_list_execute(self):
        test_str = '2009-01-06'
        test_list = [test_str, test_str]
        test_date = datetime.datetime(2009, 1, 6).date()
        expected_value = [test_date, test_date]
        self.assertEquals(expected_value, to_date(test_list, format='%Y-%m-%d'))

    def test_series_execute(self):
        test_str = '2009-01-06'
        test_list = [test_str, test_str]
        test_series = pd.Series(test_list)
        test_date = datetime.datetime(2009, 1, 6).date()
        expected_value = pd.Series([test_date, test_date])
        self.assertEquals(True, expected_value.equals(to_date(test_series, format='%Y-%m-%d')))


class RegexSubTests(unittest.TestCase):

    def test_str_execute(self):
        test_str = "Example String"
        expected_value = re.sub('[ES]', 'a', test_str)
        self.assertEquals(expected_value, regex_sub(test_str, regex='[ES]', with_val='a'))

    def test_list_execute(self):
        test_str = "Example String"
        expected_str_value = re.sub('[ES]', 'a', test_str)
        test_list = [test_str, test_str]
        expected_value = [expected_str_value, expected_str_value]
        self.assertEquals(expected_value, regex_sub(test_list, regex='[ES]', with_val='a'))