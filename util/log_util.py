import difflib
import re


class STYLES:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def style_text(text, style=STYLES.BOLD):
    if style is list:
        for s in style:
            text = style_text(text, s)
    return style + text + STYLES.END


def print_styled(text, style=STYLES.BOLD):
    print(style_text(text, style))


def clean_lines(in_str: str):
    if not in_str:
        return []
    lines = []
    for line in in_str.splitlines():
        line = re.sub(r" ", " ", line)  # Pull out nbsp
        lines.append(line.strip())
    return lines


def get_diff(a, b, indent=0):
    tabs = "\t" * indent
    is_different = False
    diff_text = ""
    for diff_line in difflib.Differ().compare(clean_lines(a), clean_lines(b)):
        style = STYLES.BOLD
        if diff_line.startswith("+"):
            style = STYLES.GREEN
        if diff_line.startswith("-"):
            style = STYLES.RED
        if style != STYLES.BOLD:
            is_different = True
            diff_text += tabs + style_text(diff_line, style) + '\n'
    if is_different:
        return diff_text

    # Don't run with splitlines (true), as extra whitespace will confuse the output. We're ok with extra lines at the end.
    for diff_line in difflib.Differ().compare(a.splitlines(),
                                              b.splitlines()):
        style = STYLES.BOLD
        if diff_line.startswith("+"):
            style = STYLES.GREEN
        if diff_line.startswith("-"):
            style = STYLES.RED
        if style != STYLES.BOLD:
            diff_line = re.sub(r" ", " <NBSP> ", diff_line)  # Bring attention to nbsp

            diff_text += (tabs + style_text("Whitespace Difference:", STYLES.PURPLE) +
                          style_text(diff_line, style) + '\n')

    return diff_text


def prompt_y_n(question, default="no"):
    response = input(f"{question} (y/n, default={default}):")
    return response.lower().startswith("y")
