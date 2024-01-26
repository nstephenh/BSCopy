from util.log_util import style_text, STYLES, print_styled

errors = ""


def split_at_dot(lines):
    """
    Given an entry split at line breaks containing bullet points, combine and split at bullet points
    :param lines:
    :return:
    """
    space_string = " ".join(lines)
    bullet_entries = space_string.split("● ")
    return [entry.strip() for entry in bullet_entries if entry.strip() != ""]


def split_at_dash(line):
    # print("Split at dash this: ", line)
    dash_entries = line.split("- ")
    return [entry.strip() for entry in dash_entries if entry.strip() != ""]


def remove_plural(model_name):
    if model_name.endswith('s'):
        model_name = model_name[:-1]
    return model_name


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


def get_col_dividers(heatmap):
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
        print_styled(f"Had to use min_width because dividing colum was {section_end - section_start} chars",
                     STYLES.YELLOW)
        section_start = section_end - min_width

    return section_start, section_end


def split_into_columns(text, debug_print_level=0):
    if text.strip() == "":
        raise Exception("No text passed to split_into_columns")
    heatmap = get_section_heatmap(text)
    divider_start, divider_end = get_col_dividers(heatmap)

    if debug_print_level > 2:
        print_heatmap_thresholds(heatmap,
                                 indicate_columns=[divider_start, divider_end],
                                 debug_print=text)

    return split_into_columns_at_divider(text, divider_end, divider_start, debug_print_level=debug_print_level)


def split_into_columns_at_divider(text: str, divider_end, divider_start=None, debug_print_level=0):
    if divider_start is None:
        divider_start = divider_end - 2
    # 3 lists of lists, which we can rejoin in non-col[0], col1[0], col2[0], non-col[1], etc.
    original_text: list[str] = [""]
    non_column_lines: list[list[str]] = [[]]
    col_1_lines: list[list[str]] = [[]]
    col_2_lines: list[list[str]] = [[]]
    prev_line_had_col_brake = False
    section = 0
    for line in text.split('\n'):
        has_col_break = False
        col_1_only = False
        line = line.rstrip()  # Leftover trailing space can mess us up.
        if line.strip() == "":
            # An empty line could apply to any column, so lets just put it in all columns.
            if debug_print_level > 1:
                print(style_text("EMPTY LINE", STYLES.CYAN))
            if prev_line_had_col_brake:
                col_1_lines[section].append("")
                col_2_lines[section].append("")
            else:
                non_column_lines[section].append("")

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
                col_1_lines[section].append(col_1)
            if col_2:
                col_2_lines[section].append(col_2)
        else:
            if prev_line_had_col_brake:  # Start a new section
                non_column_lines.append([])
                col_1_lines.append([])
                col_2_lines.append([])
                col_2_lines.append([])
                original_text.append("")
                section += 1
            non_column_lines[section].append(line)
        if debug_print_level > 0:
            print(f"{style_text('█', STYLES.GREEN if has_col_break else STYLES.RED)}\t", end="")
            print(
                f"{line[:divider_start]}{style_text(line[divider_start:divider_end], STYLES.UNDERLINE)}{line[divider_end:]}")
        original_text[section] += line + "\n"
        prev_line_had_col_brake = has_col_break

    sections = []
    for section in range(len(non_column_lines)):

        non_column_text = "\n".join(non_column_lines[section]) + "\n"
        if debug_print_level > 0:
            print_styled("Non-column text:", STYLES.PURPLE)
            print(non_column_text)

        col_1_text = "\n".join(col_1_lines[section]).rstrip() + "\n"
        if debug_print_level > 0:
            print_styled("Column 1 text:", STYLES.PURPLE)
            print(col_1_text)

        col_2_text = "\n".join(col_2_lines[section]).rstrip() + "\n"
        if debug_print_level > 0:
            print_styled("Column 2 text:", STYLES.PURPLE)
            print(col_2_text)

        sections.append((non_column_text, col_1_text, col_2_text, original_text[section]))
    return sections


def split_at_header(header, datasheet_text, header_at_end_of_line=True) -> (bool, str, str):
    if header_at_end_of_line:
        header = header + "\n"
    lower_half = ""
    if header in datasheet_text:
        split_text = datasheet_text.split(header)
        datasheet_text = split_text[0]
        lower_half = header + split_text[1]
        return True, datasheet_text, lower_half
    return False, datasheet_text, lower_half


def split_after_header(raw_text, header):
    header_spacing = 0
    lines = raw_text.split("\n")
    for index, line in enumerate(lines):
        if line.startswith(header):
            line = line[len(header):]
            for i, char in enumerate(line):
                if char != " ":
                    header_spacing = i + len(header)
                    break
            continue
        if header_spacing:
            # Line is indented as part of table
            line_spacing = 0
            for i, char in enumerate(line):
                if char != " ":
                    line_spacing = i
                    break
            if line_spacing != header_spacing:
                return "\n".join(lines[:index]), "\n".join(lines[index:])
    return raw_text, ""


def does_line_contain_header(line, headers, header_index=0):
    if header_index >= len(headers):
        return True
    header_to_find = headers[header_index]
    if header_to_find in line:
        # print(f"Found {header_to_find} in {line}")
        line = line[line.index(header_to_find):]
        return does_line_contain_header(line, headers, header_index + 1)
    return False


def get_index_of_line_with_headers(text, stagger_row_headers):
    lines = text.splitlines()
    for index, line in enumerate(lines):
        for header in stagger_row_headers:
            if header in line:
                line = line[line.index(header) + len(header):]
                if header == stagger_row_headers[-1]:
                    return index


def un_justify(text, index):
    new_text_array = []
    for line in text.splitlines():
        if len(line) < index:
            new_text_array.append("")
        else:
            new_text_array.append(line[index:])
    return "\n".join(new_text_array)
