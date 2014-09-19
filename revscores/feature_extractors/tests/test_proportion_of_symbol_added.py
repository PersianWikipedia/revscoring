from collections import namedtuple

from mw import Timestamp
from nose.tools import eq_

from ..proportion_of_symbol_added import proportion_of_symbol_added


def test_proportion_of_symbol_added():
    
    eq_(proportion_of_symbol_added(10, 1), 1/10)
    eq_(proportion_of_symbol_added(10, 2), 2/10)
    eq_(proportion_of_symbol_added(1, 1), 1) # prevents divide by zero
