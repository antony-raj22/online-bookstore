from django.test.runner import DiscoverRunner


class StoreDiscoverRunner(DiscoverRunner):
    """Run the installed store app tests when no test labels are supplied."""

    default_test_labels = ('store',)

    def run_tests(self, test_labels, **kwargs):
        return super().run_tests(test_labels or self.default_test_labels, **kwargs)
