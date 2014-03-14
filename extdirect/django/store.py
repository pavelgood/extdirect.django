from django.core.serializers import serialize
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.db import models
from filter import QueryParser
from django.db.models import Q
from metadata import meta_fields, meta_columns
import operator

class ExtDirectStore(object):
    """
    Implement the server-side needed to load an Ext.data.DirectStore
    """
    def __init__(self, model, extras=[], root='records', total='total', success='success', \
                 message='message', start='start', limit='limit', sort='sort', dir='direction',\
                 prop='property', id_property='id', filter='filter', pquery='query', \
                 colModel=False, metadata=False, mappings={}, sort_info={}, custom_meta={}, fields = [], \
                 exclude_fields=[], extra_fields=[], get_metadata=None):
        
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
        self.property = prop
        self.filter = filter
        self.pquery = pquery
        self.fields = fields
        self.get_metadata = get_metadata
        self.extra_fields = extra_fields
        self.sort_info = sort_info
        self.custom_meta = custom_meta
        self.showmetadata = metadata
        self.metadata = {}
        self.buildMetaData()
        self.queryfilter = 'queryfilter'
        self.value = 'value'
        self.query_filter = QueryParser(self.model)
        
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
           
            self.metadata.update(self.custom_meta)  

    def query(self, qs=None, metadata=True, colModel=False, fields=None, **kw):
        """
        Filter objects and return serialized bundle.
        """
        paginate    = False
        total       = None
        sort_field  = 'id'
        sort_dir    = 'DESC'

        kw, qfilters = self.filter_handler(kw)

        if self.start in kw and self.limit in kw:
            start = kw.pop(self.start)
            limit = kw.pop(self.limit)
            paginate = True

        if self.sort in kw:
            sort = kw.pop(self.sort)
            if isinstance(sort, list) and isinstance(sort[0], dict) \
                    and self.dir in sort[0] and self.property in sort[0]:
                sort_dir = sort[0].pop(self.dir)
                sort_field = sort[0].pop(self.property)

        if not qs is None:
            # Don't use queryset = qs or self.model.objects
            # because qs could be empty list (evaluate to False)
            # but it's actually an empty queryset that must have precedence
            queryset = qs
        else:
            queryset = self.model.objects

        if len(qfilters):
            queryset = queryset.filter(qfilters)
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
            
        return self.serialize(objects, metadata, colModel, total, fields=fields)
        
    def serialize(self, queryset, metadata=True, colModel=False, total=None, fields=None):
        meta = {
            'root': self.root,
            'total': self.total,
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
                res['columns'] = meta_columns(self.model, fields=fields)
             
        return res

    def filter_handler(self, kw):
        """
        Handles the `filter` and 'query' keys.
        """
        if self.pquery in kw:
            return self.query_handler(kw)

        if self.filter in kw:
            f = kw.pop(self.filter)
            if isinstance(f, list):
                for item in f:
                    if self.property in item and self.value in item:
                        if item[self.property] == self.queryfilter:
                            return kw, self.query_filter.parse(item[self.value])
                        else:
                            prop = item[self.property]
                            return kw, Q((prop, item[self.value]))
            elif self.property in f and self.value in f:
                if f[self.property] == self.queryfilter:
                    return kw, self.query_filter.parse(f[self.value])
                else:
                    prop = f[self.property]
                    return kw, Q((prop, f[self.value]))
        return kw, Q()

    #TODO: remove this method and 'query' key handler, use 'filter' key only
    def query_handler(self, kw):
        """
        Handles the `query` key.
        """
        qf = ()
        if self.pquery in kw:
            if self.limit in kw:
                kw.pop(self.limit)
            kw.__setitem__(self.start, 0)
            template = kw.pop(self.pquery)
            fields = self.model._meta.fields
            f = []
            for field in fields:
                keyword = field.name + '__icontains'
                if field.name == 'id':
                    continue
                if isinstance(field, models.ForeignKey):
                    continue
                f.append(Q((keyword, template)))
            qf = reduce(operator.or_, f)
        return kw, qf
