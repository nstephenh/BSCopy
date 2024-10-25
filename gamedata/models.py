from datetime import date

from django.db import models
from django.utils import timezone


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
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE)

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
    document = models.ForeignKey(PublishedDocument, on_delete=models.CASCADE)
    file_page_number = models.PositiveIntegerField()
    actual_page_number = models.PositiveIntegerField(blank=True, null=True)
    raw_text = models.TextField(blank=True, null=True)
    cleaned_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.document} {self.file_page_number} {self.raw_text.strip()[:30]}..."


class RawErrata(models.Model):
    """
    A block of text in a document that changes another block of text in another document.
    """
    PublishedDocumentVersion = models.ForeignKey(PublishedDocument, on_delete=models.CASCADE)


class ProfileType(BuilderModel):
    pass


class CharacteristicType(BuilderModel):
    profile_type = models.ForeignKey(ProfileType, on_delete=models.CASCADE)
    abbreviation = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.name} on {self.profile_type}"


class PublishedBuilderModel(BuilderModel):
    publication = models.ForeignKey(Publication, on_delete=models.SET_NULL, blank=True, null=True)
    page_number = models.PositiveIntegerField(blank=True, null=True)

    document = models.ForeignKey(PublishedDocument, on_delete=models.CASCADE, blank=True, null=True,
                                 help_text="The exact publication this version was found in")

    class Meta:
        abstract = True


class Profile(PublishedBuilderModel):
    profile_type = models.ForeignKey(ProfileType, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.profile_type})"


class ProfileCharacteristic(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
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
