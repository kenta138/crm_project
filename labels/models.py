from django.db import models


# クラス名・DB上は「Category」だが、画面表示上は「ラベル」という名称にリネームしている。
# (Labelモデルは画面上「項目」と表示される。用語対応はlabels/forms.py・各テンプレート側で行う)
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "ラベル"
        verbose_name_plural = "ラベル"


# クラス名・DB上は「Label」だが、画面表示上は「項目」という名称にリネームしている。
class Label(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="labels"
    )
    # 使用中の項目を無効化しても取引先との紐付けは残したいため、削除ではなく非活性化で運用する。
    # 無効化された項目はclients/admin.pyのformfield_for_manytomanyで新規選択肢から除外される。
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.category.name} / {self.name}"

    class Meta:
        verbose_name = "項目"
        verbose_name_plural = "項目"
