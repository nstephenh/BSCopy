import os

try:
    import pdftotext
except Exception as e:
    print("You probably need poppler installed via Conda")
    exit()

from util.log_util import style_text, STYLES, print_styled

game_system_location = os.path.expanduser('~/BattleScribe/data/moreus-heresy/')

if __name__ == '__main__':
    raw_location = os.path.join(game_system_location, "raw")
    for filename in os.listdir(raw_location):
        if not filename.endswith(".pdf"):
            continue
        print(filename)
        file_path = os.path.join(raw_location, filename)
        with open(file_path, "rb") as f:
            pdf = pdftotext.PDF(f, physical=True)

        divider_start = 74
        divider_end = 83
        non_column_text = ""
        col_1_text = ""
        col_2_text = ""
        page_count = -2

        for page in pdf:
            page_count += 1

            if page_count < 109:
                continue
            for line in page.split('\n'):
                print(line[:divider_start] +
                      style_text(line[divider_start:divider_end], STYLES.UNDERLINE) +
                      line[divider_end:])
