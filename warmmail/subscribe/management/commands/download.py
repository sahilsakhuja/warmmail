from django.core.management import BaseCommand
from luigi import build

from warmmail.subscribe.tasks_fetch import ConvertAQIFileToParquet


class Command(BaseCommand):
    help = "Run the download pipeline"

    def add_arguments(self, parser):
        # parser.add_argument("-f", "--full", action="store_true")
        pass

    def handle(self, *args, **options):
        out = build(
            [ConvertAQIFileToParquet()],
            local_scheduler=True,
            detailed_summary=True,
        )
        print(out)
        pass
