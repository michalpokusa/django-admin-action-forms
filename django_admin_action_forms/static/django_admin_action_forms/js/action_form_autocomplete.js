// Modified `contrib/admin/static/admin/js/autocomplete.js`
// Adds `admin_site` and `action_name` to the AJAX request data and changes the meaning of `field_name` to be the
// ActionForm field that is being autocompleted.

'use strict';
{
    const $ = django.jQuery;

    $.fn.djangoAdminActionFormSelect2 = function() {
        $.each(this, function(i, element) {
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
                            field_name: element.dataset.fieldName,
                        };
                    }
                }
            });
        });
        return this;
    };

    $(function() {
        // Initialize all autocomplete widgets except the one in the template
        // form used when a new formset is added.
        $('.admin-actionform-autocomplete').not('[name*=__prefix__]').djangoAdminActionFormSelect2();
    });

    document.addEventListener('formset:added', (event) => {
        $(event.target).find('.admin-actionform-autocomplete').djangoAdminActionFormSelect2();
    });
}
