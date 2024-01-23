import os

try:
    import pdftotext
except Exception as e:
    print("You probably need poppler installed via Conda")
    exit()

from util.log_util import style_text, STYLES, print_styled


def get_page_heatmap(page):
    heatmap = []
    for line in page.split('\n'):
        char_index = 0
        last_char_was_space = False
        for character in line:
            # Populate empty slots in the heatmap
            if len(heatmap) == char_index:
                heatmap.append(0)
            if character == " ":
                if last_char_was_space:
                    heatmap[char_index] += 1
                last_char_was_space = True
            else:
                last_char_was_space = False
            char_index += 1
    return heatmap


def print_heatmap_thresholds(heatmap, indicate_columns=None, debug_print_page=None):
    if debug_print_page:
        for line in debug_print_page.split('\n'):
            print("\t" + line)
    label_row_1 = ""
    label_row_2 = ""
    for i in range(len(heatmap)):
        label_row_1 += str(i).rjust(2, " ")[-2]
        label_row_2 += str(i)[-1]
    print(f"\t{label_row_1}\n\t{label_row_2}")

    for i in range(max(heatmap) + 1):
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
                print(style_text("^", STYLES.CYAN), end="")
            else:
                print(" ", end="")
        print()


def get_divider_end(heatmap):
    margins = 5  # Margins prevent us from cutting off the start of a bulleted list.
    # A section can't be smaller than this defined margin.

    # look for the largest "edge"
    section_start = 0
    longest_edge = 0  # Best initial guess
    longest_edge_height = 0

    for index in range(len(heatmap) - 1):
        edge_height = heatmap[index] - heatmap[index + 1]
        if index < margins:
            continue  # Skip the first few lines
        if edge_height > longest_edge_height:
            longest_edge = index
            longest_edge_height = edge_height

    for index, item in enumerate(reversed(heatmap[:longest_edge])):
        if item < heatmap[longest_edge]:  # If this isn't the same length as the longest edge,
            section_start = len(
                heatmap[:longest_edge]) - index  # then the previous value it's the end of that a section.
            break
    return section_start, longest_edge


game_system_location = os.path.expanduser('~/BattleScribe/data/horus-heresy/')


def split_into_columns(page_text, debug_print_level=0):
    # 3 lists of lists, which we can rejoin in non-col[0], col1[0], col2[0], non-col[1], etc.
    original_text: list[str] = [""]
    non_column_lines: list[list[str]] = [[]]
    col_1_lines: list[list[str]] = [[]]
    col_2_lines: list[list[str]] = [[]]
    if page_text.strip() == "":
        raise Exception("No text passed to split_into_columns")
    heatmap = get_page_heatmap(page_text)
    divider_start, divider_end = get_divider_end(heatmap)

    if debug_print_level > 1:
        print_heatmap_thresholds(heatmap,
                                 indicate_columns=[divider_start, divider_end],
                                 debug_print_page=page)

    prev_line_had_col_brake = False
    section = 0
    for line in page_text.split('\n'):
        has_col_break = False
        col_1_only = False
        line = line.rstrip()  # Leftover trailing space can mess us up.
        if line.strip() == "":
            # An empty line could apply to any column, so lets just put it in all columns.
            if debug_print_level > 0:
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
            print(f"{style_text('█', STYLES.GREEN if has_col_break else STYLES.RED)}\t {line}")
        original_text[section] += line + "\n"
        prev_line_had_col_brake = has_col_break

    sections = []
    for section in range(len(non_column_lines)):
        print_styled("Non-column text:", STYLES.PURPLE)
        non_column_text = "\n".join(non_column_lines[section]) + "\n"
        print(non_column_text)
        print_styled("Column 1 text:", STYLES.PURPLE)
        col_1_text = "\n".join(col_1_lines[section]).rstrip() + "\n"
        print(col_1_text)
        print_styled("Column 2 text:", STYLES.PURPLE)
        col_2_text = "\n".join(col_2_lines[section]).rstrip() + "\n"
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


def process_page(page, page_count):
    print_styled(str(page_count), STYLES.RED)

    # consider removing page number from bottom of page
    # The main content of the page should only have one section, so get the first section.
    page_header, col_1_text, col_2_text, _ = split_into_columns(page)[0]

    # If a datasheet, it should have two columns in the center of the page.
    if "Unit Composition" not in col_1_text and "Unit Composition" not in col_2_text:
        return False  # Not a datasheet
    datasheet_text = col_1_text if "Unit Composition" in col_1_text else col_2_text
    flavor_text = col_2_text if "Unit Composition" in col_2_text else col_1_text
    print_styled("Datasheet:", STYLES.RED)
    upper_half = datasheet_text
    # First, try and split this datasheet into parts based on known headers
    was_split, profiles, upper_half = split_at_header("Unit Composition", upper_half, header_at_end_of_line=False)
    if not was_split:
        print("Could not split at Unit Composition")
        return  # If this datasheet doesn't have "Unit composition, something is wrong

    # Access points comes before Options, though a sheet is not garunteed to have either.
    was_split, upper_half, lower_half = split_at_header("Access Points", upper_half)
    if not was_split:
        was_split, upper_half, lower_half = split_at_header("Options", upper_half)
        if not was_split:
            raise Exception("Could not split datasheet")

    upper_half, comp_and_wargear, type_and_special_rules, _ = split_into_columns(upper_half, debug_print_level=0)[0]

    # Now lets put everything together:
    print_styled("Reconstructed Datasheet", STYLES.GREEN)
    print("".join(
        [page_header, profiles, comp_and_wargear, type_and_special_rules, upper_half, lower_half]))
    # Could also print flavor text on the end if we wanted.


def try_get_page_offset():
    global page_offset
    if page.count("\n") > 5:  # Assuming there are 5 lines to check,
        for line in page.split("\n")[-5:]:  # Check the last 5 lines
            line = line.strip()
            if line.isdigit():
                page_read_from_pdf = int(line)
                print(f"Page in pdf is {page_read_from_pdf}")
                print(f"Page counter is {page_counter}")
                page_offset = page_read_from_pdf - page_counter
                break  # We've got our page offset, stop iterating.


if __name__ == '__main__':
    raw_location = os.path.join(game_system_location, "raw")
    for filename in os.listdir(raw_location):
        if not filename.endswith(".pdf"):
            continue
        print(filename)
        file_path = os.path.join(raw_location, filename)
        with open(file_path, "rb") as f:
            pdf = pdftotext.PDF(f, physical=True)

        page_offset = 0  # page offset is 0 on GW book, because cover is page 0
        for page_counter, page in enumerate(pdf):
            if page_counter < 5 and not page_offset:
                try_get_page_offset()
            if page_offset:
                page_number = page_counter + page_offset
                # print(f"Page number is {page_number}, from {page_counter} + {page_offset}")
            else:
                page_number = page_counter
            if page_number < 50:  # start on this page
                continue
            if page_number > 51:
                exit()  # Early quit after this page.

            process_page(page, page_number)
