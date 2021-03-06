from collections import OrderedDict
import re

import pandas as pd


from querygraph.query_template import QueryTemplate
from querygraph.exceptions import (QueryGraphException,
                                   ConnectionError,
                                   ExecutionError,
                                   JoinContextException,
                                   ParameterError)
from querygraph.join_context import JoinContext, OnColumn
from querygraph import thread_tree
from querygraph.db.interface import DatabaseInterface
from querygraph.manipulation.set import ManipulationSet
from querygraph.execution_log import ExecutionLog


# =============================================
# Query Node Class
# ---------------------------------------------

class QueryNode(object):
    """
    QueryNode class...

    Parameters
    ----------
    name : str
        Name assigned to the node.
    query : str
        The node's query template string.
    db_interface : DatabaseInterface instance
        The node's database interface.
    log : ExecutionLog instance
        Logging class passed to QueryNode by its host QueryGraph.
    fields : list or None
        A list of fields to return - only used for NoSql databases
        that do not return relational data.

    """

    def __init__(self, name, query, db_interface, log, fields=None):
        self.name = name
        self.query = query
        if not isinstance(log, ExecutionLog):
            raise QueryGraphException
        self.log = log
        assert isinstance(db_interface, DatabaseInterface)
        self.db_interface = db_interface
        self.fields = fields
        self.children = list()
        self.parent = None
        self.join_context = JoinContext(child_node_name=self.name)
        self._df = None
        self.already_executed = False
        self._new_columns = OrderedDict()
        self.manipulation_set = ManipulationSet()

    def __getitem__(self, item):
        return OnColumn(query_node=self, col_name=item)

    def __contains__(self, item):
        """ Check if given item is a child of this QueryNode. """
        return item in list(self)

    def __iter__(self):
        """
        Define iterator behaviour. Returns all nodes in the query graph in a topological order.

        """
        yield self
        for child in self.children:
            for child_child in child:
                yield child_child

    @property
    def df(self):
        return self._df

    @df.setter
    def df(self, value):
        assert isinstance(value, pd.DataFrame)
        cleaned_df = self.clean_df_col_names(df=value)
        self._df = cleaned_df

    @staticmethod
    def clean_col_name(col_name):
        return re.sub('\W|^(?=\d)', '_', col_name)

    def clean_df_col_names(self, df):
        rename_dict = {col_name: self.clean_col_name(col_name) for col_name in df.columns.values.tolist()}
        return df.rename(columns=rename_dict)

    def is_independent(self):
        # Todo: this.
        pass

    def root_node(self):
        if self.parent is None:
            return self
        else:
            return self.parent.root_node()

    @property
    def result_set_empty(self):
        return self.df.empty

    @property
    def num_edges(self):
        return len(self.children)

    @property
    def is_root_node(self):
        return self.parent is None

    def creates_cycle(self, child_node):
        """
        Check if adding the given node will result in a cycle.

        """
        return self in child_node

    def execute_manipulation_set(self):
        self.df = self.manipulation_set.execute(self.df)

    def join_with_parent(self):
        """
        Join this QueryNode with its parent node, using the defined join context.

        """
        self.log.node_info(source_node=self.name, msg="Attempting to join with parent node '%s'." % self.parent.name)
        if self.parent is None and self.df is None:
            raise QueryGraphException
        try:
            joined_df = self.join_context.apply_join(parent_df=self.parent.df, child_df=self.df)
            self.parent.df = joined_df
            self.log.node_info(source_node=self.name, msg="Joined with parent node '%s' dataframe." % self.parent.name)
        except JoinContextException, e:
            self.log.node_error(source_node=self.name,
                                msg="Couldn't join child '%s''s dataframe"
                                    " with parent node '%s''s dataframe." % (self.name, self.parent.name))
            raise

    def fold_children(self):
        """
        Join all QueryNode's with their parent in reverse topological order. This
        should only be called by the root QueryNode.

        """
        reverse_topological_ordering = list()
        for child in self:
            if child is not self:
                reverse_topological_ordering.insert(0, child)
        for query_node in reverse_topological_ordering:
            query_node.join_with_parent()

    @property
    def query_template(self):
        # return self._make_query_template()
        return QueryTemplate(template_str=self.query,
                             type_converter=self.db_interface.type_converter)

    def retrieve_dataframe(self, independent_param_vals):
        self.log.node_info(source_node=self.name,
                           msg="Attempting to execute query using connector '%s'." % self.db_interface.name)
        try:
            self._execute_query(independent_param_vals=independent_param_vals)
        except ConnectionError, e:
            self.log.node_error(source_node=self.name, msg="Could not connect to database using connector '%s': \n %s"
                                                           % (self.db_interface.name, e))
            raise
        except ExecutionError, e:
            self.log.node_error(source_node=self.name, msg="Problem executing query on database using "
                                                           "connector '%s': \n %s" % (self.db_interface.name, e))
            raise
        if self.manipulation_set and not self.result_set_empty:
            self.execute_manipulation_set()
        self.log.node_dataframe_header(source_node=self.name, df=self.df)

    def _rendered_query(self, independent_param_vals):
        try:
            query_template = self.query_template
            if self.parent is not None:
                rendered_query = query_template.render(df=self.parent.df, independent_param_vals=independent_param_vals)
            else:
                rendered_query = query_template.render(independent_param_vals=independent_param_vals)
            return rendered_query
        except ParameterError, e:
            self.log.node_error(source_node=self.name, msg="Couldn't render query template due to error(s): \n %s" % e)
            raise

    def _execute_query(self, independent_param_vals):
        rendered_query = self._rendered_query(independent_param_vals=independent_param_vals)
        if self.db_interface.fields_accepted:
            df = self.db_interface.execute_query(query=rendered_query, fields=self.fields)
        else:
            df = self.db_interface.execute_query(query=rendered_query)
        self.df = df

    def _execute(self, **independent_param_vals):
        """
        Execute this QueryNode's query. This requires:

            (1) Getting the parent node's dataframe, if one exists.
            (2) Passing the parent node's dataframe (if exists) to
                the QueryTemplate, and passing the independent parameter
                values, as defined in **kwargs, to the QueryTemplate.
            (3) Parsing the query - generating the actual query string
                that will be run on the node's database.
            (4) Getting the query results and defining the node's dataframe.
            (5) Creating any new columns.
            (6) Setting the node's 'already_executed' attribute to True.


        """
        pass

    def root_execution_thread(self, threads, independent_param_vals):
        if not self.is_root_node:
            raise QueryGraphException("Trying to get root execution thread from node that is not root node.")
        root_thread = thread_tree.ExecutionThread(query_node=self,
                                                  threads=threads,
                                                  independent_param_vals=independent_param_vals)
        return root_thread

    def execute(self, **independent_param_vals):
        """
        Execute the QueryGraph. If this QueryNode is the root node, then also
        fold all child nodes (join them with their parents).

        :param df:
        :param kwargs:
        :return:
        """
        for query_node in self:
            query_node._execute(**independent_param_vals)
        if self.is_root_node:
            self.fold_children()