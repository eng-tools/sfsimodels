from sfsimodels import output


def test_format_value():
    assert output.format_value(0.45584) == "0.456"
    assert output.format_value(0.045584) == "0.0456"
    assert output.format_value(0.45554) == "0.456"
    assert output.format_value(0.45544) == "0.455"
    assert output.format_value(4.5584) == "4.56"
    assert output.format_value(0.45584, sf=4) == "0.4558"
    assert output.format_value(0.45) == "0.45"
    pass


if __name__ == '__main__':
    test_format_value()