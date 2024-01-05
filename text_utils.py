from util import SHARED_RULES_TYPE, get_random_bs_id

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


def format_quote_alikes(in_str):
    '''
    Converts double quote and it's right and left variations to &quot
    :param in_str:
    :return:
    '''
    return in_str.replace('"', '&quot;').replace('”', '&quot;').replace('“', '&quot;')


def option_process_line(line):
    global cost_per_model, model_max, errors
    name = line[:line.index('.')].strip()
    pts = 0
    try:
        pts_string = line[line.index('+') + 1:]
        pts = int(pts_string[:pts_string.index(' ')])
    except ValueError:
        pass  # Free

    return name, pts
