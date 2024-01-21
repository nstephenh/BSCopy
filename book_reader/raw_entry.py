class RawEntry:
    def __init__(self, name, stats, special_rules):
        self.name: str = name
        self.stats: dict[str: str] = stats
        self.special_rules: list[str] = special_rules

    def get_diffable_profile(self):
        text = ""
        print_dict = {"Name": self.name}
        print_dict.update(self.stats)
        for key, item in print_dict.items():
            text += f"{key}: {item}\n"
        for rule in self.special_rules:
            text += f"Special Rule: {rule}\n"
        return text
