import datetime
from django.views.generic.list import ListView
from tagging.models import Tag, TaggedItem
from tagging.utils import get_tag

#try: # pragma: no cover
from django.views.generic.dates import BaseDateDetailView, ArchiveIndexView,  _date_from_string, YearArchiveView, MonthArchiveView, WeekArchiveView, DayArchiveView
from django.views.generic.detail import SingleObjectTemplateResponseMixin, DetailView
#except ImportError:  # pragma: no cover
#    from cbv.views.detail import SingleObjectTemplateResponseMixin, DetailView
#    from cbv.views.dates import BaseDateDetailView, ArchiveIndexView, YearArchiveView, MonthArchiveView, WeekArchiveView, DayArchiveView, _date_lookup_for_field, _date_from_string

from django.http import Http404
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _

from menus.utils import set_language_changer

from simple_translation.middleware import filter_queryset_language
from simple_translation.utils import get_translation_filter, get_translation_filter_language
from cmsplugin_blog.models import Entry
from cmsplugin_blog.utils import is_multilingual


class Redirect(Exception):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

class DateDetailView(SingleObjectTemplateResponseMixin, BaseDateDetailView):
    # Override to fix django bug
    def get_object(self, queryset=None):
        """
        Get the object this request displays.
        """
        year = self.get_year()
        month = self.get_month()
        day = self.get_day()
        date = _date_from_string(year, self.get_year_format(),
                                 month, self.get_month_format(),
                                 day, self.get_day_format())

        if queryset is None:
            queryset = self.get_queryset()

        if not self.get_allow_future() and date > datetime.date.today() and not self.request.user.is_staff: # pragma: no cover
            raise Http404(_(u"Future %(verbose_name_plural)s not available because %(class_name)s.allow_future is False.") % {
                'verbose_name_plural': queryset.model._meta.verbose_name_plural,
                'class_name': self.__class__.__name__,
            })

        # Filter down a queryset from self.queryset using the date from the
        # URL. This'll get passed as the queryset to DetailView.get_object,
        # which'll handle the 404
#        date_field = self.get_date_field()
#        field = queryset.model._meta.get_field(date_field)
#        lookup = _date_lookup_for_field(field, date)
#        queryset = queryset.filter(**lookup)

        return super(BaseDateDetailView, self).get_object(queryset=queryset)
    
class EntryDateDetailView(DateDetailView):
    slug_field = get_translation_filter(Entry, slug=None).items()[0][0]
    date_field = 'pub_date'
    template_name_field = 'template'
    month_format = '%m'
    queryset = Entry.objects.all()
    
    def get_object(self):
        try:
            obj = super(EntryDateDetailView, self).get_object()
        except Http404, e:
            # No entry has been found for a given language, we fallback to search for an entry in any language
            # Could find multiple entries, in this way we cannot decide which one is the right one, so we let
            # exception be propagated FIXME later
            if is_multilingual():
                try:
                    queryset = self.get_unfiltered_queryset()
                    obj = super(EntryDateDetailView, self).get_object(queryset=queryset)
                except Entry.MultipleObjectsReturned, s:
                    raise e
                # We know there is only one title for this entry, so we can simply use get()
                raise Redirect(obj.entrytitle_set.get().get_absolute_url())
            else:
                raise e

        set_language_changer(self.request, obj.language_changer)
        return obj
        
    def get_unfiltered_queryset(self):
        return super(EntryDateDetailView, self).get_queryset().published()
            
    def get_queryset(self):
        queryset = super(EntryDateDetailView, self).get_queryset()
        queryset = filter_queryset_language(self.request, queryset)
        if self.request.user.is_staff or self.request.user.is_superuser:
            return queryset
        else:
            return queryset.published()
    
    def dispatch(self, request, *args, **kwargs):
        try:
            return super(EntryDateDetailView, self).dispatch(request, *args, **kwargs)
        except Redirect, e:
            return redirect(*e.args, **e.kwargs)

class EntryArchiveIndexView(ArchiveIndexView):
    date_field = 'pub_date'
    allow_empty = True
    paginate_by = 15
    template_name_field = 'template'
    queryset = Entry.objects.all()

    def get_dated_items(self):
        items = super(EntryArchiveIndexView, self).get_dated_items()
        return items

    def get_dated_queryset(self, **lookup):
        queryset = super(EntryArchiveIndexView, self).get_dated_queryset(**lookup)
        queryset = filter_queryset_language(self.request, queryset)
        return queryset.published()


class BlogArchiveMixin(object):
    model = Entry
    date_field = 'pub_date'
    make_object_list = True
    allow_empty = True
    month_format = '%m'

    def get_queryset(self):
        queryset = super(BlogArchiveMixin, self).get_queryset().published()
        if queryset:
            set_language_changer(self.request, queryset[0].language_changer)
        return queryset


class BlogYearArchiveView(BlogArchiveMixin, YearArchiveView):
    template_name = 'cmsplugin_blog/entry_archive_year.html'


class BlogMonthArchiveView(BlogArchiveMixin, MonthArchiveView):
    template_name = 'cmsplugin_blog/entry_archive_month.html'


class BlogDayArchiveView(BlogArchiveMixin, DayArchiveView):
    template_name = 'cmsplugin_blog/entry_archive_day.html'


class BlogAuthorArchiveView(ListView):
    model = Entry
    allow_empty = True,
    slug_field = 'entrytitle__author__username'
    template_name = 'cmsplugin_blog/entry_author_list.html',

    def get_queryset(self):
        author = self.kwargs['slug']
        queryset = super(BlogAuthorArchiveView, self).get_queryset().published().filter(entrytitle__author__username=author)
        if queryset:
            set_language_changer(self.request, queryset[0].language_changer)
        return queryset

    def get_context_data(self, **kwargs):
        return super(BlogAuthorArchiveView,
                     self).get_context_data(author=self.kwargs['slug'], **kwargs)


class TaggedObjectList(ListView):
    queryset_or_model = None
    tag = None
    related_tags = False
    related_tag_counts = True

    def get(self, request, *args, **kwargs):
        tag = self.tag or kwargs.get('tag')
        self.tag_instance = get_tag(tag)
        return super(TaggedObjectList, self).get(request, *args, **kwargs)

    def get_queryset(self):
        if hasattr(self.queryset_or_model, 'objects'):
            return self.queryset_or_model.objects.all()
        return self.queryset_or_model

    def get_context_data(self, **kwargs):
        tag = self.tag or self.kwargs['tag']
        self.tag_instance = get_tag(self.tag or self.kwargs['tag'])
        if self.tag_instance is None:
            raise Http404(_('No Tag found matching "%s".') % tag)
        context = super(TaggedObjectList, self).get_context_data(**kwargs)
        if self.related_tags:
            context['related_tags'] = Tag.objects.related_for_model(
                self.tag_instance,
                context['queryset'],
                counts=self.related_tag_counts,
            )
        return context

    def get_queryset(self):
        return TaggedItem.objects.get_by_model(self.queryset_or_model, self.tag_instance)


class BlogTaggedArchiveView(TaggedObjectList):
    template_name = 'cmsplugin_blog/entry_list.html'
    queryset_or_model = Entry.objects.all()

    def get_queryset(self):
        queryset = super(BlogTaggedArchiveView, self).get_queryset().published()
        if queryset:
            set_language_changer(self.request, queryset[0].language_changer)
        return queryset
