# Generated by Django 5.0 on 2024-09-01 14:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='receipt_photo',
            field=models.ImageField(default='api', upload_to='', verbose_name='chek/'),
            preserve_default=False,
        ),
    ]
