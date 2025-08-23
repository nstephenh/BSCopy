from settings import name_synonyms
from util.log_util import style_text, STYLES, print_styled

errors = ""


def split_at_dot(lines):
    """
    Given an entry split at line breaks containing bullet points, combine and split at bullet points
    :param lines:
    :return:
    """
    text_to_split = ""
    prev_line_ends_in_dash = False
    for line in lines:
        line = line.strip()
        if prev_line_ends_in_dash:
            prev_line_ends_in_dash = False
            text_to_split += line  # Skip the space we add in.
            continue
        if line.endswith("-"):
            prev_line_ends_in_dash = True
        text_to_split += " " + line
    bullet = None
    if "●" in text_to_split:  # Panoptica bullet
        bullet = "●"
    if "•" in text_to_split:  # GW bullet
        bullet = "•"
    if bullet is None:
        raise Exception(f"Could not find a bullet in {text_to_split}")
    bullet_entries = text_to_split.split(bullet + " ")  # Bullet followed by space
    return [entry.strip() for entry in bullet_entries if entry.strip() != ""]


def split_at_dash(line):
    delimiter = "- "
    dash_entries = line.split(delimiter)
    return [entry.strip() for entry in dash_entries if entry.strip() != ""]


def remove_plural(model_name):
    if " with " in model_name:
        components = model_name.split(" with ") # Ravagers with jump packs
        return remove_plural(components[0]) + " with " + remove_plural(components[1])
    if model_name.endswith('naires'):
        return model_name.replace('naires', 'ary')
    if model_name.endswith('s'):
        return model_name[:-1]
    return model_name


def make_plural(model_name):
    if " with " in model_name:
        components = model_name.split(" with ")  # Ravagers with jump packs
        return make_plural(components[0]) + " with " + make_plural(components[1])
    if model_name.endswith('s'):
        return model_name
    if model_name.endswith('y'):
        model_name = model_name[:-1] + "ie"
    return model_name + "s"


