import pytest
from mainpkg.core import utils
from mainpkg.core.utils.OrderedSet import OrderedSet


def test_ordered_set() -> None:
    oset = OrderedSet()
    oset.add(5)
    oset.add(1)
    oset.add(2)
    oset.add(3)
    oset.add(4)
    assert oset.to_list() == [5, 1, 2, 3, 4]
