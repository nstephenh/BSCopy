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


def get_bullet_type(existing_text):
    """
    Given existing text, find the bullet character used the most in that selection.
    :param existing_text:
    :return: "-", "*", "●", or "•", default to "●"
    """
    bullet_type = "●"  # Default to big bullet
    bullet_options = ["-", "*", "●", "•"]
    most_appearances = 0
    for option in bullet_options:
        if existing_text.count(option) > most_appearances:
            most_appearances = existing_text.count(option)
            bullet_type = option
    return bullet_type