def number_word_to_int(word):
    units = [
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten"]
    return units.index(word)


def check_alt_names(name):
    if name in name_synonyms:
        return name_synonyms[name]
    return name


def get_generic_rule_name(rule_name, after_dash=False):
    # Special handling for some rules:
    if rule_name.startswith('Blast (') or rule_name.startswith('Large Blast (') \
            or rule_name.startswith('Massive Blast ('):
        return "Blast"
    if after_dash and '-' in rule_name:  # for Twin-linked, Two-handed, and Master-crafted
        components = rule_name.split('-')
        return components[0] + "-" + components[1].lower()

    if '(' in rule_name:
        return rule_name.split('(')[0] + '(X)'
    return rule_name


def replace_quote_alikes(in_str):
    '''
    Converts right and left double quote to quote
    :param in_str:
    :return:
    '''
    return in_str.replace('”', '"').replace('“', '"')


def cleanup_disallowed_bs_characters(in_str):
    '''
    Converts double quote, it's right and left variations to &quot,
    along with handling &amp
    :param in_str:
    :return:
    '''
    return in_str.replace('"', '&quot;').replace('”', '&quot;').replace('“', '&quot;') \
        .replace('&', '&amp;').replace("'", '&apos;')


def option_process_line(line):
    name = line[:line.index('.')].strip()
    pts = 0
    try:
        pts_string = line[line.index('+') + 1:]
        pts = int(pts_string[:pts_string.index(' ')])
    except ValueError:
        pass  # Free

    return name, pts


def column_text_to_paragraph_text(text, force_single_paragraph=False):
    # Simpler version of text_to_rules's processing that converts text into a set of paragraphs.
    # Will interpret a line that happens to end in a period as the end of a paragraph (minor bug).
    text_out = ""
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        text_out += line
        if not force_single_paragraph and line[-1] in [".", "…"]:
            # add linebreaks between paragraphs:
            text_out += "\n"
        else:
            text_out += " "  # Space instead of a line break.
    return text_out


bullet_options = ["-", "*", "●", "•"]


def get_bullet_type(existing_text):
    """
    Given existing text, find the bullet character used the most in that selection.
    :param existing_text:
    :return: "-", "*", "●", or "•", default to "●"
    """
    bullet_type = "●"  # Default to big bullet
    most_appearances = 0
    for option in bullet_options:
        if existing_text.count(option) > most_appearances:
            most_appearances = existing_text.count(option)
            bullet_type = option
    return bullet_type


def get_section_heatmap(section_text):
    heatmap = []
    lines = section_text.splitlines()

    # First, find the longest line
    # Populate empty slots in the heatmap
    heatmap = [0] * len(max(lines, key=len))

    # For each line, track whitespace and characters past the end of the line
    for line in section_text.splitlines():
        for char_index in range(len(heatmap)):
            if char_index >= len(line) or line[char_index] == " ":
                heatmap[char_index] += 1
    return heatmap


def print_heatmap_thresholds(heatmap, indicate_columns=None, debug_print=None):
    label_row_0 = ""
    label_row_1 = ""
    label_row_2 = ""
    for i in range(len(heatmap)):
        label_row_0 += str(i).rjust(3, " ")[-3]
        label_row_1 += str(i).rjust(3, " ")[-2]
        label_row_2 += str(i)[-1]
    print(f"\t{label_row_0}\n\t{label_row_1}\n\t{label_row_2}")

    for i in range(max(heatmap) + 2):
        print(f"{i}\t", end="")
        for count in heatmap:
            if count >= i:
                print(style_text("█", STYLES.GREEN), end="")
            else:
                print(style_text("█", STYLES.RED), end="")
        print()
    if isinstance(indicate_columns, list):
        print(f"\t", end="")
        for i in range(len(heatmap)):
            if i in indicate_columns:
                print(style_text("⎸", STYLES.CYAN), end="")
            else:
                print(" ", end="")
        print()


def get_col_dividers(heatmap, margins=None):
    if margins is None:
        margins = 10  # Margins prevent us from cutting off the start of a bulleted list.
    min_width = 2
    # A section can't be smaller than this defined margin.

    # look for the largest "edge"
    section_start = 0
    longest_edge = 0
    longest_edge_height = 0

    for index in range(len(heatmap) - 1):
        edge_height = heatmap[index] - heatmap[index + 1]
        if index < margins:
            continue  # Skip the first few lines
        if edge_height > longest_edge_height:
            longest_edge = index
            longest_edge_height = edge_height

    for index, item in enumerate(reversed(heatmap[:longest_edge])):
        if item != heatmap[longest_edge]:  # If this isn't the same length as the longest edge,
            section_start = len(
                heatmap[:longest_edge]) - index  # then the previous value it's the end of that a section.
            break

    section_end = longest_edge + 1  # the next section starts at the character after our longest_edge char.
    if section_end - section_start < min_width:  # But this could also make our divider too small.
        # print_styled(f"Had to use min_width because dividing colum was {section_end - section_start} chars",
        #              STYLES.YELLOW)
        section_start = section_end - min_width

    return section_start, section_end


def split_into_columns(text, ensure_middle=False, debug_print_level=0):
    if text.strip() == "":
        raise Exception("No text passed to split_into_columns")
    heatmap = get_section_heatmap(text)
    margins = None
    if ensure_middle:
        middle = len(max(text.splitlines(), key=len)) / 2
        margins = middle - 10  # 20char wide section in the center.
    divider_start, divider_end = get_col_dividers(heatmap, margins=margins)

    if debug_print_level > 2:
        print_heatmap_thresholds(heatmap,
                                 indicate_columns=[divider_start, divider_end],
                                 debug_print=text)

    return split_into_columns_at_divider(text, divider_end, divider_start, debug_print_level=debug_print_level)


def split_into_columns_at_divider(text: str, divider_end, divider_start=None, debug_print_level=0):
    if divider_start is None:
        divider_start = divider_end - 2
    original_text: list[str] = [""]
    non_column_lines: list[str] = []
    col_1_lines: list[str] = []
    col_2_lines: list[str] = []
    prev_line_had_col_brake = False
    for line in text.split('\n'):
        has_col_break = False
        col_1_only = False
        line = line.rstrip()  # Leftover trailing space can mess us up.
        if line.strip() == "":
            # An empty line could apply to any column, so lets just put it in all columns.
            if debug_print_level > 1:
                print(style_text("EMPTY LINE", STYLES.CYAN))
            if prev_line_had_col_brake:
                col_1_lines.append("")
                col_2_lines.append("")
            else:
                non_column_lines.append("")

            # Allow col break to persist across the linebreak
            continue

        if len(line) > divider_end:
            has_col_break = all(char == " " for char in line[divider_start:divider_end])
        elif prev_line_had_col_brake:
            # if the current line is too short but the previous line had a col break,
            has_col_break = True  # this line also has a col break.
            col_1_only = True  # and doesn't go in non-column

        if has_col_break:
            col_1 = line[:divider_start].rstrip()  # Leftover trailing space can mess us up.
            col_2 = ""
            if not col_1_only:
                col_2 = line[divider_end:].rstrip()  # Leftover trailing space can mess us up.
            if col_1:
                col_1_lines.append(col_1)
            if col_2:
                col_2_lines.append(col_2)
        else:
            non_column_lines.append(line)
        if debug_print_level > 0:
            print(f"{style_text('█', STYLES.GREEN if has_col_break else STYLES.RED)}\t", end="")
            print(
                f"{line[:divider_start]}{style_text(line[divider_start:divider_end], STYLES.UNDERLINE)}{line[divider_end:]}")
        original_text += line + "\n"
        prev_line_had_col_brake = has_col_break

    non_column_text = "\n".join(non_column_lines) + "\n"
    if debug_print_level > 0:
        print_styled("Non-column text:", STYLES.PURPLE)
        print(non_column_text)

    col_1_text = "\n".join(col_1_lines).rstrip() + "\n"
    if debug_print_level > 0:
        print_styled("Column 1 text:", STYLES.PURPLE)
        print(col_1_text)

    col_2_text = "\n".join(col_2_lines).rstrip() + "\n"
    if debug_print_level > 0:
        print_styled("Column 2 text:", STYLES.PURPLE)
        print(col_2_text)

    return (non_column_text, col_1_text, col_2_text, original_text)


def split_2_columns_at_right_header(two_column_section, header) -> (bool, str, str):
    """
    Given text in a two-column format, split the text at the position of a header
    :param two_column_section:
    :param header:
    :return: was_split, left, right
    """
    # If special rules, split wargear_and_on at that position
    # instead of using the find column and split there code.
    sr_col_index = get_2nd_colum_index_from_header(header, two_column_section)
    if sr_col_index is None:
        print(f"Could not properly locate column {header}")
        return False, two_column_section, ""
    _, left, right, _ = split_into_columns_at_divider(two_column_section, sr_col_index, debug_print_level=0)
    return True, left, right


def get_2nd_colum_index_from_header(header: str, two_column_section: str) -> int:
    sr_col_index = None
    if header in two_column_section:
        sr_row_index = get_index_of_line_with_headers(two_column_section, [header])
        if header in two_column_section.splitlines()[sr_row_index]:
            sr_col_index = two_column_section.splitlines()[sr_row_index].index(header)
    return sr_col_index


def split_at_header(header, datasheet_text, header_at_end_of_line=True) -> (bool, str, str):
    """
    Split DIRECTLY on a header index, including in the middle of a line.
    :param header:
    :param datasheet_text:
    :param header_at_end_of_line: default true, expect header to be directly followed by a linebreak
    :return: was_split, a, b
    """
    if header_at_end_of_line:
        header = header + "\n"
    lower_half = ""
    if header in datasheet_text:
        header_index = datasheet_text.index(header)
        lower_half = datasheet_text[header_index:]
        datasheet_text = datasheet_text[:header_index]
        return True, datasheet_text, lower_half
    return False, datasheet_text, lower_half


def split_on_header_line(raw_text, header, ignore_indent=True) -> (bool, str, str):
    """
    Split at a line starting with the header line, returning the line with the header.
    :param raw_text:
    :param header:
    :param ignore_indent: Defaults to true, allowing the header to be indented. If passing our own indent, set to false.
    :return: was_split, a, b(inclusive of header)
    """
    lines = raw_text.split("\n")
    for index, line in enumerate(lines):
        if line.startswith(header) or (ignore_indent and line.lstrip().startswith(header)):
            return True, "\n".join(lines[:index]), "\n".join(lines[index:])
    return False, raw_text, ""


def split_after_header(raw_text, header):
    """
    Splits after an indented header, such as:
    Special Rules:  Some items
                    More items
    Will split out after more items, and not just on the line "Special Rules"
    :param raw_text:
    :param header:
    :return:
    """
    header_spacing = 0
    lines = raw_text.split("\n")
    for index, line in enumerate(lines):
        if line.startswith(header):
            # print(f"Header line: {header_spacing} ⎹\t{line}")
            header_spacing = get_line_indent(line, len(header))
            continue
        if header_spacing:
            # Line is indented as part of table
            line_spacing = get_line_indent(line)
            if line_spacing != header_spacing:
                return "\n".join(lines[:index]), "\n".join(lines[index:])
            # print(f"{header_spacing} vs {line_spacing} ⎹\t{line}")
    return raw_text, ""


def does_line_contain_header(line, headers, header_index=0):
    if header_index >= len(headers):
        return True
    header_to_find = headers[header_index]
    if header_to_find == "WP" and header_to_find not in line:
        header_to_find = "WL"  # HH3 hotfix for the legacies document
    if header_to_find in line:
        # print(f"Found {header_to_find} in {line}")
        line = line[line.index(header_to_find):]
        return does_line_contain_header(line, headers, header_index + 1)
    return False


def get_index_of_line_with_headers(text: str, in_order_headers: [str]):
    """
    Find the index of the line which contains at least the last header in the array.
    If multiple headers are provided, the appearance must be in order.
    ex: headers: ["a", "b", "c"] finds the following lines:
        a b c
        b c
        c,
    but if a or b come after c, we will not find c. ex:
        c a ; (We ignore c because we trim the line after a first).
    This is very useful for finding the line where a table starts, and if the array only has 1 parameter, 
    it's essentially looking up a line with a specific header.
    :param text:    text to get line index of header row.
    :param in_order_headers: array of ordered headers.
    :return:
    """
    lines = text.splitlines()
    for index, line in enumerate(lines):
        for header in in_order_headers:
            if header in line:
                line = line[line.index(header) + len(header):]
                if header == in_order_headers[-1]:
                    return index


def split_at_unindent(text) -> (bool, str, str):
    """
    Given a block of text that starts indented, split it when the indent becomes broken
    :param text:
    :return: was_split, a, b
    """
    lines = text.splitlines()
    header_indent = get_line_indent(lines[0])
    for i, line_text in enumerate(lines):
        if line_text[:header_indent].strip() != "":
            return True, "\n".join(lines[:i]), "\n".join(lines[i:])
    return False, text, ""


def un_justify(text, move_bullets=False):
    index = None
    new_text_array = []
    for line in text.splitlines():
        if index is None:
            if line.strip() == "":
                continue  # skip over blank lines at the start
            stripped_line = line.lstrip()
            if move_bullets:
                for bullet in bullet_options:
                    stripped_line = stripped_line.lstrip(bullet).lstrip()
            index = len(line) - len(stripped_line)
        if len(line) < index:
            new_text_array.append("")
        else:
            un_justified_line = line[index:]
            if move_bullets:
                for bullet in bullet_options:
                    if bullet in line[:index]:  # If we cut off a bullet, re-add it to the start of the line.
                        un_justified_line = bullet + " " + line[index:]
                        break
            new_text_array.append(un_justified_line)
    return "\n".join(new_text_array)


def get_first_non_list_or_header_line(text, headers):
    """
    Get the first non-list entry or header line after the initial line.
    If the indent is the same, it counts it as a continuation of the existing entry.
    If a line starts with a parenthesis we also assume it's a continuation of an existing line.
    :param text: text to search
    :param headers: list of headers
    :return:
    """
    in_options = False
    in_option_line = False
    in_option_header = False
    last_indent = 0
    for index, line in enumerate(text.splitlines()[1:]):
        if line.strip() == "":
            continue
        if not in_options:
            if not (line.lstrip()[0] in bullet_options + ["("]
                    or line.strip() in headers
                    or last_indent == get_line_indent(line)):
                return index + 1
            last_indent = get_line_indent(line, 1)
            if line.strip() == "Options:" or line.strip() == "Options":
                in_options = True
            continue
        if not in_option_header and line.lstrip()[0] in ["●", "•"]:
            in_option_header = True
        if not in_option_line and line.lstrip()[0] == "-":
            in_option_line = True
        if (line.lstrip()[0] not in bullet_options) and (not in_option_header) and (not in_option_line):
            return index + 1
        if in_option_header and line.strip().endswith(":"):
            in_option_header = False
        if in_option_line and line.strip().endswith("points"):
            in_option_line = False


def get_line_indent(line, offset=0):
    for i, char in enumerate(line[offset:]):  # Skip the bullet
        if char != " ":
            return i + offset
    return 0


def read_type_and_subtypes(unit_type_text):
    type_and_subtypes = None
    if "(" in unit_type_text:
        type_and_subtypes = [unit_type_text.split("(")[0].strip()]
        type_and_subtypes += [text.strip() for text in unit_type_text.split("(")[1][:-1].strip().split(",")]
    else:
        type_and_subtypes = [unit_type_text.strip()]
    return type_and_subtypes


def remove_copyright_footer(text):
    footer_text = "Permission to print/download for personal use."
    return text.partition(footer_text)[0].rstrip()


def looks_like_sentence(line):
    """
    See if this line of text contains words not commonly found in tables, but are commonly found in sentences.
    :param line:
    :return:
    """
    if ". " in line:
        return True

    # Not "the" or "of" because weapons could be named "the something of something"
    suspicious_words = ["are", "at", "than", "a", "an", "by"]
    for word in suspicious_words:
        if f" {word} " in line:
            return True
    return False
