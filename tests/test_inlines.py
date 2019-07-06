from beam import RelatedInline
from testapp.models import Sighting, Dragonfly


def test_inline_formset_is_generated():
    class SightingInline(RelatedInline):
        title = "Title of sightings"
        fields = ["name"]
        model = Sighting
        foreign_key_field = "dragonfly"

    formset = SightingInline(parent_model=Dragonfly).formset

    assert "name" in formset.forms[0].fields


def test_inlines_prefix_works_without_formset():
    class SightingInline(RelatedInline):
        title = "Title of sightings"
        fields = ["name", "created_at"]
        model = Sighting
        foreign_key_field = "dragonfly"

    assert SightingInline(parent_model=Dragonfly).prefix == "sighting_set"
