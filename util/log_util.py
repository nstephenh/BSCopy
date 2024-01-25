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


def style_text(text, style: str or list[str] = STYLES.BOLD):
    if type(style) is list:
        # apply all styles with recursion.
        for s in style:
            text = style_text(text, s)
        return text
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
    diff_lines = list(difflib.Differ().compare(clean_lines(a), clean_lines(b)))
    diff_lines = [line for line in diff_lines if line[0] in ["-", "+"]]  # filter out ? (whitespace changes)

    diff_text = try_get_detailed_diff(diff_lines, tabs)
    if diff_text:
        return diff_text

    for diff_line in diff_lines:
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

    # Don't run with splitlines (true), as extra whitespace will confuse the output.
    # We're ok with extra lines at the end.
    if not a:
        a = ""
    if not b:
        b = ""
    diff_lines = list(difflib.Differ().compare(a.splitlines(),
                                               b.splitlines()))

    for diff_line in diff_lines:
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


def try_get_detailed_diff(diff_lines, tabs=""):
    diff_text = ""
    if len(diff_lines) % 2 == 0:
        alternating = True
        last_line_start = "+"
        pairs = []
        pair = 0
        for diff_line in diff_lines:
            if not diff_line[0] in ["+", "-"]:
                continue
            expected_start = alternate_plus_minus(last_line_start)
            if not diff_line.startswith(expected_start):
                alternating = False
                break
            last_line_start = expected_start  # update for next iteration.
            if expected_start == "-":
                pairs.append([diff_line])  # Add a list with this line in it to the end of the list
            else:
                pairs[pair].append(diff_line)  # Add this line to this pair's pair
                pair += 1

        if alternating:
            for pair in pairs:
                diff_text += get_two_line_diff(pair, tabs)
    return diff_text


def get_two_line_diff(pair, tabs=""):
    diff_text = ""
    shortest_line_length = min(len(pair[0]), len(pair[1]))
    for line in pair:
        diff_text += tabs
        style = STYLES.BOLD
        if line.startswith("+"):
            style = STYLES.GREEN
        if line.startswith("-"):
            style = STYLES.RED
        for i in range(len(line)):
            char_style = style
            if i >= shortest_line_length:
                char_style = STYLES.BOLD
            elif pair[0][i] != pair[1][i] and i > 1:  # Characters different, skipping the + and - at the start
                char_style = STYLES.UNDERLINE
            diff_text += style_text(line[i], [style, char_style])
        diff_text += '\n'
    return diff_text


def alternate_plus_minus(a):
    if a == "+":
        return "-"
    if a == "-":
        return "+"
    return "?"


def prompt_y_n(question, default="no"):
    response = input(f"{question} (y/n, default={default}):")
    return response.lower().startswith("y")
