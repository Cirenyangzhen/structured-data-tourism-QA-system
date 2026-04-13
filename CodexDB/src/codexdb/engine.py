'''
Created on Oct 3, 2021

@author: immanueltrummer
'''
# -*- coding: utf-8 -*-

import abc
import os
import pandas as pd
import subprocess
import sys
import sqlite3
import time
import shutil
# -*- coding: utf-8 -*-
class ExecutionEngine(abc.ABC):
    """ Executes code in different languages. """
    
    def __init__(self, catalog):
        """ Initialize with database catalog and variables.
        
        Args:
            catalog: informs on database schema and file locations
        """
        self.catalog = catalog
        self.tmp_dir = os.environ['CODEXDB_TMP']
        self.result_path = os.path.join(self.tmp_dir, 'result.csv')
    
    @abc.abstractmethod
    def execute(self, db_id, code, timeout_s):
        """ Execute code written in specified language.
        
        Args:
            db_id: code references data in this database
            code: execute this code
            timeout_s: execution timeout in seconds
        
        Returns:
            Boolean success flag, output, execution statistics
        """
        raise NotImplementedError()
    
    def _clean(self):
        """ Cleans up working directory before execution. """
        result_path = self.result_path
        if os.path.exists(result_path):
            if os.path.isdir(result_path):
                shutil.rmtree(result_path, ignore_errors=True)
            else:
                try:
                    os.remove(result_path)
                except Exception as e:
                    print(f"Error removing file {result_path}: {e}")
    
    def _copy_db(self, db_id):
        """ Copies data to a temporary directory.
        
        Args:
            db_id: database ID
        """
        src_dir = self.catalog.db_dir(db_id)
        for tbl_file in self.catalog.files(db_id):
            src_path = os.path.join(src_dir, tbl_file)
            dest_path = os.path.join(self.tmp_dir, tbl_file.lower() if not self.id_case else tbl_file)
            if self.id_case:
                # 使用shutil复制文件，无需sudo
                shutil.copy2(src_path, dest_path)
            else:
                with open(src_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                    lines[0] = lines[0].lower()
                with open(dest_path, 'w', encoding='utf-8') as file:
                    file.writelines(lines)

    def _expand_paths(self, db_id, code):
        """ Expand relative paths to data files in code.
        
        Args:
            db_id: database identifier
            code: generated code
        
        Returns:
            code after expanding paths
        """
        for file in self.catalog.files(db_id):
            for quote in ['"', "'"]:
                file_path = f'{quote}{file}{quote}'
                full_path = f'{quote}{os.path.join(self.tmp_dir, file).replace(os.sep, "/")}{quote}'
                code = code.replace(file_path, full_path)
        
        # 修改路径分隔符为Windows样式
        tmp_dir_win = self.tmp_dir.replace(os.sep, "/")
        prefix = f"import os\nos.chdir(r'{tmp_dir_win}')\n"
        return prefix + code
    

    def _write_file(self, filename, code):
        file_path = os.path.join(self.tmp_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write('# -*- coding: utf-8 -*-\n' + code)


class PythonEngine(ExecutionEngine):
    """ Executes Python code. """
    
    def __init__(self, catalog, id_case):
       
        super().__init__(catalog)
        self.id_case = id_case
        self.python_path = os.environ['CODEXDB_PYTHON']
    
    def execute(self, db_id, code, timeout_s):
       
        self._clean()
        self._copy_db(db_id)
        start_s = time.time()
        success, output, stats = self._exec_python(db_id, code, timeout_s)
        total_s = time.time() - start_s
        stats['total_s'] = total_s
        return success, output, stats
    
    def _exec_python(self, db_id, code, timeout_s):
        """ Execute Python code and return generated output.
        
        Args:
            db_id: database identifier
            code: Python code to execute
            timeout_s: execution timeout in seconds
        
        Returns:
            Success flag, output, and execution statistics
        """
        filename = 'execute.py'
        code = self._expand_paths(db_id, code)
        print('--- EXECUTED CODE ---')
        print(code)
        print('--- (EXECUTED CODE) ---')
        self._write_file(filename, code)
        exe_path = os.path.join(self.tmp_dir, filename)
        cmd_parts = [self.python_path, exe_path]
        try:
            sub_comp = subprocess.run(
                cmd_parts, 
                capture_output=True, 
                timeout=timeout_s,
                text=True
            )
            success = (sub_comp.returncode == 0)
        except subprocess.TimeoutExpired:
            success = False
            sub_comp = None
        
        if not success:
            if sub_comp:
                print(f'Python stdout: {sub_comp.stdout}')
                print(f'Python stderr: {sub_comp.stderr}')
            else:
                print("Execution timed out.")
            output = pd.DataFrame([[]])
        else:
            try:
                output = pd.read_csv(self.result_path)
            except Exception as e:
                print(f'Exception while reading result file: {e}')
                output = pd.DataFrame([[]])
        return success, output, {}


class SqliteEngine(ExecutionEngine):
    """ SQL execution engine using SQLite. """
    
    def __init__(self, catalog):
        
        super().__init__(catalog)
    
    def execute(self, db_id, sql, timeout_s):
       
        self._prepare_db(db_id)
        return self._execute(db_id, sql, timeout_s)
    
    def _execute(self, db_id, sql, timeout_s):

        db_dir = self.catalog.db_dir(db_id)
        db_path = os.path.join(db_dir, 'db.db')
        try:
            with sqlite3.connect(db_path) as connection:
                start_s = time.time()
                result = pd.read_sql(sql, connection)
                total_s = time.time() - start_s
                print(f'Query Result Info: {result.info()}')

                result.to_csv(self.result_path, index=False)
                
            return True, result, {'execution_s': total_s}
        except Exception as e:
            print(f'Exception: {e}')
            return False, pd.DataFrame(), {'execution_s': -1}
    
    def _prepare_db(self, db_id):
        
        db_dir = self.catalog.db_dir(db_id)
        db_path = os.path.join(db_dir, 'db.db')
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception as e:
                print(f"Error removing database file: {e}")
        with sqlite3.connect(db_path) as connection:
            schema = self.catalog.schema(db_id)
            tables = schema['table_names_original']
            for table in tables:
                file_name = self.catalog.file_name(db_id, table)
                table_path = os.path.join(db_dir, file_name)
                df = pd.read_csv(table_path)
                df.columns = df.columns.str.replace(' ', '_')
                df.to_sql(table, connection, index=False, if_exists='replace')