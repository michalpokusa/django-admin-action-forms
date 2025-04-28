// Modified `contrib/admin/static/admin/js/autocomplete.js`
// Adds `admin_site` and `action_name` to the AJAX request data and changes the meaning of `field_name` to be the
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
                            admin_site: element.dataset.adminSite,
                            app_label: element.dataset.appLabel,
                            model_name: element.dataset.modelName,
                            action_name: element.dataset.actionName,
                            inline_name: element.dataset.inlineName,
                            field_name: element.dataset.fieldName,
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
