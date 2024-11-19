from django.db.models import QuerySet

from drf_spectacular.utils import extend_schema, OpenApiParameter

from rest_framework.exceptions import ValidationError

from timetrials.models.categories import CategoryChoices
from timetrials.models.players import PlayerAwardTypeChoices
from timetrials.models.regions import Region, RegionTypeChoices
from timetrials.models.stats.region_stats import TopScoreCountChoices
from timetrials.serializers import CategoryField, TopScoreCountField


class FilterMixin:

    def filter(self, queryset: QuerySet) -> QuerySet:
        for filter_field in self.filter_fields:
            if not filter_field.auto:
                continue

            if not filter_field.required and not filter_field.has_value(self.request):
                continue

            queryset = filter_field.filter(self.request, queryset)

        return queryset

    def get_filter_value(self, filter_class):
        for filter_field in self.filter_fields:
            if isinstance(filter_field, filter_class):
                return filter_field.get_filter_value(self.request)

        raise TypeError(f"No filter fields of type {filter_class.__name__}")

    def limit(self, queryset: QuerySet) -> QuerySet:
        for filter_field in self.filter_fields:
            if isinstance(filter_field, LimitFilter):
                return filter_field.filter(self.request, queryset)

        raise TypeError("No LimitFilter in filter fields")


def extend_schema_with_filters(view):
    return extend_schema(
        parameters=list(map(lambda field: field.open_api_param, view.filter_fields))
    )(view)


class FilterBase:
    default_error_messages = {
        'missing_required_param': "Required parameter '%s' is missing from query string.",
        'invalid_value': "Invalid value for parameter '%s': %s",
    }

    def __init__(self, *, field_name: str, request_field: str, auto=False, required=False):
        """
        Parameters
        ----------
        field_name : str
            The name of the field on the model to apply the filter to
        request_field : str
            The name of the query param of the request to get the filter value from
        auto : bool
            Whether this filter should be applied by FilterMixin.filter
        required : bool
            Whether this filter is required to be present in the query params
        """
        self.field_name = field_name
        self.request_field = request_field
        self.auto = auto
        self.required = required

    def validation_error(self, code: str, *args):
        """Raise a `ValidationError`."""
        if code in self.default_error_messages:
            detail = self.default_error_messages[code] % args
        else:
            detail = code

        raise ValidationError(detail=detail, code=code)

    def validate_filter_value(self, value: str):
        """Validate filter value and convert to expected type."""
        return value

    def has_value(self, request):
        """Return whether the filter is present in the query params of the request."""
        return self.request_field in request.query_params

    def get_filter_value(self, request):
        """Get the filter value from the query params of the request."""
        if not self.has_value(request):
            if self.required:
                raise self.validation_error('missing_required_param', self.request_field)
            else:
                return None

        value = request.query_params[self.request_field]

        return self.validate_filter_value(value)

    def filter(self, request, queryset: QuerySet) -> QuerySet:
        """Filter the queryset."""
        return queryset.filter(**{
            self.field_name: self.get_filter_value(request),
        })

    @property
    def open_api_param(self) -> OpenApiParameter:
        """The OpenAPI parameter schema definition."""
        raise NotImplementedError


class OrderingFilterBase(FilterBase):

    def __init__(self, *,
                 fields: dict[str, str],
                 request_field: str,
                 auto=True,
                 required=True):
        """
        Parameters
        ----------
        fields : dict of {str: str}
            Mapping of query param value to model field name to order by
        request_field : str
            The name of the query param of the request to get the filter value from
        auto : bool
            Whether this filter should be applied by FilterMixin.filter
        required : bool
            Whether this filter is required to be present in the query params
        """
        super().__init__(
            field_name='',
            request_field=request_field,
            auto=auto,
            required=required
        )

        self.fields = fields

    def validate_filter_value(self, value: str):
        if value not in self.fields:
            self.validation_error('invalid_value', self.request_field, value)

        return self.fields[value]

    def filter(self, request, queryset: QuerySet) -> QuerySet:
        """Sort the queryset."""
        return queryset.order_by(self.get_filter_value(request))


