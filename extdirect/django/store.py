from django.core.serializers import serialize
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.db.models import Q
import operator
from metadata import meta_fields, meta_columns


class ExtDirectStore(object):
    """
    Implement the server-side needed to load an Ext.data.DirectStore
    """
    
    def __init__(self, model, extras=[], root='records', total='total', success='success', \
                 message='message', start='start', limit='limit', sort='sort', dir='direction',\
                 prop='property', id_property='id', filter='filter', colModel=False, metadata=False, \
                 mappings={}, sort_info={}, custom_meta={}, fields = [], exclude_fields=[], \
                 extra_fields=[], get_metadata=None):
        
        self.model = model        
        self.root = root
        self.total = total
        self.success = success
        self.extras = extras        
        self.id_property = id_property
        self.message = message
        self.exclude_fields = exclude_fields
        self.mappings = mappings
        # paramNames
        self.start = start
        self.limit = limit
        self.sort = sort
        self.dir = dir
        self.property = prop # sort and filter fieldname
        self.filter = filter
        self.fields = fields
        self.get_metadata = get_metadata
        self.extra_fields = extra_fields
        self.sort_info = sort_info
        self.custom_meta = custom_meta
        self.showmetadata = metadata
        self.metadata = {}
        self.buildMetaData()
        
    def buildMetaData(self):
        self.metadata = {}
        if self.showmetadata:      
        
            fields = meta_fields(self.model, self.mappings, self.exclude_fields, self.get_metadata, fields = self.fields) + self.extra_fields            
            #print 'buildMetaData meta_fields', fields
            self.metadata = {
                'idProperty': self.id_property,
                'root': self.root,
                'totalProperty': self.total,
                'successProperty': self.success,
                'fields': fields,
                'messageProperty': self.message
            }
            if self.sort_info:
                self.metadata.update({'sortInfo': self.sort_info})
            
            # if self.model.__name__ == 'User':
                # for field in fields:
                    # if not field['allowBlank']:
                        # print 'mandatory', field
           
            self.metadata.update(self.custom_meta)  
            
            
    def query(self, qs=None, metadata=True, colModel=False, fields = None, **kw):                
        paginate = False
        total = None
        order = False
        if kw.has_key(self.start) and kw.has_key(self.limit):
            start = kw.pop(self.start)
            limit = kw.pop(self.limit)
            paginate = True

        qfilters=[]
        if kw.has_key(self.filter):
            prefilters = []
            items = kw.pop(self.filter)
            if isinstance(items, list):
                for item in items:
                    prefilters.append( ( item.pop(self.property) + '__contains', item.pop('value') ) )
            else:
                prefilters.append( ( item.pop(self.property) + '__contains', item.pop('value') ) )

            qfilters = [Q(x) for x in prefilters]

        sort_field = None
        sort_dir   = 'DESC'

        if kw.has_key(self.sort):
            sort = kw.pop(self.sort)
            if len(sort) and sort[0].has_key(self.dir) and sort[0].has_key(self.sort_field):
                sort_dir = sort[0].pop(self.dir)
                sort_field = sort[0].pop(self.sort_field)

        if not qs is None:
            # Don't use queryset = qs or self.model.objects
            # because qs could be empty list (evaluate to False)
            # but it's actually an empty queryset that must have precedence
            queryset = qs
        else:
            queryset = self.model.objects
            
        if len(qfilters):
            queryset = queryset.filter(reduce(operator.or_, qfilters))
        else:
            queryset = queryset.filter()

        if not sort_field is None:
            if sort_dir == 'DESC':
                sort_field = '-' + sort_field
            queryset = queryset.order_by(sort_field)
                 
        if not paginate or (limit==0):
            objects = queryset
            total = queryset.count()
        else:
            paginator = Paginator(queryset, limit)
            total = paginator.count
            
            try:                
                page = paginator.page(start / limit + 1)
            except (EmptyPage, InvalidPage):
                #out of range, deliver last page of results.
                page = paginator.page(paginator.num_pages)
            
            objects = page.object_list
            
        return self.serialize(objects, metadata, colModel, total, fields = fields)
        
    def serialize(self, queryset, metadata=True, colModel = False, total=None, fields = None):        
        meta = {
            'root': self.root,
            'total' : self.total,
            'success': self.success,
            'idProperty': self.id_property
        }        
        res = serialize('extdirect', queryset, meta=meta, extras=self.extras,
                        total=total, exclude_fields=self.exclude_fields)
        
        self.buildMetaData()
        if metadata and self.metadata:            
            
            res['metaData'] = self.metadata     
            # also include columns for grids
            if colModel:    
                res['columns'] =  meta_columns(self.model, fields = fields)
             
        return res
