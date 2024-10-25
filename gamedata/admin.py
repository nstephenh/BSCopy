from django.contrib import admin

from gamedata.models import Game, GameEdition, Publication, CharacteristicType, ProfileType, Profile, \
    ProfileCharacteristic, RawPage, RawErrata

admin.site.register(Game)
admin.site.register(GameEdition)
admin.site.register(Publication)
admin.site.register(ProfileType)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_filter = ["edition"]


@admin.register(CharacteristicType)
class CharacteristicTypeAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_filter = ["edition"]


@admin.register(ProfileCharacteristic)
class ProfileCharacteristicAdmin(admin.ModelAdmin):
    search_fields = ['profile__name']
    autocomplete_fields = ['profile', 'characteristic_type']
    list_filter = ["profile__edition"]


@admin.register(RawPage)
class RawPageAdmin(admin.ModelAdmin):
    list_filter = ["document"]


@admin.register(RawErrata)
class RawErrataAdmin(admin.ModelAdmin):
    list_filter = ["page__document"]