class LimitFilter(FilterBase):

    def __init__(self, *,
                 request_field='limit',
                 min=1,
                 max=None,
                 default=None,
                 required=True):
        """
        Parameters
        ----------
        request_field : str
            The name of the query param of the request to get the filter value from
        min : int
            The minimum value for this field
        max : int
            The maximum value for this field, or None for no limit
        default : int
            The default value for this field if not present in the query params
        required : bool
            Whether this filter is required to be present in the query params
        """
        super().__init__(
            field_name='',
            request_field=request_field,
            auto=False,
            required=required
        )

        self.min = min
        self.max = max
        self.default = default

    def validate_filter_value(self, value: str):
        try:
            limit = int(value)
        except ValueError:
            self.validation_error('invalid_value', self.request_field, value)

        if limit < self.min or limit > self.max:
            self.validation_error('invalid_value', self.request_field, value)

        return limit

    def filter(self, request, queryset: QuerySet) -> QuerySet:
        """Limit the queryset."""
        limit = self.get_filter_value(request) or self.default
        if limit is None:
            return queryset
        return queryset[:limit]

    @property
    def open_api_param(self) -> OpenApiParameter:
        return OpenApiParameter(
            self.request_field,
            type=int,
            required=self.required,
            allow_blank=False,
        )


class CategoryFilter(FilterBase):

    def __init__(self, *,
                 expand=True,
                 field_name='category',
                 request_field='category',
                 auto=True,
                 required=True):
        """
        Parameters
        ----------
        expand : bool
            Whether to also filter for more restricted categories (e.g., include `NON_SHORTCUT`
            with `SHORTCUT`)
        field_name : str
            The name of the field on the model to apply the filter to
        request_field : str
            The name of the query param of the request to get the filter value from
        auto : bool
            Whether this filter should be applied by FilterMixin.filter
        required : bool
            Whether this filter is required to be present in the query params
        """
        super().__init__(
            field_name=field_name,
            request_field=request_field,
            auto=auto,
            required=required
        )

        self.expand = expand

    def validate_filter_value(self, value: str):
        category = CategoryField().to_internal_value(value)

        if category not in CategoryChoices.values:
            self.validation_error('invalid_value', self.request_field, value)

        return category

    def filter(self, request, queryset: QuerySet) -> QuerySet:
        if self.expand:
            return queryset.filter(**{
                f'{self.field_name}__lte': self.get_filter_value(request)
            })

        else:
            return super().filter(request, queryset)

    @property
    def open_api_param(self) -> OpenApiParameter:
        return OpenApiParameter(
            self.request_field,
            type=str,
            enum=CategoryField.values(),
            required=self.required,
            allow_blank=False,
        )


class LapModeFilter(FilterBase):

    def __init__(self, *,
                 allow_overall=False,
                 field_name='is_lap',
                 request_field='lap_mode',
                 auto=True,
                 required=True):
        """
        Parameters
        ----------
        allow_overall : bool
            Whether to allow 'overall' as param value to filter for `None`
        field_name : str
            The name of the field on the model to apply the filter to
        request_field : str
            The name of the query param of the request to get the filter value from
        auto : bool
            Whether this filter should be applied by FilterMixin.filter
        required : bool
            Whether this filter is required to be present in the query params
        """
        super().__init__(
            field_name=field_name,
            request_field=request_field,
            auto=auto,
            required=required
        )

        self.choices = {
            'course': False,
            'lap': True
        }
        if allow_overall:
            self.choices['overall'] = None

    def validate_filter_value(self, value: str):
        if value not in self.choices:
            self.validation_error('invalid_value', self.request_field, value)

        return self.choices[value]

    @property
    def open_api_param(self) -> OpenApiParameter:
        return OpenApiParameter(
            self.request_field,
            type=str,
            enum=self.choices.keys(),
            required=self.required,
            allow_blank=False,
        )


class RegionFilter(FilterBase):

    def __init__(self, *,
                 expand=True,
                 ranked_only=False,
                 field_name='region',
                 request_field='region',
                 auto=True,
                 required=True):
        """
        Parameters
        ----------
        ranked_only : bool
            Whether to only allow filtering by ranked regions
        field_name : str
            The name of the field on the model to apply the filter to
        request_field : str
            The name of the query param of the request to get the filter value from
        auto : bool
            Whether this filter should be applied by FilterMixin.filter
        required : bool
            Whether this filter is required to be present in the query params
        """
        super().__init__(
            field_name=field_name,
            request_field=request_field,
            auto=auto,
            required=required
        )

        self.expand = expand
        self.ranked_only = ranked_only

    def validate_filter_value(self, value: str):
        try:
            region_id = int(value)
        except ValueError:
            self.validation_error('invalid_value', self.request_field, value)

        region = Region.objects.filter(id=region_id)

        if self.ranked_only:
            region = region.filter(is_ranked=True)

        if not region.exists():
            self.validation_error('invalid_value', self.request_field, value)

        return region.first()

    def filter(self, request, queryset: QuerySet) -> QuerySet:
        if self.expand:
            return queryset.filter(**{
                f'{self.field_name}__in': (
                    self.get_filter_value(request).descendants(
                        include_self=True
                    ).values_list('pk', flat=True)
                ),
            })

        else:
            return super().filter(request, queryset)

    @property
    def open_api_param(self) -> OpenApiParameter:
        return OpenApiParameter(
            self.request_field,
            type=int,
            required=self.required,
            allow_blank=False,
        )


