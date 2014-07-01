import datetime
from django import forms
#
# ExtJs Field models
#

#
# MISSING :
#

#'CommaSeparatedIntegerField'    : {'type':'string'}
#'FilePathField'                 : {'type':'string'}
#'ImageField'                    : {'type':'string'}
#'IPAddressField'                : {'type':'string'}
#'NullBooleanField'              : {'type':'bool'}
#'PositiveIntegerField'          : {'type':'int'}
#'PositiveSmallIntegerField'     : {'type':'int'}
#'SmallIntegerField'             : {'type':'int'}

# TYPES: string, bool, int, float, date, array, auto


class Field(object):
    """
    Base class for all fields.
    """

    WIDTH = 200
    COL_WIDTH = None
    TYPE = ''

    def __init__(self, field):
        self.field = field  # django field

    def getEditor(self, initialValue=False, data={}):
        name = self.getName()
        label = name

        if getattr(self.field, 'verbose_name', None):
            label = unicode(self.field.verbose_name)

        # if not self.field.blank:
        # label += '*'
        conf = {
            'xtype': 'textfield',
            'fieldLabel': label,
            'allowBlank': self.allowBlank(),
            'name': name
        }

        if getattr(self.field, 'initial', None):
            conf['value'] = unicode(self.field.initial)

        if initialValue:
            conf['value'] = self.getValue(initialValue)

        if getattr(self.field, 'help_text', None):
            conf['emptyText'] = unicode(getattr(self.field, 'help_text'))

        #conf['tooltip'] = unicode(getattr(self.field, 'help_text'))
        if getattr(self.field, 'max_length', None):
            pixels = self.field.max_length*5
            if pixels < 40:
                pixels = 40
            if pixels > 300:
                pixels = 300
            conf['width'] = pixels

        if self.WIDTH:
            conf['width'] = self.WIDTH

        # disable some fields : eg: autofields and auto datetimefields
        if not getattr(self.field, 'editable', True) or self.field.__class__.__name__ == 'AutoField':
            conf = {
                'xtype': 'hidden',
                'disabled': True,
                'editable': False,
                'name': name
            }

        conf.update(data)
        # if self.field.name in  .in _get_validation_exclusions
        return conf

    def getName(self):
        if isinstance(self.field, forms.Field):
            name = self.field.label
        else:
            name = self.field.name
        if not name:
            name = self.field.__class__.__name__
        return unicode(name)

    def allowBlank(self):
        if isinstance(self.field, forms.Field):
            allow = not self.field.required
        else:
            allow = self.field.blank
        return allow

    def getReaderConfig(self):
        return {
            'name': self.getName(),
            'type': self.TYPE,
            'allowBlank': self.allowBlank()
        }

    def getColumnConfig(self):
        conf = {
            'header': unicode(self.field.verbose_name),
            'tooltip': unicode(self.field.verbose_name),
            'name': unicode(self.field.name),
            'sortable': True,
            'dataIndex': unicode(self.field.name),
            'editor': self.getEditor()
        }
        if self.COL_WIDTH:
            conf['width'] = self.COL_WIDTH
        return conf

    def parseValue(self, value):
        # called by the handler
        # transform input data to fit field format
        return value

    def getValue(self, value):
        # format data for ExtJs emitter
        return value


class AutoField(Field):
    WIDTH = 40
    TYPE = 'auto'

    def getEditor(self, *args, **kwargs):
        conf = super(AutoField, self).getEditor(*args, **kwargs)
        conf.update({'xtype': 'hidden', 'editable': False})
        return conf

    def getColumnConfig(self):
        conf = super(AutoField, self).getColumnConfig()
        conf['hidden'] = True
        return conf


class EmailField(Field):
    WIDTH = 250
    TYPE = 'string'

    def getEditor(self, *args, **kwargs):
        conf = super(EmailField, self).getEditor(*args, **kwargs)
        conf.update({'xtype': 'textfield', 'vtype': 'email'})
        return conf


class URLField(Field):
    WIDTH = 250
    TYPE = 'string'

    def getEditor(self, *args, **kwargs):
        conf = super(URLField, self).getEditor(*args, **kwargs)
        conf.update({'xtype': 'textfield', 'vtype': 'url'})
        return conf


