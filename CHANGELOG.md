# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [2.2.0] - 2025-08-28

### Added

- Support for `objects_summary` in `ActionForm.Meta`

## [2.1.0] - 2025-04-29

### Added

- Support for `inlines` in `ActionForm.Meta`
- Support for `radio_fields` in `ActionForm.Meta`

## [2.0.0] - 2025-04-14

### Added

- `AdminActionFormsMixin` class that needs to be inherited in `ModelAdmin` classes to use `@action_with_form` decorator
- Template used by `ActionForm` can now be overridden
- `ActionForm.action_form_view()` method can be overridden e.g. for providing extra context to the template

### Changed

- `ActionForm.__post_init__` method was removed in favor of `ActionForm.__init__` method

## [1.3.0] - 2024-12-01

### Fixed

- Error when `"index"` key was missing from `request.POST`

### Added

- CSS variables for action form button colors

## [1.2.4] - 2024-11-25

### Fixed

- German translation for "Cancel"

## [1.2.3] - 2024-10-05

### Fixed

- Widgets for `filter_horizontal` and `filter_vertical` were missing the help text for selecting multiple items

## [1.2.2] - 2024-10-01

### Fixed

- `@action_with_form` and `@no_queryset_action` can be used in any order

## [1.2.1] - 2024-09-30

## [1.2.0] - 2024-09-24

### Fixed

- Files were not passed to the action
- In templates, `extrahead` block was being replaced instead of extended
- `limit_choices_to` was not considered on `ModelChoiceField`s

### Added

- Compatibility with `django-autocomplete-light` package
- `confirm_button_text` and `cancel_button_text` in `ActionForm.Meta`
- Support for grouped fields in `fields`
- `ActionForm.__post_init__` method for modyfying form after initialization

## [1.1.1] - 2024-09-11

### Fixed

- Exception when action was not a `ModelAdmin` method

## [1.1.0] - 2024-08-28

### Added

- Compatibility with `django-no-queryset-admin-actions` package
- `get_fields` and `get_fieldsets` methods in `ActionForm.Meta`
- Support for grouped fields in `fields`

## [1.0.0] - 2024-08-02


[2.2.0]: https://github.com/michalpokusa/django-admin-action-forms/compare/2.1.0...2.2.0
[2.1.0]: https://github.com/michalpokusa/django-admin-action-forms/compare/2.0.0...2.1.0
[2.0.0]: https://github.com/michalpokusa/django-admin-action-forms/compare/1.3.0...2.0.0
[1.3.0]: https://github.com/michalpokusa/django-admin-action-forms/compare/1.2.4...1.3.0
[1.2.4]: https://github.com/michalpokusa/django-admin-action-forms/compare/1.2.3...1.2.4
[1.2.3]: https://github.com/michalpokusa/django-admin-action-forms/compare/1.2.2...1.2.3
[1.2.2]: https://github.com/michalpokusa/django-admin-action-forms/compare/1.2.1...1.2.2
[1.2.1]: https://github.com/michalpokusa/django-admin-action-forms/compare/1.2.0...1.2.1
[1.2.0]: https://github.com/michalpokusa/django-admin-action-forms/compare/1.1.1...1.2.0
[1.1.1]: https://github.com/michalpokusa/django-admin-action-forms/compare/1.1.0...1.1.1
[1.1.0]: https://github.com/michalpokusa/django-admin-action-forms/compare/1.0.0...1.1.0
[1.0.0]: https://github.com/michalpokusa/django-admin-action-forms/releases/tag/1.0.0