class RegionTypeFilter(FilterBase):

    def __init__(self, *,
                 field_name='type',
                 request_field='type',
                 auto=True,
                 required=True):
        """
        Parameters
        ----------
        field_name : str
            The name of the field on the model to apply the filter to
        request_field : str
            The name of the query param of the request to get the filter value from
        auto : bool
            Whether this filter should be applied by FilterMixin.filter
        required : bool
            Whether this filter is required to be present in the query params
        """
        super().__init__(
            field_name=field_name,
            request_field=request_field,
            auto=auto,
            required=required
        )

        self.choices = [
            RegionTypeChoices.CONTINENT,
            RegionTypeChoices.COUNTRY,
            RegionTypeChoices.SUBNATIONAL,
        ]

    @property
    def open_api_param(self) -> OpenApiParameter:
        return OpenApiParameter(
            self.request_field,
            type=str,
            enum=self.choices,
            required=self.required,
            allow_blank=False,
        )


class RegionStatsTopScoreCountFilter(FilterBase):

    def __init__(self, *,
                 field_name='top_score_count',
                 request_field='top',
                 auto=True,
                 required=True):
        """
        Parameters
        ----------
        field_name : str
            The name of the field on the model to apply the filter to
        request_field : str
            The name of the query param of the request to get the filter value from
        auto : bool
            Whether this filter should be applied by FilterMixin.filter
        required : bool
            Whether this filter is required to be present in the query params
        """
        super().__init__(
            field_name=field_name,
            request_field=request_field,
            auto=auto,
            required=required
        )

    def validate_filter_value(self, value: str):
        top_score_count = TopScoreCountField().to_internal_value(value)

        if top_score_count not in TopScoreCountChoices.values:
            self.validation_error('invalid_value', self.request_field, value)

        return top_score_count

    @property
    def open_api_param(self) -> OpenApiParameter:
        return OpenApiParameter(
            self.request_field,
            type=str,
            enum=TopScoreCountField.values(),
            required=self.required,
            allow_blank=False,
        )


class PlayerAwardTypeFilter(FilterBase):

    def __init__(self, *,
                 field_name='type',
                 request_field='type',
                 auto=True,
                 required=True):
        """
        Parameters
        ----------
        field_name : str
            The name of the field on the model to apply the filter to
        request_field : str
            The name of the query param of the request to get the filter value from
        auto : bool
            Whether this filter should be applied by FilterMixin.filter
        required : bool
            Whether this filter is required to be present in the query params
        """
        super().__init__(
            field_name=field_name,
            request_field=request_field,
            auto=auto,
            required=required
        )

    def validate_filter_value(self, value: str):
        if value not in PlayerAwardTypeChoices.values:
            self.validation_error('invalid_value', self.request_field, value)

        return value

    @property
    def open_api_param(self) -> OpenApiParameter:
        return OpenApiParameter(
            self.request_field,
            type=str,
            enum=PlayerAwardTypeChoices.values,
            required=self.required,
            allow_blank=False,
        )


class MetricOrderingFilter(OrderingFilterBase):

    def __init__(self, *,
                 request_field='metric',
                 auto=True,
                 required=True):
        super().__init__(
            fields={
                'total_rank': 'total_rank',
                'total_score': 'total_score',
                'total_standard': 'total_standard',
                'total_record_ratio': '-total_record_ratio',
                'total_records': 'total_records',
                'leaderboard_points': '-leaderboard_points',
            },
            request_field=request_field,
            auto=auto,
            required=required,
        )

    @property
    def open_api_param(self) -> OpenApiParameter:
        return OpenApiParameter(
            self.request_field,
            type=str,
            enum=self.fields.keys(),
            required=self.required,
            allow_blank=False,
        )
