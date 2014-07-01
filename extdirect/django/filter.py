import operator
import string
import json
import sys
from django.db.models import Q
from django.db.models.fields import FieldDoesNotExist


class QueryParser:
    """
    Mongodb like query parser.
    
    Parses query from dict and returns Q-objects.
    $lt, $gt, $lte, $gte syntax: { field: {$lt: value} }
    $and, $or syntax: { $and: [ { <expression1> }, { <expression2> } , ... , { <expressionN> } ] }
    $not syntax: { field: { $not: { <operator-expression> } } }
    foreign key fields syntax: fkfield1__fkfield2__......__fkfieldN__filterfield
    
    JSON structure:
        filter: { property: "queryfilter", value: { <expression> } }
    
    Value example:
        value: { $or: [ { $or:[ {}, {} ...] }, { $not: {} }, {} ] }
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
        """
        Deserialize json string to python object and parse it.
        Return Q-object.
        """
        result = Q()
        try:
            data = json.loads(data)
            result = self._parse_item(data)
        except ValueError:
            print('Value error: ', sys.exc_info()[1])

        return result

    def _parse_item(self, data):
        """
        Parse filter item: { element: expression }
        Return Q-object.
        """
        if not isinstance(data, dict):
            return Q()
        if not len(data):
            return Q()
        key = data.keys()[0]
        if key[0] == '$':
            if key in self.logical:
                return self._parse_logical(key, data.pop(key))
            else:
                raise ValueError("Unsupported logical operation %s" % key)
        else:
            return self._parse_field(key, data[key])

    def _parse_logical(self, key, data):
        """
        Parse block with logical operation.
        Return Q-object.
        """
        if key == self._and:
            if not isinstance(data, list):
                print("Not a list")
                return Q()
            qf = list()
            for item in data:
                obj = self._parse_item(item)
                if len(obj) > 0:
                    qf.append(obj)
            if len(qf) > 0:
                return reduce(operator.and_, qf)
            return Q()
        elif key == self._or:
            if not isinstance(data, list):
                print("Not a list")
                return Q()
            qf = list()
            for item in data:
                obj = self._parse_item(item)
                if len(obj) > 0:
                    qf.append(obj)
            if len(qf) > 0:
                return reduce(operator.or_, qf)
            return Q()
        elif key == self._not:
            obj = self._parse_item(data)
            if len(obj) > 0:
                return ~obj
        else:
            pass
        return Q()

    def _parse_comparision(self, field, key, data):
        """
        Return string value.
        """
        return data

    def _parse_field(self, field, value):
        """
        Return Q-object.
        field - field name
        value - field value or expression
        """
        if isinstance(value, dict):
            key = value.keys()[0]
            value = self._parse_comparision(field, key, value[key])
            return Q((field + '__' + key[1:], value))
        else:
            return Q((field + '__' + self._iexact[1:], value))