class CharField(Field):
    TYPE = 'string'
    
    def getEditor(self, *args, **kwargs):
        conf = super(CharField, self).getEditor(*args, **kwargs)
        if getattr(self.field, 'choices', None):
            choices = {
                'xtype': 'awesomecombo',
                'format': 'string',
                'displayField': 'value',
                'hiddenName': conf.get('name'),
                'valueField': 'id',
                'mode': 'local',
                'triggerAction': 'all',
                'editable': False,
                'forceSelection': True,
                'store': {
                    'xtype': 'simplestore',
                    'fields': ['id', 'value'],
                    'data': self.field.choices
                }
            }
            conf.update(choices)
        return conf

        return {'xtype': 'textfield'}

ChoiceField = CharField
SlugField = CharField
TextField = CharField


class MultipleChoiceField(ChoiceField):
    
    def getEditor(self, *args, **kwargs):
        conf = super(MultipleChoiceField, self).getEditor(*args, **kwargs)
        conf['enableMultiSelect'] = True
        conf['format'] = 'array'
        return conf


class MultipleStringChoiceField(ChoiceField):
    
    def getEditor(self, *args, **kwargs):
        conf = super(MultipleStringChoiceField, self).getEditor(*args, **kwargs)
        conf['enableMultiSelect'] = True
        conf['format'] = 'string'
        return conf


class DecimalField(Field):
    FORMAT_RENDERER = '0.00'
    TYPE = 'float'
    COL_WIDTH = 50

    def getEditor(self, *args, **kwargs):
        conf = super(DecimalField, self).getEditor(*args, **kwargs)
        conf.update({'xtype': 'numberfield', 'style': 'text-align:right', 'width': 50})
        return conf

    def getReaderConfig(self):
        conf = super(DecimalField, self).getReaderConfig()
        conf['type'] = self.TYPE
        return conf

    def getColumnConfig(self):
        conf = super(DecimalField, self).getColumnConfig()
        conf['xtype'] = 'numbercolumn'
        conf['align'] = 'right'
        conf['format'] = self.FORMAT_RENDERER
        return conf

    def parseValue(self, value):
        if value:
            value = str(value)
        return value


class IntegerField(DecimalField):
    FORMAT_RENDERER = '0'
    TYPE = 'int'

PositiveIntegerField = IntegerField
FloatField = DecimalField


class DateTimeField(Field):
    FORMAT = 'Y-m-d H:i:s'
    FORMAT_RENDERER = 'Y-m-d H:i'
    EDITOR_XTYPE = 'datefield'
    FORMAT_PARSE = '%Y-%m-%dT%H:%M:%S'
    FORMAT_GET = '%Y-%m-%dT%H:%M:%S'
    WIDTH = 50
    COL_WIDTH = 50
    TYPE = 'date'

    def getEditor(self, *args, **kwargs):
        conf = super(DateTimeField, self).getEditor(*args, **kwargs)
        conf.update({'xtype': self.EDITOR_XTYPE, 'format': self.FORMAT})
        return conf

    def getReaderConfig(self):
        conf = super(DateTimeField, self).getReaderConfig()
        conf['dateFormat'] = self.FORMAT
        return conf

    def getColumnConfig(self):
        conf = super(DateTimeField, self).getColumnConfig()
        conf['xtype'] = 'datecolumn'
        conf['align'] = 'center'
        conf['format'] = self.FORMAT_RENDERER
        return conf

    def parseValue(self, value):
        if value:
            value = datetime.datetime.strptime(value, self.FORMAT_PARSE)
        return value

    def getValue(self, value):
        # format data for ExtJs emitter
        return value.strftime(self.FORMAT_GET)


class DateField(DateTimeField):
    FORMAT = 'Y-m-d'
    FORMAT_RENDERER = 'Y-m-d'
    FORMAT_PARSE = '%Y-%m-%d'
    WIDTH = 30
    COL_WIDTH = 30

    def parseValue(self, value):
        if value:
            if value.find('T') > 0:
                value = value.split('T')[0]
            value = datetime.datetime.strptime(value, self.FORMAT_PARSE).date()
        return value


