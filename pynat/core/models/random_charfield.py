import string

from django.conf import settings
from django.db.models import CharField
from django.db.models import Q
from django.db.models import UniqueConstraint
from django.utils.crypto import get_random_string

MAX_UNIQUE_QUERY_ATTEMPTS = getattr(
    settings,
    "EXTENSIONS_MAX_UNIQUE_QUERY_ATTEMPTS",
    100,
)


class RandomCharField(CharField):
    """
    NOTE: Ripped from django extensions

    length
        Specifies the length of the field

    Optional arguments:

    unique
        If set to True, duplicate entries are not allowed (default: False)

    lowercase
        If set to True, lowercase the alpha characters (default: False)

    uppercase
        If set to True, uppercase the alpha characters (default: False)

    include_alpha
        If set to True, include alpha characters (default: True)

    include_digits
        If set to True, include digit characters (default: True)

    include_punctuation
        If set to True, include punctuation characters (default: False)

    keep_default
        If set to True, keeps the default initialization value (default: False)
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("blank", True)
        kwargs.setdefault("editable", False)

        self.length = kwargs.pop("length", None)
        if self.length is None:
            raise ValueError("missing 'length' argument")
        kwargs["max_length"] = self.length

        self.lowercase = kwargs.pop("lowercase", False)
        self.check_is_bool("lowercase")
        self.uppercase = kwargs.pop("uppercase", False)
        self.check_is_bool("uppercase")
        if self.uppercase and self.lowercase:
            raise ValueError("cannot pass both uppercase AND lowercase arguments")
        self.include_digits = kwargs.pop("include_digits", True)
        self.check_is_bool("include_digits")
        self.include_alpha = kwargs.pop("include_alpha", True)
        self.check_is_bool("include_alpha")
        self.include_punctuation = kwargs.pop("include_punctuation", False)
        self.keep_default = kwargs.pop("keep_default", False)
        self.check_is_bool("include_punctuation")
        self.max_unique_query_attempts = kwargs.pop(
            "max_unique_query_attempts",
            MAX_UNIQUE_QUERY_ATTEMPTS,
        )

        # Set unique=False unless it's been set manually.
        if "unique" not in kwargs:
            kwargs["unique"] = False

        super().__init__(*args, **kwargs)

    def random_char_generator(self, chars):
        for _ in range(self.max_unique_query_attempts):
            yield "".join(get_random_string(self.length, chars))
        raise RuntimeError(
            f"max random character attempts exceeded ({self.max_unique_query_attempts})",
        )

    def in_unique_together(self, model_instance):
        for params in model_instance._meta.unique_together:
            if self.attname in params:
                return True
        return False

    def pre_save(self, model_instance, add):
        if (not add or self.keep_default) and getattr(
            model_instance,
            self.attname,
        ) != "":
            return getattr(model_instance, self.attname)

        population = ""
        if self.include_alpha:
            if self.lowercase:
                population += string.ascii_lowercase
            elif self.uppercase:
                population += string.ascii_uppercase
            else:
                population += string.ascii_letters

        if self.include_digits:
            population += string.digits

        if self.include_punctuation:
            population += string.punctuation

        random_chars = self.random_char_generator(population)
        if not self.unique and not self.in_unique_together(model_instance):
            new = next(random_chars)
            setattr(model_instance, self.attname, new)
            return new

        return self.find_unique(
            model_instance,
            model_instance._meta.get_field(self.attname),
            random_chars,
        )

    def internal_type(self):
        return "CharField"

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["length"] = self.length
        del kwargs["max_length"]

        optional_params = [
            ("lowercase", self.lowercase, True),
            ("uppercase", self.uppercase, True),
            ("include_alpha", self.include_alpha, False),
            ("include_digits", self.include_digits, False),
            ("include_punctuation", self.include_punctuation, True),
            ("unique", self.unique, True),
        ]

        kwargs |= {
            name: val for name, val, trigger in optional_params if val is trigger
        }

        return name, path, args, kwargs

    def check_is_bool(self, attrname):
        if not isinstance(getattr(self, attrname), bool):
            raise ValueError(f"'{attrname}' argument must be True or False")

    @staticmethod
    def _get_fields(model_cls):
        return [
            (f, f.model if f.model != model_cls else None)
            for f in model_cls._meta.get_fields()
            if not f.is_relation or f.one_to_one or (f.many_to_one and f.related_model)
        ]

    def get_queryset(self, model_cls, slug_field):
        for field, model in self._get_fields(model_cls):
            if model and field == slug_field:
                return model._default_manager.all()
        return model_cls._default_manager.all()

    def find_unique(self, model_instance, field, iterator, *args):
        # exclude the current model instance from the queryset used in finding
        # next valid hash
        queryset = self.get_queryset(model_instance.__class__, field)
        if model_instance.pk:
            queryset = queryset.exclude(pk=model_instance.pk)

        # form a kwarg dict used to implement any unique_together constraints
        kwargs = {}
        for params in model_instance._meta.unique_together:
            if self.attname in params:
                for param in params:
                    kwargs[param] = getattr(model_instance, param, None)

        # for support django 2.2+
        query = Q()
        constraints = getattr(model_instance._meta, "constraints", None)
        if constraints:
            unique_constraints = filter(
                lambda c: isinstance(c, UniqueConstraint),
                constraints,
            )
            for unique_constraint in unique_constraints:
                if self.attname in unique_constraint.fields:
                    condition = {
                        field: getattr(model_instance, field, None)
                        for field in unique_constraint.fields
                        if field != self.attname
                    }
                    query &= Q(**condition)

        new = next(iterator)
        kwargs[self.attname] = new
        while not new or queryset.filter(query, **kwargs):
            new = next(iterator)
            kwargs[self.attname] = new
        setattr(model_instance, self.attname, new)
        return new
