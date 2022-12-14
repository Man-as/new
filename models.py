from django.db import models

from common_utils.models import DefaultModel, UUIDPKModel
from custom_fields.constants import ENTITY_TYPE_CHOICES
from modules.models import Module
from programs.models import OrgHierarchy, Program

FIELD_TYPE_CHOICES = [
    ('NUMBER', 'NUMBER'), ('STRING', 'STRING'), ('DROPDOWN', 'DROPDOWN'),
    ('DATE', 'DATE')]

FLOW_TYPE_CHOICES = [
    ('APPROVAL', 'APPROVAL'), ('REVIEW', 'REVIEW')]


class DataSource(UUIDPKModel):
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=255, unique=True)
    api_url = models.CharField(max_length=255, blank=True, null=True)
    db_model = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.slug


class FieldOperator(UUIDPKModel):
    sign = models.CharField(max_length=50)
    eval_text = models.CharField(max_length=50, unique=True)
    is_seperator = models.BooleanField(default=False)

    def __str__(self):
        return self.sign


class FieldTypeOperatorMap(models.Model):
    field_type = models.CharField(primary_key=True, max_length=255)
    field_operators = models.ManyToManyField(
        FieldOperator, related_name='field_type_maps', blank=True)

    def __str__(self):
        return self.pk


class FlowSystemField(UUIDPKModel):
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=255, unique=True)
    field_type = models.ForeignKey(
        FieldTypeOperatorMap, related_name='fields', on_delete=models.CASCADE)
    data_source = models.ForeignKey(
        DataSource, related_name='fields', on_delete=models.CASCADE)
    field_meta = models.JSONField()

    def __str__(self):
        return self.name


class FlowSystemSchema(UUIDPKModel):
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.slug


class FieldConfig(UUIDPKModel):
    name = models.CharField(max_length=100)
    parent_config = models.ForeignKey(
        "self", on_delete=models.CASCADE, related_name="children_configs",
        blank=True, null=True)
    slug = models.CharField(max_length=255, unique=True)
    schema = models.ForeignKey(
        FlowSystemSchema, related_name='field_configs',
        on_delete=models.CASCADE)
    field = models.ForeignKey(
        FlowSystemField, related_name='field_configs',
        on_delete=models.CASCADE)
    placement_order = models.IntegerField()
    nest_level = models.IntegerField()
    config = models.JSONField()

    class Meta:
        unique_together = (
            'schema', 'field', 'placement_order', 'nest_level')

    def __str__(self):
        return self.slug


class RecipientType(UUIDPKModel):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, unique=True)
    is_chain = models.BooleanField(default=False)
    parameter_schema = models.ForeignKey(
        FlowSystemSchema, related_name='recipient_types',
        on_delete=models.CASCADE)
    metadata = models.JSONField()

    def __str__(self):
        return self.slug


class FlowSystemEvent(UUIDPKModel):
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=255, unique=True)
    module = models.ForeignKey(
        Module, related_name='events', on_delete=models.CASCADE)
    event_schema = models.ForeignKey(
        FlowSystemSchema, related_name='flow_events', on_delete=models.CASCADE)
    payload_fetch_template = models.CharField(
        max_length=255, blank=True, null=True)

    def __str__(self):
        return f'{self.module.name}-{self.name}'


class EventRecipientTypeMapping(UUIDPKModel):
    event = models.OneToOneField(
        FlowSystemEvent, related_name='recipient_type_mapping',
        on_delete=models.CASCADE)
    recipient_types = models.ManyToManyField(
        RecipientType, related_name='event_mappings')

    def __str__(self):
        return f'{self.event.module.name}-{self.event.name}'


class FlowConfig(DefaultModel):
    sequence_key = "svms:flow_config"
    unique_id_prefix = FlowConfig.unique_id_prefix

    program = models.ForeignKey(
        Program, related_name='flow_configs', on_delete=models.CASCADE)
    hierarchies = models.ManyToManyField(
        OrgHierarchy, related_name='flow_configs', blank=True)
    event = models.ForeignKey(
        FlowSystemEvent, related_name='flow_configs', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255, blank=True, null=True)
    placement_order = models.IntegerField(default=0)
    flow_type = models.CharField(max_length=20, choices=FLOW_TYPE_CHOICES)


class Level(DefaultModel):
    program = models.ForeignKey(
        Program, related_name='flow_config_levels',
        on_delete=models.CASCADE)
    flow_config = models.ForeignKey(
        FlowConfig, related_name='levels', on_delete=models.CASCADE)
    placement_order = models.IntegerField(default=0)

    class Meta:
        unique_together = ('flow_config', 'placement_order')


class LevelCondition(DefaultModel):
    program = models.ForeignKey(
        Program, related_name='flow_config_level_conditions',
        on_delete=models.CASCADE)
    level = models.ForeignKey(
        Level, related_name='level_conditions', on_delete=models.CASCADE)
    field_config = models.ForeignKey(
        FieldConfig, related_name='level_conditions',
        on_delete=models.CASCADE, blank=True, null=True)
    operator = models.ForeignKey(
        FieldOperator, related_name='level_conditions',
        on_delete=models.CASCADE)
    placement_order = models.IntegerField()
    indent = models.IntegerField(default=0)
    source_field_meta = models.JSONField(blank=True, null=True)
    target_field_value = models.JSONField(blank=True, null=True)

    class Meta:
        unique_together = ('level', 'placement_order')


class LevelRecipientConfig(DefaultModel):
    program = models.ForeignKey(
        Program, related_name='level_recipient_configs',
        on_delete=models.CASCADE)
    level = models.ForeignKey(
        Level, related_name='recipient_configs', on_delete=models.CASCADE)
    recipient_type = models.ForeignKey(
        RecipientType, related_name='level_recipient_configs',
        on_delete=models.CASCADE)
    metadata = models.JSONField()

    class Meta:
        unique_together = ('level', 'recipient_type')


class EntityFlowLevel(DefaultModel):
    program = models.ForeignKey(
        Program, related_name='entity_flow_levels', on_delete=models.CASCADE)
    entity_type = models.CharField(max_length=255, choices=ENTITY_TYPE_CHOICES)
    entity_id = models.UUIDField()
    last_completed_level = models.ForeignKey(
        Level, related_name='last_completed_level', on_delete=models.CASCADE)
    flow_complete = models.BooleanField(default=False)
