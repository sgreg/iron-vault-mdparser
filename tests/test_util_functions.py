from ironvaultmd.util import convert_link_name
from utils import CompareData

def test_util_convert_link_name():
    data = [
        CompareData[str]("[link name](https://example.org)", "link name"),
        CompareData[str]("[linkName](https://example.org)", "linkName"),
        CompareData[str]("[link\\/name](https://example.org)", "link/name"),
        CompareData[str]("[link/name](https://example.org)", "link/name"),
        CompareData[str]("before [link name](https://example.org) after", "before link name after"),
        CompareData[str]("before[link name](https://example.org)after", "beforelink nameafter"),
        CompareData[str]("[]()", "[]()"),
        CompareData[str]("[[link name]]", "link name"),
        CompareData[str]("[[linkName]]", "linkName"),
        CompareData[str]("[[link\\/name]]", "link/name"),
        CompareData[str]("[[link/name]]", "link/name"),
        CompareData[str]("before [[link name]] after", "before link name after"),
        CompareData[str]("before[[link name]]after", "beforelink nameafter"),
        CompareData[str]("[[]]", "[[]]"),
        CompareData[str]("[[https://example.org|link name]]", "link name"),
        CompareData[str]("[[https://example.org|linkName]]", "linkName"),
        CompareData[str]("[[https://example.org|link\\/name]]", "link/name"),
        CompareData[str]("[[https://example.org|link/name]]", "link/name"),
        CompareData[str]("before [[https://example.org|link name]] after", "before link name after"),
        CompareData[str]("before[[https://example.org|link name]]after", "beforelink nameafter"),
        CompareData[str]("[[|]]", "[[|]]"),
        CompareData[str]("No link in here", "No link in here"),
        CompareData[str]("", ""),
    ]

    for d in data:
        assert convert_link_name(d.content) == d.expected

