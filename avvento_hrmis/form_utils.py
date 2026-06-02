from django import forms


class BootstrapFormMixin:
    """Apply consistent Bootstrap classes and validation state to Django widgets."""

    control_widgets = (
        forms.TextInput,
        forms.EmailInput,
        forms.NumberInput,
        forms.DateInput,
        forms.TimeInput,
        forms.DateTimeInput,
        forms.Textarea,
        forms.PasswordInput,
        forms.FileInput,
    )

    select_widgets = (forms.Select, forms.SelectMultiple)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        bound_errors = self.errors if self.is_bound else {}

        for name, field in self.fields.items():
            widget = field.widget
            attrs = widget.attrs

            if isinstance(widget, forms.CheckboxInput):
                self._add_class(attrs, "form-check-input")
            elif isinstance(widget, self.select_widgets):
                self._remove_class(attrs, "form-control")
                self._add_class(attrs, "form-select")
            elif isinstance(widget, self.control_widgets):
                self._add_class(attrs, "form-control")

            if field.help_text:
                attrs.setdefault("aria-describedby", f"id_{name}_help")

            if name in bound_errors:
                attrs["aria-invalid"] = "true"
                if isinstance(widget, forms.CheckboxInput):
                    self._add_class(attrs, "is-invalid")
                elif not isinstance(widget, forms.RadioSelect):
                    self._add_class(attrs, "is-invalid")

    @staticmethod
    def _add_class(attrs, class_name):
        classes = attrs.get("class", "").split()
        if class_name not in classes:
            classes.append(class_name)
        attrs["class"] = " ".join(classes).strip()

    @staticmethod
    def _remove_class(attrs, class_name):
        classes = [name for name in attrs.get("class", "").split() if name != class_name]
        attrs["class"] = " ".join(classes).strip()
