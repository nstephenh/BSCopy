from django.contrib import admin

from gamedata.models import Game, GameEdition, Publication, GameCharacteristicType, GameProfileType, PublishedProfile, \
    ProfileCharacteristic, RawPage, RawErrata, RawText, ForceOrg

admin.site.register(Game)
admin.site.register(GameEdition)
admin.site.register(Publication)
admin.site.register(GameProfileType)


class PublishedModelAdmin(admin.ModelAdmin):
    list_filter = ["page__document", "page__document__publication", "page__document__publication__edition"]


@admin.register(GameCharacteristicType)
class CharacteristicTypeAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(ForceOrg)
class ForceOrgAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(PublishedProfile)
class ProfileAdmin(PublishedModelAdmin):
    search_fields = ['name']


@admin.register(ProfileCharacteristic)
class ProfileCharacteristicAdmin(admin.ModelAdmin):
    search_fields = ['profile__name']
    autocomplete_fields = ['profile', 'characteristic_type']
    list_filter = ["profile__page__document",
                   "profile__page__document__publication",
                   "profile__page__document__publication__edition",
                   ]


@admin.register(RawPage)
class RawPageAdmin(admin.ModelAdmin):
    list_filter = ["document", "document__publication", "document__publication__edition"]


@admin.register(RawText)
class RawTextAdmin(PublishedModelAdmin):
    pass


@admin.register(RawErrata)
class RawErrataAdmin(PublishedModelAdmin):
    list_filter = ["target_docs"]
