from nose.tools import eq_

from .. import parent_revision
from ...dependencies import solve


def test_words():

    words = solve(parent_revision.words,
                  cache={parent_revision.text: "Some text words 55."})
    eq_(words, ["Some", "text", "words"])

    # Make sure we don't error when there is no parent revision
    words = solve(parent_revision.words,
                  cache={parent_revision.text: None})
    eq_(words, [])
