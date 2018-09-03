# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings
import cmsplugin_blog.fields
import tagging.fields


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0003_auto_20140926_2347'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Entry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_published', models.BooleanField(verbose_name='is published')),
                ('pub_date', models.DateTimeField(default=datetime.datetime.now, verbose_name='publish at')),
                ('tags', tagging.fields.TagField(max_length=255, blank=True)),
                ('placeholders', cmsplugin_blog.fields.M2MPlaceholderField(to='cms.Placeholder', editable=False)),
            ],
            options={
                'ordering': ('-pub_date',),
                'verbose_name': 'entry',
                'verbose_name_plural': 'entries',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EntryTitle',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('language', models.CharField(max_length=15, verbose_name='language', choices=[(b'pl', b'Polski')])),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('slug', models.SlugField(max_length=255, verbose_name='slug')),
                ('author', models.ForeignKey(verbose_name='author', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('entry', models.ForeignKey(verbose_name='entry', to='cmsplugin_blog.Entry')),
            ],
            options={
                'verbose_name': 'blogentry',
                'verbose_name_plural': 'blogentries',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LatestEntriesPlugin',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin')),
                ('limit', models.PositiveIntegerField(help_text='Limits the number of items that will be displayed', verbose_name='Number of entries items to show')),
                ('current_language_only', models.BooleanField(verbose_name='Only show entries for the current language')),
                ('tagged', models.CharField(max_length=255, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.AlterUniqueTogether(
            name='entrytitle',
            unique_together=set([('language', 'slug')]),
        ),
    ]
