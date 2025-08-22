import timeit
from unittest import mock

from django.contrib.auth import get_user_model
from django_webtest import WebTest
from testapp.models import Dragonfly, Sighting
from testapp.views import DragonflyViewSet, SightingInline


class PerformanceTest(WebTest):
    timeit_execution_count = 10

    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create(username="root", is_superuser=True)

        self.alpha = Dragonfly.objects.create(name="alpha", age=47)
        for i in range(1000):
            Sighting.objects.create(name=f"Berlin {i}", dragonfly=self.alpha)

    def _get_detail_performance_baseline(self):
        # we simulate rendering a thousand rows with 10 columns
        # using a baseline template that is as simple as possible
        links = DragonflyViewSet().links

        # with verbose name, html check, attribute:
        # ~0,25s

        # with html check, attribute:
        # ~0,2s

        # with html check that doesn't try to access attribute first
        # ~0.1s

        # with attribute:
        # ~0,07s
        # just having a simple if-false-node there bumps this up to 0.09s

        with (
            mock.patch.object(SightingInline, "paginate_by", 1000),
            mock.patch.object(SightingInline, "fields", ["name", "age"] * 5),
            mock.patch.object(
                SightingInline,
                "detail_template_name",
                "performance_baseline_inline.html",
            ),
        ):

            def render():
                response = self.app.get(
                    links["detail"].reverse(self.alpha),
                    user=self.user,
                )
                self.assertContains(response, "alpha")
                self.assertContains(response, "Berlin 999")

            execution_time = timeit.timeit(render, number=self.timeit_execution_count)

        return execution_time / self.timeit_execution_count

    def _get_detail_performance(self):
        # we simulate rendering a thousand rows with 10 columns
        links = DragonflyViewSet().links
        with mock.patch.object(SightingInline, "paginate_by", 1000), mock.patch.object(
            SightingInline, "fields", ["name", "age"] * 5
        ):

            def render():
                response = self.app.get(
                    links["detail"].reverse(self.alpha),
                    user=self.user,
                )
                self.assertContains(response, "alpha")
                self.assertContains(response, "Berlin 999")

            execution_time = timeit.timeit(render, number=self.timeit_execution_count)

        # times on an m1 macbook air
        # with |is_html roughly 1 s
        # with .is_html roughly 1.1 s
        # including detail_field.html but replacing it's contents with a simple get_attribute: 0.85
        # simply dumping value instead of including detail_field.html is 0.5 s
        # so one of the worst parts is including the field template
        return execution_time / self.timeit_execution_count

    def test_detail_performance_compared_to_baseline(self):
        baseline = self._get_detail_performance_baseline()
        detail = self._get_detail_performance()

        # keep our overhead in check, at most 300% over the baseline template
        # might be a good idea to get rid of includes to reduce this
        self.assertLess(detail, 4 * baseline)
