from __future__ import absolute_import

from django.contrib.formtools.wizard.views import SessionWizardView
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _

from common.views import MayanPermissionCheckMixin
from documents.forms import DocumentTypeSelectForm
from documents.permissions import PERMISSION_DOCUMENT_CREATE
from metadata.forms import MetadataFormSet, MetadataSelectionForm


class DocumentCreateWizard(MayanPermissionCheckMixin, SessionWizardView):
    form_list = [DocumentTypeSelectForm, MetadataSelectionForm, MetadataFormSet]
    template_name = 'main/generic_wizard.html'
    extra_context = {}
    permissions_required = [PERMISSION_DOCUMENT_CREATE]

    @staticmethod
    def has_metadata_types(wizard):
        # Skip the 3rd step if no metadata types or sets are selected
        try:
            return wizard.get_cleaned_data_for_step('1')['metadata_types']
        except TypeError:
            return False

    def generate_metadata_initial_values(self):
        initial = []

        for metadata_type in self.get_cleaned_data_for_step('1')['metadata_types']:
            initial.append({
                'metadata_type': metadata_type,
            })

        return initial

    def __init__(self, *args, **kwargs):
        super(DocumentCreateWizard, self).__init__(*args, **kwargs)

        self.condition_dict = {'2': DocumentCreateWizard.has_metadata_types}

        self.step_titles = [
            _(u'Step 1 of 3: Document type'),
            _(u'Step 2 of 3: Metadata selection'),
            _(u'Step 3 of 3: Document metadata'),
        ]

    def get_form_initial(self, step):
        if step == '1':
            try:
                return {'document_type': self.get_cleaned_data_for_step('0')['document_type']}
            except TypeError:
                return {}
        elif step == '2':
            return self.generate_metadata_initial_values()

        return self.initial_dict.get(step, {})

    def get_context_data(self, form, **kwargs):
        context = super(DocumentCreateWizard, self).get_context_data(form=form, **kwargs)
        context.update({
            'step_title': self.step_titles[self.steps.step0],
            'submit_label': _(u'Next step'),
            'submit_icon_famfam': 'arrow_right',
        })
        return context

    def done(self, form_list):
        query_dict = {}
        try:
            query_dict['document_type_id'] = self.get_cleaned_data_for_step('0')['document_type'].pk
        except AttributeError:
            pass

        try:
            for identifier, metadata in enumerate(self.get_cleaned_data_for_step('2')):
                query_dict['metadata%s_id' % identifier] = metadata['id']
                query_dict['metadata%s_value' % identifier] = metadata['value']
        except TypeError:
            pass

        url = '?'.join([reverse('sources:upload_interactive'), urlencode(query_dict, doseq=True)])
        return HttpResponseRedirect(url)
