from django.contrib import admin

from gamedata.models import Game, GameEdition, Publication, CharacteristicType, ProfileType, Profile, \
    ProfileCharacteristic, RawPage, RawErrata, RawText, ForceOrg

admin.site.register(Game)
admin.site.register(GameEdition)
admin.site.register(Publication)
admin.site.register(ProfileType)


class ModelBuilderAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_filter = ['edition']


@admin.register(Profile)
class ProfileAdmin(ModelBuilderAdmin):
    pass


@admin.register(CharacteristicType)
class CharacteristicTypeAdmin(ModelBuilderAdmin):
    pass


@admin.register(ProfileCharacteristic)
class ProfileCharacteristicAdmin(admin.ModelAdmin):
    search_fields = ['profile__name']
    autocomplete_fields = ['profile', 'characteristic_type']
    list_filter = ["profile__edition"]


@admin.register(RawPage)
class RawPageAdmin(admin.ModelAdmin):
    list_filter = ["document"]


@admin.register(RawText)
class RawTextAdmin(admin.ModelAdmin):
    list_filter = ["page__document", "page__document__publication", "page__document__publication__edition"]


@admin.register(RawErrata)
class RawErrataAdmin(admin.ModelAdmin):
    list_filter = ["target_docs"]


@admin.register(ForceOrg)
class ForceOrgAdmin(ModelBuilderAdmin):
    pass
