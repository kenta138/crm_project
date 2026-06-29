from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'スーパーユーザーが存在しない場合のみ作成する'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                email='admin@email.com',
                password='pass0000',
                name='Admin',
            )
            self.stdout.write('スーパーユーザーを作成しました。')
        else:
            self.stdout.write('スーパーユーザーは既に存在します。')