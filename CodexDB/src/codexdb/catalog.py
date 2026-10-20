'''
Created on Oct 5, 2021

@author: immanueltrummer
'''
import json

class DbCatalog():
    """ Information over all databases in database directory. """
    
    def __init__(self, data_dir):
        """ Initialize for given database directory. 
        
        Args:
            data_dir: contains databases and schemata
        """
        self.data_dir = data_dir
        self.schema_path = f'{data_dir}/schemata.json'
        with open(self.schema_path) as file:
            self.schemata = json.load(file)
        self.table_to_file = {}
    
    def assign_file(self, db_id, table, file_name):
        """ Assign file to given table in given database.
        
        Args:
            db_id: table is in this database
            table: assign file containing data for this table
            file_name: name of file containing data
        """
        self.table_to_file[(db_id, table)] = file_name
        
    def db_dir(self, db_id):
        """ Returns directory storing specific database.
        
        Args:
            db_id: name of database
        
        Returns:
            path of directory containing database
        """
        return f'{self.data_dir}/database/{db_id}'
    
    def db_ids(self):
        """ Returns IDs of available databases.
        
        Returns:
            list with database IDs
        """
        return self.schemata.keys()
    
    def file_name(self, db_id, table):
        """ Returns name of file storing table data.
        
        Args:
            db_id: ID of database
            table: name of table
        
        Returns:
            name of file storing data
        """
        key = (db_id, table)
        default = f'{table}.csv'
        return self.table_to_file.get(key, default)
    
    def file_path(self, db_id, table):
        """ Returns path to file containing data for table.
        
        Args:
            db_id: search table in this database
            table: name of table
        
        Returns:
            path to file containing data for table
        """
        db_dir = self.db_dir(db_id)
        file_name = self.file_name(db_id, table)
        return f'{db_dir}/{file_name}'

    def files(self, db_id):
        """ Returns names of files containing database tables.
        
        Args:
            db_id: unique database identifier
        
        Returns:
            list of files associated with database tables
        """
        tables = self.schema(db_id)['table_names_original']
        return [self.file_name(db_id, t) for t in tables]
    
    def schema(self, db_id):
        """ Returns description of database schema.
        
        Args:
            db_id: unique name of database
        
        Returns:
            JSON object describing database schema
        """
        return self.schemata[db_id]
    def sqlite_schema(self, db_id):
        """Return live, read-only SQLite schema for Research V2.

        This deliberately does not modify the legacy schemata.json. Several
        historical metadata fields differ from schema.sql, and V2 prompts must
        use the actual database instead of guessing which text file is right.
        """
        from contextlib import closing
        from pathlib import Path
        from urllib.parse import quote
        import sqlite3

        if db_id not in self.schemata:
            raise KeyError('Unknown database id: ' + db_id)
        path = Path(self.db_dir(db_id)) / (db_id + '.sqlite')
        path = path.resolve(strict=True)
        uri = 'file:' + quote(path.as_posix(), safe='/:') + '?mode=ro'
        with closing(sqlite3.connect(uri, uri=True)) as con:
            tables = [
                row[0] for row in con.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
                    "ORDER BY name"
                )
            ]
            if not tables:
                raise ValueError('SQLite database has no user tables')
            columns = [[-1, '*']]
            keys_by_table = {}
            refs = []
            primary_keys = []
            for table_idx, table in enumerate(tables):
                name = '"' + table.replace('"', '""') + '"'
                rows = list(con.execute('PRAGMA table_info(' + name + ')'))
                if not rows:
                    raise ValueError('Table has no columns: ' + table)
                for info in rows:
                    columns.append([table_idx, info[1]])
                    if info[5]:
                        primary_keys.append(len(columns) - 1)
                keys_by_table[table] = {
                    col[1]: idx for idx, col in enumerate(columns)
                    if col[0] == table_idx
                }
                for fk in con.execute('PRAGMA foreign_key_list(' + name + ')'):
                    refs.append((table, fk[3], fk[2], fk[4]))
        foreign_keys = []
        for from_table, from_col, to_table, to_col in refs:
            src = keys_by_table.get(from_table, {}).get(from_col)
            dst = keys_by_table.get(to_table, {}).get(to_col)
            if src is not None and dst is not None:
                foreign_keys.append([src, dst])
        return {
            'db_id': db_id,
            'table_names_original': tables,
            'table_names': tables,
            'column_names_original': columns,
            'column_names': columns,
            'primary_keys': primary_keys,
            'foreign_keys': foreign_keys,
        }
