// Modified `contrib/admin/static/admin/js/autocomplete.js`
// Adds `action_name` to the AJAX request data and changes the meaning of `field_name` to be the
// ActionForm field that is being autocompleted.
// When autocomplete is used inside inline, `field_name` is not enough and `inline_name` is needed to identify the correct field
// and not use the field from the ActionForm that has the same name.

'use strict';
{
    const $ = django.jQuery;

    $.fn.djangoAdminActionFormSelect2 = function () {
        $.each(this, function (i, element) {
            $(element).select2({
                ajax: {
                    data: (params) => {
                        return {
                            term: params.term,
                            page: params.page,
                            action_name: element.dataset.actionName,
                            field_name: element.dataset.fieldName,
                            inline_name: element.dataset.inlineName,
                        };
                    }
                }
            });
        });
        return this;
    };

    $(function () {
        // Initialize all autocomplete widgets except the one in the template
        // form used when a new formset is added.
        $('.admin-actionform-autocomplete').not('[name*=__prefix__]').djangoAdminActionFormSelect2();
    });

    // Django 4.1.x and above
    document.addEventListener('formset:added', (event) => {
        $(event.target).find('.admin-actionform-autocomplete').djangoAdminActionFormSelect2();
    });

    // Django 3.2.x
    $(document).on('formset:added', (function () {
        return function (event, $newFormset) {
            return $newFormset.find('.admin-actionform-autocomplete').djangoAdminActionFormSelect2();
        };
    })(this));
}
