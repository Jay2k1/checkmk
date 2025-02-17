# generated by datamodel-codegen:
#   filename:  vue_formspec_components.json
#   timestamp: 2024-07-11T13:36:17+00:00

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Union


@dataclass(kw_only=True)
class IsInteger:
    type: str = "is_integer"
    error_message: Optional[str] = None


@dataclass(kw_only=True)
class IsFloat:
    type: str = "is_float"
    error_message: Optional[str] = None


@dataclass(kw_only=True)
class LengthInRange:
    type: str = "length_in_range"
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    error_message: Optional[str] = None


@dataclass(kw_only=True)
class NumberInRange:
    type: str = "number_in_range"
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    error_message: Optional[str] = None


Validators = Union[IsInteger, IsFloat, NumberInRange, LengthInRange]


@dataclass(kw_only=True)
class SingleChoiceElement:
    name: str
    title: str


@dataclass(kw_only=True)
class ValidationMessage:
    location: list[str]
    message: str
    invalid_value: Any


@dataclass(kw_only=True)
class FormSpec:
    type: str
    title: str
    help: str
    validators: list[Validators] = field(default_factory=lambda: [])


@dataclass(kw_only=True)
class Integer(FormSpec):
    input_hint: Any
    type: str = "integer"
    label: Optional[str] = None
    unit: Optional[str] = None


@dataclass(kw_only=True)
class Float(FormSpec):
    input_hint: Any
    type: str = "float"
    label: Optional[str] = None
    unit: Optional[str] = None


@dataclass(kw_only=True)
class LegacyValuespec(FormSpec):
    html: str
    varprefix: str
    type: str = "legacy_valuespec"


@dataclass(kw_only=True)
class String(FormSpec):
    input_hint: Any
    type: str = "string"
    placeholder: Optional[str] = None


@dataclass(kw_only=True)
class List(FormSpec):
    element_template: FormSpec
    element_default_value: Any
    editable_order: bool
    add_element_label: str
    remove_element_label: str
    no_element_label: str
    type: str = "list"


@dataclass(kw_only=True)
class DictionaryElement:
    ident: str
    required: bool
    default_value: Any
    parameter_form: FormSpec


@dataclass(kw_only=True)
class Dictionary(FormSpec):
    type: str = "dictionary"
    elements: list[DictionaryElement] = field(default_factory=lambda: [])


@dataclass(kw_only=True)
class SingleChoice(FormSpec):
    frozen: bool
    input_hint: Any
    type: str = "single_choice"
    elements: list[SingleChoiceElement] = field(default_factory=lambda: [])
    no_elements_text: Optional[str] = None
    label: Optional[str] = None


@dataclass(kw_only=True)
class CascadingSingleChoiceElement:
    name: str
    title: str
    default_value: Any
    parameter_form: FormSpec


@dataclass(kw_only=True)
class CascadingSingleChoice(FormSpec):
    input_hint: Any
    type: str = "cascading_single_choice"
    elements: list[CascadingSingleChoiceElement] = field(default_factory=lambda: [])
    no_elements_text: Optional[str] = None
    label: Optional[str] = None


Components = Union[
    Integer,
    Float,
    String,
    Dictionary,
    List,
    LegacyValuespec,
    SingleChoice,
    CascadingSingleChoice,
]


@dataclass(kw_only=True)
class VueFormspecComponents:
    components: Optional[Components] = None
    validation_message: Optional[ValidationMessage] = None
