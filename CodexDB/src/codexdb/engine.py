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
    """CodexDB-compatible V2 SQLite execution engine.

    Unlike the original CSV-to-db-on-every-query implementation, this engine
    executes read-only SQL against a pinned, existing SQLite database.
    It retains the execute(db_id, sql, timeout_s) result contract.
    """

    def __init__(self, catalog, *, max_rows=200, max_opcodes=1000000,
                 db_path=None):
        self.catalog = catalog
        self.max_rows = max_rows
        self.max_opcodes = max_opcodes
        self.override_db_path = db_path
        temp_dir = os.environ.get('CODEXDB_TMP')
        self.tmp_dir = temp_dir
        self.result_path = os.path.join(temp_dir, 'result.csv') if temp_dir else None

    def execute(self, db_id, sql, timeout_s):
        """Return (success, DataFrame, execution metadata)."""
        from pathlib import Path
        from codexdb.sql_execution import (
            SQLValidationError, SQLExecutionError, execute_select
        )

        db_path = self.override_db_path or (
            Path(self.catalog.db_dir(db_id)) / f'{db_id}.sqlite'
        )
        try:
            result, stats = execute_select(
                sql, db_path, timeout_s=timeout_s,
                max_rows=self.max_rows, max_opcodes=self.max_opcodes,
            )
            if self.result_path:
                Path(self.result_path).parent.mkdir(parents=True, exist_ok=True)
                result.to_csv(self.result_path, index=False)
            return True, result, stats
        except (SQLValidationError, SQLExecutionError, OSError, ValueError) as exc:
            return False, pd.DataFrame(), {
                'execution_s': -1,
                'error_type': type(exc).__name__,
                'error': str(exc),
            }
