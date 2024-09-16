import django_filters
from django_filters import rest_framework as filters

from timetrials.models.categories import CategoryChoices, eligible_categories


class TimeTrialsFilterBackend(filters.DjangoFilterBackend):
    """Allow filtering queryset after filterset."""

    def filter_queryset(self, request, queryset, view, no_post=False):
        qs = super().filter_queryset(request, queryset, view)

        is_lap_as_null_bool = getattr(view, 'is_lap_as_null_bool', False)
        if is_lap_as_null_bool:
            if 'is_lap' not in request.query_params:
                qs = qs.filter(is_lap=None)

        do_not_expand_category = getattr(view, 'do_not_expand_category', False)
        if do_not_expand_category:
            qs = qs.filter(category=request.query_params.get('category'))

        post_filter_queryset = getattr(view, 'post_filter_queryset', None)
        if post_filter_queryset:
            return post_filter_queryset(qs)

        return qs


class CategoryFilter(django_filters.FilterSet):
    """Filter by category by properly following fallthrough rules as well as by course or lap."""

    region = django_filters.CharFilter(method='region_filter')

    category = django_filters.ChoiceFilter(
        choices=CategoryChoices.choices,
        method='category_filter',
        required=True,
    )

    is_lap = django_filters.BooleanFilter()

    def region_filter(self, queryset, name: str, value: str):
        return queryset

    def category_filter(self, queryset, name: str, value: CategoryChoices):
        """Filter for all eligible categories for a given category."""
        return queryset.filter(**{
            f'{name}__in': eligible_categories(value),
        })


class PlayerStatsFilter(CategoryFilter):
    metric = django_filters.OrderingFilter(
        fields={
            'total_rank': 'total_rank',
            'total_standard': 'total_standard',
            '-total_record_ratio': 'total_record_ratio',
            'total_score': 'total_score',
        },
        choices=(
            ('total_rank', "Average finish"),
            ('total_standard', "Average standard"),
            ('total_record_ratio', "Personal record to world record ratio"),
            ('total_score', "Total time"),
        ),
        required=True
    )
