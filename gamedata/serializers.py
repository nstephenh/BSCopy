from rest_framework import serializers

from gamedata.models import Publication, PublishedDocument, RawPage, PublishedUnit, PublishedProfile, \
    ProfileCharacteristic, SpecialRule


class PublicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publication
        fields = ['id', 'name']


class PublishedDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublishedDocument
        fields = ['id', 'version']


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawPage
        fields = ['id', 'file_page_number', 'actual_page_number', 'raw_text', 'cleaned_text']


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublishedUnit
        fields = ['id', 'name']


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublishedProfile
        fields = ['id', 'name']


class ProfileCharacteristicSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileCharacteristic
        fields = ['id', 'characteristic_type', 'value_text']


class SpecialRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecialRule
        fields = ['id', 'name', 'text']
