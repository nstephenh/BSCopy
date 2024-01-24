class RawProfile:
    def __init__(self, name: str, stats: dict[str: str], special_rules: list[str] = None):
        self.name: str = name
        self.stats: dict[str: str] = stats
        self.special_rules: list[str] = []
        if special_rules:
            for rule in special_rules:
                self.special_rules.append(rule.strip())

    def get_diffable_profile(self):
        text = ""
        print_dict = {"Name": self.name}
        print_dict.update(self.stats)
        for key, item in print_dict.items():
            text += f"{key}: {item}\n"
        text += f"Special Rules: {self.get_special_rules_list()}"
        # Printing each rule was a good idea but not great in practice for diffing.
        # for rule in self.special_rules:
        #    text += f"Special Rule: {rule}\n"
        return text

    def get_special_rules_list(self):
        return ", ".join(self.special_rules)


class RawUnit:
    def __init__(self, name: str, points: int = None):
        self.name = name
        self.points = points
        self.model_profiles: list[RawProfile] = []
