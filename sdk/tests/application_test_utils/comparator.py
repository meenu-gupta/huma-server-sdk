class Skip(object):
    pass


skip = Skip()
supported_complex_types = (dict, list)
supported_primitive_types = (int, str, float, bool, Skip, type(None))


def _unpack_simple(expected, actual):
    if type(expected) not in supported_primitive_types:
        return False
    if type(actual) not in supported_primitive_types:
        return False

    if isinstance(expected, Skip):
        return True

    if type(expected) != type(actual):
        raise AssertionError(
            f"Expected simple type {type(expected)} but was {type(actual)}"
        )
    elif expected != actual:
        raise AssertionError(f"Expected {expected} but was {actual}")

    return True


def _unpack_complex(expected, actual):
    if isinstance(expected, Skip):
        return True

    if type(expected) != type(actual):
        raise AssertionError(
            f"Expected type is {type(expected)} but was {type(actual)}"
        )

    if isinstance(expected, dict):
        expected: dict = expected
        actual: dict = actual

        diff = expected.keys() - actual.keys()
        if len(diff) != 0:
            raise AssertionError(
                f"Expected keys {expected.keys()} but was {actual.keys()}. Missing keys {diff}"
            )

        for key in expected.keys():
            _unpack(expected[key], actual[key])

        return True
    elif isinstance(expected, list):
        if len(expected) != len(actual):
            raise AssertionError(
                f"Expected length is {len(expected)} but was {len(actual)}"
            )

        for e, a in zip(expected, actual):
            _unpack(e, a)

        return True
    else:
        return False


def _unpack(expected, actual):
    if _unpack_simple(expected, actual):
        pass
    elif _unpack_complex(expected, actual):
        pass
    else:
        raise AssertionError(
            f"Unknown type combination expected->{type(expected)} actual->{type(actual)}"
        )


def assert_matches(expected, actual):
    if type(expected) not in supported_complex_types:
        raise AssertionError(
            f"Expected type should be dict, list but was {type(expected)}"
        )
    if type(actual) not in supported_complex_types:
        raise AssertionError(
            f"Actual type should be dict or list but was {type(actual)}"
        )

    _unpack(expected, actual)
