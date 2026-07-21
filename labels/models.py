from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'ラベル'
        verbose_name_plural = 'ラベル'


class Label(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='labels')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.category.name} / {self.name}'

    class Meta:
        verbose_name = '項目'
        verbose_name_plural = '項目'