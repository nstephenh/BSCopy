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
    Anything that can be in multiple editions of a game. Can have a builder model for mapping multiple
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


class GameMod(models.Model):
    """
    A modification to a game system that adds or tweaks things.
    One source that has multiple "levels" of options may be broken up as such.
    """
    name = models.CharField(max_length=100, blank=True, null=True)
    edition = models.ForeignKey(GameEdition, on_delete=models.CASCADE)


class Publication(models.Model):
    edition = models.ForeignKey(GameEdition, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)

    publication_year = models.PositiveIntegerField(blank=True, null=True)  # Since we can't be super exact with dates.
    publication_date = models.DateField(blank=True, null=True)

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

    @property
    def units(self):
        return PublishedUnit.objects.filter(page=self)

    @property
    def rules(self):
        return SpecialRule.objects.filter(page=self)


class PublishedModel(models.Model):
    page = models.ForeignKey(RawPage, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class ForceOrg(GameMetaModel):
    pass  # All we need is name


# Rough equivalent of raw_entry.RawUnit
class PublishedUnit(PublishedModel):
    name = models.CharField(max_length=200)
    force_org = models.ForeignKey(ForceOrg, on_delete=models.CASCADE, blank=True, null=True)
    max = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} on {self.page}"


class RawText(PublishedModel):
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


class GameProfileType(GameMetaModel):
    pass  # All we need is name


class GameCharacteristicType(GameMetaModel):
    profile_type = models.ForeignKey(GameProfileType, on_delete=models.CASCADE)
    abbreviation = models.CharField(max_length=10)

    def __str__(self):
        if self.name:
            return f"{self.name} on {self.profile_type}"
        return f"{self.abbreviation} on {self.profile_type}"


class PublishedProfile(PublishedModel):
    name = models.CharField(max_length=100)
    profile_type = models.ForeignKey(GameProfileType, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.profile_type})"


class ProfileCharacteristic(models.Model):
    profile = models.ForeignKey(PublishedProfile, on_delete=models.CASCADE, related_name="characteristics")
    characteristic_type = models.ForeignKey(GameCharacteristicType, on_delete=models.CASCADE)
    value_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.characteristic_type} on {self.profile}"


class Miniature(models.Model):  # Roughly equivalent of raw_entry.RawModel
    # Using Miniature instead of model just to avoid confusion with django.
    unit = models.ForeignKey(PublishedUnit, on_delete=models.CASCADE, related_name='models')
    name = models.CharField(max_length=100)
    profile = models.OneToOneField('PublishedProfile', on_delete=models.CASCADE, related_name='model')


class SpecialRule(PublishedModel):
    name = models.CharField(max_length=100)
    text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} on {self.page}"

