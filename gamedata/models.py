from datetime import date

from django.db import models


# Create your models here

class Publisher(models.Model):
    """
    A company or collective creating a document for release.
    """
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        if self.abbreviation:
            return self.abbreviation
        return self.name


class Game(models.Model):
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return self.name


class GameMetaModel(models.Model):
    """
    Anything that can be in multiple editions of a game, will have a builder model that maps back to it.
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        abstract = True


class GameEdition(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    edition_name = models.CharField(max_length=100, blank=True, null=True)
    release_year = models.PositiveIntegerField()

    def __str__(self):
        if self.edition_name:
            return f"{self.game} {self.edition_name}"
        else:
            return f"{self.game} ({self.release_year})"


class BuilderModel(models.Model):
    edition = models.ForeignKey(GameEdition, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True, null=True)
    builder_id = models.CharField(max_length=40, blank=True, null=True)
    builder_type = None  # TODO: Set a builder type for reference?

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.name} from {self.edition}"


class Publication(BuilderModel):
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)

    publication_year = models.PositiveIntegerField(blank=True, null=True)  # Since we can't be super exact with dates.
    publication_date = models.DateField(blank=True, null=True)

    name = models.CharField(max_length=120)

    def __str__(self):
        return f"{self.name}"


class PublishedDocument(models.Model):
    """
    Has versions for each printing.
    """
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name="documents")

    version = models.CharField(max_length=10)

    release_date = models.DateField(blank=True, null=True)
    release_year = models.PositiveSmallIntegerField(blank=True, null=True,
                                                    help_text="If exact release date is not known")
    release_month = models.PositiveSmallIntegerField(blank=True, null=True,
                                                     help_text="If exact release date is not known")
    sort_date = models.DateField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.release_date is not None:
            self.sort_date = self.release_date
        else:
            if self.release_month is not None and self.release_year is not None:
                self.sort_date = date(year=self.release_year, month=self.release_month, day=1)
            if self.release_year is not None:
                self.sort_date = date(year=self.release_year, month=1, day=1)
        super(PublishedDocument, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.publication} {self.version}"


class RawPage(models.Model):
    document = models.ForeignKey(PublishedDocument, on_delete=models.CASCADE, related_name='pages')
    file_page_number = models.PositiveIntegerField()
    actual_page_number = models.PositiveIntegerField(blank=True, null=True)
    raw_text = models.TextField(blank=True, null=True)
    cleaned_text = models.TextField(blank=True, null=True)
    rules_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.document} pg{self.file_page_number}: {self.raw_text.strip()[:30]}..."

    def find_errata(self):
        return RawErrata.objects.filter(target_page=str(self.actual_page_number), target_docs=self.document)


class ForceOrg(BuilderModel):
    pass  # All we need is name


# Rough equivalent of raw_entry.RawUnit
class PublishedUnit(models.Model):
    page = models.ForeignKey(RawPage, on_delete=models.CASCADE, related_name='units')
    name = models.CharField(max_length=200)
    force_org = models.ForeignKey(ForceOrg, on_delete=models.CASCADE, blank=True, null=True)
    max = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} on {self.page}"


class RawText(models.Model):
    page = models.ForeignKey(RawPage, on_delete=models.CASCADE, related_name='texts')
    unit = models.ForeignKey(PublishedUnit, on_delete=models.CASCADE, related_name='subheadings', blank=True, null=True)
    title = models.CharField(max_length=100)
    text = models.TextField(blank=True, null=True)

    def __str__(self):
        if self.unit:
            return f"{self.title} on {self.unit}"
        return f"{self.title} on {self.page}"


class RawErrata(RawText):
    """
    A block of text in a document that changes one or more blocks of text in another document.
    """
    # Target page is not an integer because it could be a range, or 'Various Pages', etc
    target_page = models.CharField(max_length=len("Various Pages"))
    target_docs = models.ManyToManyField(PublishedDocument, related_name="Errata")

    def __str__(self):
        target_name_list = (self.target_docs.all().values_list("publication__name", flat=True))
        return (f"{self.page.document} pg{self.page.file_page_number}: " +
                f"{self.title} ({', '.join(target_name_list)} Page {self.target_page})")


class ProfileType(BuilderModel):
    pass  # All we need is name


class CharacteristicType(BuilderModel):
    profile_type = models.ForeignKey(ProfileType, on_delete=models.CASCADE)
    abbreviation = models.CharField(max_length=10)

    def __str__(self):
        if self.name:
            return f"{self.name} on {self.profile_type}"
        return f"{self.abbreviation} on {self.profile_type}"


class PublishedBuilderModel(BuilderModel):
    publication = models.ForeignKey(Publication, on_delete=models.SET_NULL, blank=True, null=True)
    page_number = models.PositiveIntegerField(blank=True, null=True)

    document = models.ForeignKey(PublishedDocument, on_delete=models.CASCADE, blank=True, null=True,
                                 help_text="The exact publication this version was found in")

    class Meta:
        abstract = True


class Profile(PublishedBuilderModel):
    profile_type = models.ForeignKey(ProfileType, on_delete=models.CASCADE)
    unit = models.ForeignKey(PublishedUnit, on_delete=models.CASCADE, null=True, blank=True, related_name="profiles")

    def __str__(self):
        return f"{self.name} ({self.profile_type})"


class ProfileCharacteristic(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="characteristics")
    characteristic_type = models.ForeignKey(CharacteristicType, on_delete=models.CASCADE)
    value_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.characteristic_type} on {self.profile}"


class GameMod(models.Model):
    """
    A modification to a game system that adds or tweaks things.
    One source that has multiple "levels" of options may be broken up as such.
    """
    name = models.CharField(max_length=100, blank=True, null=True)
    edition = models.ForeignKey(GameEdition, on_delete=models.CASCADE)
