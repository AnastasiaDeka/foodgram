# Generated by Django 4.2 on 2025-04-07 19:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0004_shoppingcart_created_at_alter_ingredient_name_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ingredient',
            options={'ordering': ('name',), 'verbose_name': 'Ингредиент', 'verbose_name_plural': 'Ингредиенты'},
        ),
        migrations.AlterModelOptions(
            name='recipeingredient',
            options={'ordering': ('recipe',), 'verbose_name': 'Ингредиент в рецепте', 'verbose_name_plural': 'Ингредиенты в рецептах'},
        ),
        migrations.AddField(
            model_name='recipe',
            name='short_link',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Короткая ссылка'),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='measurement_unit',
            field=models.CharField(choices=[('шт', 'Штуки'), ('г', 'Граммы'), ('мл', 'Миллилитры')], default='шт', max_length=64, verbose_name='Единица измерения'),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='name',
            field=models.CharField(max_length=128, verbose_name='Название ингредиента'),
        ),
    ]
