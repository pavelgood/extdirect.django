import operator
import string
import json
import sys
from django.db.models import Q
from django.db.models.query import QuerySet

class QueryParser:
    """
    Mongodb like query parser.
    Parses query from dict abd return Q-objects.
    $lt, $gt, $lte, $gte syntax: { field: {$lt: value} }
    $and, $or syntax: { $and: [ { <expression1> }, { <expression2> } , ... , { <expressionN> } ] }
    $not syntax: { field: { $not: { <operator-expression> } } }
    foreign key fields syntax: fkfield1__fkfield2__......__fkfieldN__filterfield
    """
    #comparision operators
    _gt = '$gt'
    _lt = '$lt'
    _gte = '$gte'
    _lte = '$lte'
    _in = '$in'
    _contains = '$contains'
    _icontains = '$icontains'
    _exact = '$exact'
    _iexact = '$iexact'
    _range = '$range'

    #logical operators
    _or = '$or'
    _and = '$and'
    _not = '$not'

    #list of comparision operators
    comparision = [_gt, _gte, _lt, _lte, _in, _contains, _icontains, _exact, _iexact]

    #list of logical operators
    logical = [_or, _and, _not]

    #django's model
    model = None

    def __init__(self, model):
        self.model = model

    def parse(self, data):
        result = ()
        try:
            data = json.loads(data)
            result = self.parse_item(data)
        except:
            err = sys.exc_info()[1]
            print "Unexpected error: ", err
        return result

    def parse_item(self, data):
        """
        Parse filter item: { element: expression }
        """
        if not isinstance(data, dict):
            return ()
        if not len(data):
            return ()
        key = data.keys()[0]
        if key[0] == '$':
            if key in self.logical:
                return self.parse_logical(key, data.pop(key))
            else:
                print('Unknown logical operator: %s' % key)
                return ()
        else:
            return self.parse_field(key, data[key])

    def parse_logical(self, key, data):
        """
        Parse block with logical operation.
        """
        if key == self._and:
            if not isinstance(data, list):
                print('Not a list')
                return ()
            qf = list()
            for item in data:
                qf.append(self.parse_item(item))
            ob = reduce(operator.and_, qf)
            return ob
        elif key == self._or:
            if not isinstance(data, list):
                print('Not a list')
                return ()
            qf = list()
            for item in data:
                obj = self.parse_item(item)
                if len(obj) > 0:
                    qf.append(obj)
            if len(qf) > 0:
                return reduce(operator.or_, qf)
            return ()
        elif key == self._not:
            # todo:
            pass
        else:
            pass
            #raise
        return ()

    def parse_comparision(self, data):
        """
        Return string operator and value.
        """
        if isinstance(data, list):
            pass
        return data
        # elif key == self._lt:
        #     return 'lt'
        # elif key == self._gt:
        #     pass
        # elif key == self._lte:
        #     pass
        # elif key == self._gte:
        #     pass
        # elif key == self._in:
        #     pass
        # elif key == self._range:
        #     pass
        # elif key == self._contains:
        #     pass
        # elif key == self._icontains:
        #     pass
        # elif key == self._exact:
        #     pass
        # elif key == self._iexact:
        #     pass

    def parse_field(self, field, value):
        """
        Return Q-object.
        """
        if isinstance(value, dict):
            key = value.keys()[0]
            value = self.parse_comparision(value[key])
            return (Q((field + '__' + key[1:], value)))
        else:
            return (Q((field + '__' + self._iexact[1:], value)))