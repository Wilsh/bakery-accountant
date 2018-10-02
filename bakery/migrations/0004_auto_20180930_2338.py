# Generated by Django 2.1.1 on 2018-10-01 03:38

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('bakery', '0003_auto_20180218_2122'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderQuantity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveSmallIntegerField(default=1)),
            ],
        ),
        migrations.RemoveField(
            model_name='order',
            name='recipes',
        ),
        migrations.AlterField(
            model_name='order',
            name='created_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='order',
            name='quoted_price',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='orderquantity',
            name='for_order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bakery.Order'),
        ),
        migrations.AddField(
            model_name='orderquantity',
            name='for_recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bakery.Recipe'),
        ),
    ]