class TimeField(DateTimeField):
    FORMAT = 'H:i:s'
    FORMAT_RENDERER = 'H:i'
    EDITOR_XTYPE = 'timefield'
    FORMAT_PARSE = '%H:%M:%S'
    WIDTH = 30
    COL_WIDTH = 30

    def parseValue(self, value):
        if value:
            if value.find('T') > 0:
                value = value.split('T')[1]
            value = datetime.datetime.strptime(value, self.FORMAT_PARSE).time()
        return value


class BooleanField(Field):

    WIDTH = 30
    COL_WIDTH = 30
    TYPE = 'bool'

    def getEditor(self, *args, **kwargs):
        conf = super(BooleanField, self).getEditor(*args, **kwargs)
        conf.update({'xtype': 'checkbox'})

        if 'initialValue' in kwargs:
            conf.update({'checked': True})

        if hasattr(self.field, 'initial'):
            conf['checked'] = True

        return conf

    def getColumnConfig(self):
        conf = super(BooleanField, self).getColumnConfig()
        conf['xtype'] = 'checkcolumn'
        return conf

    def getReaderConfig(self):
        conf = super(BooleanField, self).getReaderConfig()
        return conf


class ForeignKey(Field):

    MANYTOMANY = False
    RENDERER = 'Ext.django.FKRenderer'
    TYPE = 'int'

    def getEditor(self, *args, **kwargs):
        conf = super(ForeignKey, self).getEditor(*args, **kwargs)
        conf.update({
            'xtype': 'djangocombo',
            'enableMultiSelect': self.MANYTOMANY,
            'model': '%s.%s' % (
                self.field.related.parent_model._meta.app_label,
                self.field.related.parent_model._meta.object_name,
            ),
        })
        return conf

    def getColumnConfig(self):
        conf = super(ForeignKey, self).getColumnConfig()
        conf['related'] = True
        conf['renderer'] = {'fn': self.RENDERER, 'scope': 'this'}
        return conf

    def getReaderConfig(self):
        # generates tow config groups: with int type for ids and with string type for values
        conf = super(ForeignKey, self).getReaderConfig()
        conf_id = conf.copy()
        conf_id['name'] = conf.get('name') + '_id'
        conf.update({'type': 'string'})
        return [conf, conf_id]

    def parseValue(self, value):
        if value:
            value = self.parseFK(self.field.rel.to, value)[0]
        if not value:
            value = None
        return value

    def parseFK(self, cls, value):
        """ Translates FK or M2M values to instance list """

        relateds = []
        if isinstance(value, list):
            for id in value:
                if isinstance(id, dict) and 'id' in id:
                    item = cls.objects.get(pk=id['id'])
                else:
                    item = cls.objects.get(pk=id)
                relateds.append(item)
        elif isinstance(value, dict) and 'id' in value:
            relateds.append(cls.objects.get(pk=value['id']))
        else:
            relateds.append(cls.objects.get(pk=value))
        return relateds

OneToOneField = ForeignKey


class ModelChoiceField(ForeignKey):

    def getEditor(self, *args, **kwargs):
        conf = super(ForeignKey, self).getEditor(*args, **kwargs)
        model = self.field._queryset.model
        conf.update({
            'xtype': 'djangocombo',
            'enableMultiSelect': self.MANYTOMANY,
            'model': '%s.%s' % (
                model._meta.app_label,
                model._meta.object_name,
            ),
        })
        return conf


class ManyToManyField(ForeignKey):

    MANYTOMANY = True
    RENDERER = 'Ext.django.M2MRenderer'
    TYPE = 'array'

    def parseValue(self, value):
        if value:
            value = self.parseFK(self.field.rel.to, value)
        return value

    def getReaderConfig(self):
        conf = {
            'name': self.getName(),
            'type': self.TYPE,
            'allowBlank': self.allowBlank()
        }
        conf_id = conf.copy()
        conf_id['name'] = conf.get('name') + '_ids'
        return [conf, conf_id]


class ModelMultipleChoiceField(ModelChoiceField, ManyToManyField):
    pass


class FileField(Field):
    pass
