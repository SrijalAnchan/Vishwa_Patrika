# Generated by Django 5.1.3 on 2025-02-22 13:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0002_newsarticle_api_source_id_newsarticle_category_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newsarticle',
            name='category',
            field=models.CharField(choices=[('POL', 'Politics'), ('TECH', 'Technology'), ('BUS', 'Business'), ('SPO', 'Sports'), ('ENT', 'Entertainment')], default='POL', max_length=50),
        ),
        migrations.AlterField(
            model_name='newsarticle',
            name='source',
            field=models.CharField(choices=[('BBC', 'BBC News'), ('REU', 'Reuters'), ('TH', 'The Hindu'), ('WION', 'WION'), ('TOI', 'The Times of India')], default='BBC', max_length=50),
        ),
    ]
