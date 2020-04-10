from odoo import api, fields, models, tools, exceptions, _
from odoo.exceptions import AccessError, UserError, ValidationError

class PostgresLog(models.Model):
    _name = 'postgres.log'
    _description = 'Postgres Log'

    _auto = False


    def init(self):
        query = """
                    CREATE FOREIGN TABLE IF NOT EXISTS postgres_log
                    (
                    log_time timestamp(3) with time zone,
                    user_name text,
                    database_name text,
                    process_id integer,
                    connection_from text,
                    session_id text,
                    session_line_num bigint,
                    command_tag text,
                    session_start_time timestamp with time zone,
                    virtual_transaction_id text,
                    transaction_id bigint,
                    error_severity text,
                    sql_state_code text,
                    message text,
                    detail text,
                    hint text,
                    internal_query text,
                    internal_query_pos integer,
                    context text,
                    query text,
                    query_pos integer,
                    location text,
                    application_name text)
                    SERVER logserver OPTIONS (filename 'log/postgresql.csv', format 'csv');        
                    """

        try:
            q1 = self.env.cr.execute("""CREATE EXTENSION IF NOT EXISTS file_fdw;""")
            try:
                q2 = self.env.cr.execute("""CREATE SERVER IF NOT EXISTS logserver FOREIGN DATA WRAPPER file_fdw;""")
                try:
                    q2 = self.env.cr.execute(query)
                
                except Exception as e:
                    raise UserError(_(e.args))
            except Exception as e:
                raise UserError(_(e.args))


        except Exception as e:
              raise UserError(_(e.args))



        
 
        q3 = self.env.cr.execute(query)

      
        return True


class EvlAuditLog(models.Model):
    _name = 'evl.auditlog'
    _description = 'EVL Audit Log'
    _auto = False
    _order = 'log_time desc'
    
    log_time  = fields.Datetime('Log Time', readonly=True)
    user_name = fields.Char('Username', readonly=True)
    database_name = fields.Text('Database Name',  readonly=True)
    process_id = fields.Integer('Process ID',  readonly=True)
    connection_from = fields.Text('Connection From ', readonly=True)
    session_id = fields.Text('Session ID ', readonly=True)
    session_line_num = fields.Integer('Session ID', readonly=True)
    command_tag = fields.Text('Command', readonly=True)
    session_start_time = fields.Datetime('Session', readonly=True)
    virtual_transaction_id = fields.Text('Virtual Transaction ID', readonly=True)
    transaction_id = fields.Text('Transaction ID ', readonly=True)
    error_severity = fields.Text('Error Severity', readonly=True)
    sql_state_code = fields.Text('SQL State Code', readonly=True)
    message = fields.Text('Message ', readonly=True)
    detail = fields.Text('Detail ', readonly=True)
    hint = fields.Text('Hint ', readonly=True)

    internal_query = fields.Text('Internal Query ', readonly=True)
    internal_query_pos = fields.Integer('Internal Query Pos ', readonly=True)
    context = fields.Text('Context', readonly=True)
    query = fields.Text('Query ', readonly=True)
    query_pos = fields.Integer('Query Pos ', readonly=True)
    location = fields.Text('Location', readonly=True)
    application_name = fields.Text('Application Name ', readonly=True)


    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        
        with_ = ("WITH %s" % with_clause) if with_clause else ""
        select_ = """
            ROW_NUMBER() over (ORDER BY database_name) as id,
            log_time as log_time,
            user_name as user_name,
            database_name as database_name,
            process_id as process_id,
            connection_from as connection_from,         
            
            session_id as session_id,
            session_line_num as session_line_num,
            command_tag as command_tag,
            virtual_transaction_id as virtual_transaction_id,
            message as message,
            query as query,                       
            
            transaction_id as transaction_id,
            error_severity as error_severity,
            session_start_time as session_start_time,
            sql_state_code as sql_state_code,
            detail as detail,
            hint as hint,
            internal_query as internal_query,
            internal_query_pos as internal_query_pos,
            context as context,
            query_pos as query_pos,
            location as location,
            application_name as application_name
        """

        for field in fields.values():
            select_ += field

        from_ = """
                postgres_log
                %s
        """ % from_clause

        # groupby_ = """
        #     l.product_id,
        # """ % (groupby)

        return "%s (SELECT %s FROM %s WHERE database_name= '%s' ORDER BY log_time DESC)" % (with_, select_, from_, self._cr.dbname)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))




