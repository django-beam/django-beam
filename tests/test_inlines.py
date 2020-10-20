from beam import RelatedInline
from django.test import TestCase
from testapp.models import Dragonfly, Sighting


class InlineTest(TestCase):
    def test_inline_formset_is_generated(self):
        class SightingInline(RelatedInline):
            title = "Title of sightings"
            fields = ["name"]
            model = Sighting
            foreign_key_field = "dragonfly"

        formset = SightingInline(parent_model=Dragonfly).formset

        self.assertIn("name", formset.forms[0].fields)

    def test_inlines_prefix_works_without_formset(self):
        class SightingInline(RelatedInline):
            title = "Title of sightings"
            fields = ["name", "created_at"]
            model = Sighting
            foreign_key_field = "dragonfly"

        self.assertEqual(SightingInline(parent_model=Dragonfly).prefix, "sighting_set")
