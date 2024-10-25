from rest_framework import serializers

from gamedata.models import Publication, PublishedDocument, RawPage


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
