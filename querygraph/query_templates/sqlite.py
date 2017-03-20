import datetime


from querygraph.template_parameter import TemplateParameter
from querygraph.query_template import QueryTemplate


# =============================================
# SQLite Template Parameter
# ---------------------------------------------

class SqliteParameter(TemplateParameter):

    CHILD_DATA_TYPES = {
        'datetime': {datetime.datetime: lambda x: "'%s'" % x.strftime('%Y-%m-%d %H:%M:%S'),
                     str: lambda x: "'%s'" % x},
        'date': {datetime.datetime: lambda x: "'%s'" % x.strftime('%Y-%m-%d'),
                 str: lambda x: "'%s'" % x},
        'time': {datetime.datetime: lambda x: "'%s'" % x.strftime('%H:%M:%S'),
                 str: lambda x: "'%s'" % x}
    }

    def __init__(self, parameter_str, parameter_type):
        TemplateParameter.__init__(self,
                                   parameter_str=parameter_str,
                                   parameter_type=parameter_type)

    class TypeMaps:

        _datetime = {datetime.datetime: lambda x: "'%s'" % x.strftime('%Y-%m-%d %H:%M:%S'),
                     str: lambda x: "'%s'" % x}

        _date = {datetime.datetime: lambda x: "'%s'" % x.strftime('%Y-%m-%d'),
                 str: lambda x: "'%s'" % x}

        _time = {datetime.datetime: lambda x: "'%s'" % x.strftime('%H:%M:%S'),
                 str: lambda x: "'%s'" % x}


# =============================================
# SQLite Query Template
# ---------------------------------------------

class SqliteTemplate(QueryTemplate):

    def __init__(self, template_str, db_connector):
        QueryTemplate.__init__(self,
                               template_str=template_str,
                               db_connector=db_connector,
                               parameter_class=SqliteParameter)

    def execute(self, df=None, **independent_param_vals):
        if self.rendered_query is not None:
            rendered_query = self.rendered_query
        else:
            rendered_query = self.render(df=df, **independent_param_vals)
        df = self.db_connector.execute_query(query=rendered_query)
        return df