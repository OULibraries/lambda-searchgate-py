import pprint

from chalicelib import searchapi


def test_one():
    r = searchapi.Result()
    print(r)


def test_two():

    lgapi = searchapi.LibGuidesSilo()
    result = lgapi.get_result("french", 5)

    pprint.pprint(result.get_data())
