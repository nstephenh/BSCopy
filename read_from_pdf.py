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
    # look for the largest "edge"
    section_start = 0
    longest_edge = 0  # Best initial guess
    longest_edge_height = 0

    for index in range(len(heatmap) - 1):
        edge_height = heatmap[index] - heatmap[index + 1]
        if edge_height > longest_edge_height:
            longest_edge = index
            longest_edge_height = edge_height

    for index, item in enumerate(reversed(heatmap[:longest_edge])):
        if item != heatmap[longest_edge]:  # If this isn't the same length as the longest edge,
            section_start = len(heatmap[:longest_edge]) - index  # then the previous value it's the end of that a section.
            break
    return section_start, longest_edge


game_system_location = os.path.expanduser('~/BattleScribe/data/horus-heresy/')


def split_into_columns(page_text):
    non_column_text = ""
    col_1_lines = []
    col_2_lines = []
    heatmap = get_page_heatmap(page_text)
    divider_start, divider_end = get_divider_end(heatmap)
    # print_heatmap_thresholds(heatmap,
    #                          indicate_columns=[divider_start, divider_end],
    #                          debug_print_page=page)
    prev_line_had_col_brake = False
    for line in page_text.split('\n'):
        has_col_break = False
        col_1_only = False
        print(line, end="")  # Don't print end, so we can reprint over the line while processing.

        if line.strip() == "":
            # An empty line could apply to any column, so lets just put it in all columns.
            print(style_text("\rEMPTY LINE", STYLES.GREEN))
            non_column_text += "\n"
            col_1_lines.append("")
            col_2_lines.append("")
            # Allow col break to persist across the linebreak
            continue

        if len(line) > divider_end:
            has_col_break = all(char == " " for char in line[divider_start:divider_end])
        elif prev_line_had_col_brake:
            # if the current line is too short but the previous line had a col break,
            has_col_break = True  # this line also has a col break.
            col_1_only = True  # and doesn't go in non-column

        if has_col_break:
            col_1 = line[:divider_start]
            col_2 = ""
            if not col_1_only:
                col_2 = line[divider_end:]
            if col_1:
                col_1_lines.append(col_1)
            else:
                print(style_text("\rSkipped Newline in A\r", STYLES.GREEN), end="")
                # ^ this prints over the existing line, so reprint it.

            if col_2:
                col_2_lines.append(col_2)
            else:
                debug_col_spacing = ' ' * divider_end
                print(style_text(f"\r{debug_col_spacing} Skipped Newline in B\r", STYLES.CYAN), end="")
                # ^ this prints over the existing line, so reprint it.
                print(line, end="")

            prev_a_blank = bool(col_1)
            prev_b_blank = bool(col_2)

        else:
            non_column_text += line + "\n"
        print()
        prev_line_had_col_brake = has_col_break
    print_styled("Non-column text:", STYLES.PURPLE)
    print(non_column_text)
    print_styled("Column 1 text:", STYLES.PURPLE)
    col_1_text = "\n".join(col_1_lines).rstrip()
    print(col_1_text)
    print_styled("Column 2 text:", STYLES.PURPLE)
    col_2_text = "\n".join(col_2_lines).rstrip()
    print(col_2_text)
    return non_column_text, col_1_text, col_2_text


if __name__ == '__main__':
    raw_location = os.path.join(game_system_location, "raw")
    for filename in os.listdir(raw_location):
        if not filename.endswith(".pdf"):
            continue
        print(filename)
        file_path = os.path.join(raw_location, filename)
        with open(file_path, "rb") as f:
            pdf = pdftotext.PDF(f, physical=True)

        page_count = -2  # Panoptica page offset.

        for page in pdf:
            page_count += 1

            if page_count < 52:
                continue
            if page_count > 53:
                exit()  # Early quit on page 1


            # TODO: Strip headers and footers.
            non_col_text, col_1_text, col_2_text = split_into_columns(page)

            for col_text in [col_1_text, col_2_text]:
                if "Special Rules" in col_text:
                    split_into_columns(col_text)
