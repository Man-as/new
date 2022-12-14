from django.db.models.signals import pre_save
from django.dispatch import receiver
from sequences import get_next_value
from flow_system.models import FlowConfig

# from candidates.models import Candidate
# from interviews.models import Interview
# from offers.models import Offer
from organizations.models import Organization

# from submissions.models import Submission

program_id_sequence_key_models = [
    # Interview, Offer, Submission
]


#@receiver(pre_save, sender=Candidate)
# @receiver(pre_save, sender=Interview)
# @receiver(pre_save, sender=Offer)
# @receiver(pre_save, sender=Submission)
@receiver(pre_save, sender=Organization)
@receiver(pre_save, sender=FlowConfig)
def generate_unique_id(sender, instance=None, created=False, **kwargs):
    if instance._state.adding:
        sequence_key = sender.sequence_key
        prefix = sender.unique_id_prefix
        if sender in program_id_sequence_key_models:
            sequence_key = sequence_key.replace('<PROGRAM_ID>', str(
                instance.program_id))
        unique_id = "{}-{:0>6}".format(prefix, get_next_value(sequence_key))
        if prefix != FlowConfig.unique_id_prefix:
            if prefix != 'ORG':
                instance.unique_id = unique_id
            else:
                instance.code = unique_id
        else:
            unique_id = "{}-{:0>3}".format(
                prefix, get_next_value(sequence_key))
            instance.code = '-'.join([instance.program.code, unique_id])
