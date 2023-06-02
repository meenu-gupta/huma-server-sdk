from sdk.common.utils.string_utils import to_plural, compact_html

msg_template = "'%s' is not equal to '%s'"


def test_to_plural():
    test_cases = (
        ("word", "words"),
        ("Article", "Articles"),
        ("penalty", "penalties"),
        ("Body", "Bodies"),
    )
    for case, result in test_cases:
        assert result == to_plural(case), msg_template % (case, result)


def test_compact_html():
    html_template = """
    <html>
        <body>
        <!--[if mso]><table width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td style="padding-right: 10px; padding-left: 10px; padding-top: 10px; padding-bottom: 10px; font-family: Georgia, 'Times New Roman', serif"><![endif]-->
        greater  good!
        </body>
    </html>
    """
    expect_compact_html = """<html> <body> <!--[if mso]><table width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td style="padding-right: 10px; padding-left: 10px; padding-top: 10px; padding-bottom: 10px; font-family: Georgia, 'Times New Roman', serif"><![endif]--> greater good! </body> </html>"""
    assert expect_compact_html == compact_html(html_template)


if __name__ == "__main__":
    test_to_plural()
    test_compact_html()
