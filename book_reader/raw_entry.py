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

    def serialize(self):
        return {'Name': self.name, 'Stats': self.stats}


class RawUnit:
    def __init__(self, name: str, points: int = None):
        self.name = name
        self.points = points
        self.force_org: str | None = None
        self.model_profiles: list[RawProfile] = []
        self.special_rules: list[str] = []
        self.subheadings: {str: str} = {}

    def serialize(self) -> dict:
        dict_to_return = {'Name': self.name}
        if self.points is not None:
            dict_to_return['Points'] = self.points
        if self.force_org is not None:
            dict_to_return['Force Org'] = self.force_org
        dict_to_return.update({'Profiles': [profile.serialize() for profile in self.model_profiles],
                               'Subheadings': self.subheadings,
                               })
        return dict_to_return
