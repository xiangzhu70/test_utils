import sqlite3

class ReadWriteDB:
    def __init__(self, db_file):
        self.db_file = db_file
        # Connect to SQLite database (or create it if it doesn't exist)
        self.create_tables_if_not_exist()

    def create_tables_if_not_exist(self):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()

        # Create table test_runs
        c.execute('''
            CREATE TABLE IF NOT EXISTS test_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                desc_label TEXT UNIQUE,
                description TEXT DEFAULT '',
                time TEXT
            )
        ''')

        # Create table log_file_types
        c.execute('''
            CREATE TABLE IF NOT EXISTS log_file_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT UNIQUE NOT NULL
            )
        ''')

        # Create table log_files
        c.execute('''
            CREATE TABLE IF NOT EXISTS log_files (
                file_id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT,
                file_type INTEGER,
                test_run_id INTEGER,
                FOREIGN KEY(test_run_id) REFERENCES test_runs(id),
                FOREIGN KEY(file_type) REFERENCES log_file_types(id)
            )
        ''')

        # Create table operation_types
        c.execute('''
            CREATE TABLE IF NOT EXISTS operation_types (
                operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_name TEXT UNIQUE
            )
        ''')
        c.execute('''
            INSERT OR IGNORE INTO operation_types (operation_name)
                VALUES ("read")
        ''')
        c.execute('''
            INSERT OR IGNORE INTO operation_types (operation_name)
                VALUES ("write")
        ''')        

        # Create table log_lines
        c.execute('''
            CREATE TABLE IF NOT EXISTS log_lines (
                log_lines_id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER,
                line_start INTEGER,
                line_end INTEGER,
                FOREIGN KEY(file_id) REFERENCES log_files(file_id)
            )
        ''')

        # Create table read_write_logs
        c.execute('''
            CREATE TABLE IF NOT EXISTS read_write_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TEXT,
                operation_id INTEGER,
                log_lines_id INTEGER,
                result INTEGER,
                address INTEGER,
                data INTEGER,
                FOREIGN KEY(operation_id) REFERENCES operation_types(operation_id),
                FOREIGN KEY(log_lines_id) REFERENCES log_lines(log_lines_id)
            )
        ''')

        conn.commit()
        conn.close()

    def add_test_run(self, desc_label, time):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()

            # Check if a row with this desc_label exists
            c.execute("SELECT id FROM test_runs WHERE desc_label = ?", (desc_label,))
            row = c.fetchone()

            if row is not None:
                # If the row exists, return the id
                return row[0]
            else:
                try:
                    # If the row does not exist, insert it and return the id
                    c.execute("INSERT INTO test_runs (desc_label, time) VALUES (?, ?)", (desc_label, time))
                    conn.commit()
                    return c.lastrowid
                except sqlite3.Error as e:
                    print(f"An error occurred: {e}")


    def get_test_runs(self):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()

        # Get all rows from the test_runs table
        c.execute("SELECT * FROM test_runs")
        rows = c.fetchall()

        conn.close()

        # Return the rows as a list of dictionaries
        return [{'id': row[0], 'desc_label': row[1], 'time': row[2]} for row in rows]

    def get_operation_id(self, operation_name):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()

            # Query the operation_id by operation_name
            c.execute("SELECT operation_id FROM operation_types WHERE operation_name = ?", (operation_name,))

            result = c.fetchone()

            # If a result was found, return the operation_id, otherwise return None
            if result is not None:
                return result[0]
            else:
                return None

    def get_test_run_id(self, desc_label):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()

            # Query the test_run id by desc_label
            c.execute("SELECT id FROM test_runs WHERE desc_label = ?", (desc_label,))

            result = c.fetchone()

            # If a result was found, return the id, otherwise return None
            if result is not None:
                return result[0]
            else:
                return None
        
    def add_file_to_test_run(self, test_desc_label, file_type, file_path):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()

            # get test_run_id by desc_label
            test_run_id = self.get_test_run_id(test_desc_label)
            if not test_run_id:
                raise Exception("Test run not found from db")

            # Get file_type_id by file_type
            c.execute("SELECT id FROM log_file_types WHERE type = ?", (file_type,))
            result = c.fetchone()
            if result is None:
                raise Exception("File type not found in db")
            file_type_id = result[0]

            # Check if the log file already exists in the db
            c.execute(
                "SELECT file_id, file_path FROM log_files WHERE test_run_id = ? AND file_type = ?",
                (test_run_id, file_type_id)
            )
            result = c.fetchone()

            if result is not None:
                # If the file already exists, check if the path is the same
                if result[1] != file_path:
                    raise Exception("Mismatching file paths in database")
                else:
                    return result[0]
            else:
                # If the file does not exist, add it to the db
                c.execute(
                    "INSERT INTO log_files (file_path, file_type, test_run_id) VALUES (?, ?, ?)",
                    (file_path, file_type_id, test_run_id)
                )
                return c.lastrowid  # Return the id of the newly inserted log file
            
    def add_rw_log(self, file_id, log_lines_start, log_lines_end, time, address, operation_id, data, result):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()

            # Check if log_lines_id exists with the same file_id and start_line
            c.execute(
                "SELECT log_lines_id FROM log_lines WHERE file_id = ? AND line_start = ?", 
                (file_id, log_lines_start)
            )
            log_lines_id = c.fetchone()

            if log_lines_id is not None:
                raise Exception("log_lines_id already exists and should not be added twice")
            else:
                # Insert new log_lines entry
                c.execute(
                    "INSERT INTO log_lines (file_id, line_start, line_end) VALUES (?, ?, ?)", 
                    (file_id, log_lines_start, log_lines_end)
                )
                log_lines_id = c.lastrowid  # Get the ID of the newly inserted log line

                # Insert new read_write_logs entry
                c.execute(
                    "INSERT INTO read_write_logs (time, operation_id, log_lines_id, address, data, result) VALUES (?, ?, ?, ?, ?, ?)", 
                    (time, operation_id, log_lines_id, address, data, result)
                )
                
            conn.commit()


    def get_rw_logs_for_file(self, test_run_desc_label, file_type):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()

            c.execute(f'''
                SELECT log_lines.line_start, log_lines.line_end, read_write_logs.time, 
                    read_write_logs.address, operation_types.operation_name, read_write_logs.data, read_write_logs.result
                FROM test_runs
                JOIN log_files ON test_runs.id = log_files.test_run_id
                JOIN log_file_types ON log_files.file_type = log_file_types.id
                JOIN log_lines ON log_files.file_id = log_lines.file_id
                JOIN read_write_logs ON log_lines.log_lines_id = read_write_logs.log_lines_id
                JOIN operation_types ON read_write_logs.operation_id = operation_types.operation_id
                WHERE test_runs.desc_label = ? AND log_file_types.type = ?
                ''', (test_run_desc_label, file_type))

            return c.fetchall()

    def delete_entries_for_file_type(self, test_run_desc_label, file_type):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()

            # Get test_run_id by desc_label
            test_run_id = self.get_test_run_id(test_run_desc_label)
            if not test_run_id:
                raise Exception("Test run not found from db")

            # Get file_type_id by file_type
            c.execute("SELECT id FROM log_file_types WHERE type = ?", (file_type,))
            result = c.fetchone()
            if result is None:
                raise Exception("File type not found in db")
            file_type_id = result[0]

            # Get all file_ids for the specified file type in the test run
            c.execute("SELECT file_id FROM log_files WHERE test_run_id = ? AND file_type = ?", (test_run_id, file_type_id))
            file_ids = c.fetchall()

            for file_id in file_ids:
                # Delete read_write_logs entries related to the log_lines entries of the file
                c.execute("DELETE FROM read_write_logs WHERE log_lines_id IN (SELECT log_lines_id FROM log_lines WHERE file_id = ?)", (file_id,))

                # Delete log_lines entries related to the file
                c.execute("DELETE FROM log_lines WHERE file_id = ?", (file_id,))

            # Finally delete the log_files entries
            c.execute("DELETE FROM log_files WHERE test_run_id = ? AND file_type = ?", (test_run_id, file_type_id))

            conn.commit()


    def delete_test_run(self, test_run_desc_label):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()

            # Get test_run_id by desc_label
            test_run_id = self.get_test_run_id(test_run_desc_label)
            if not test_run_id:
                raise Exception("Test run not found in the database.")

            # Get all the file_ids associated with this test run
            c.execute('''
                SELECT file_id
                FROM log_files
                WHERE test_run_id = ?
            ''', (test_run_id,))
            file_ids = c.fetchall()

            # Delete entries for each file id in the test run
            for file_id_tuple in file_ids:
                file_id = file_id_tuple[0]
                self.delete_entries_for_file_type(file_id)

            # Finally delete the test_run entry
            c.execute("DELETE FROM test_runs WHERE id = ?", (test_run_id,))
            
            conn.commit()

    def show_rw_logs_for_file(self, test_run_desc_label, file_type):

        results = self.get_rw_logs_for_file(test_run_desc_label, file_type)

        print(f"Read/Write logs for file type '{file_type}' in test run '{test_run_desc_label}':")
        for row in results:
            log_lines_start, log_lines_end, time, address, operation, data, valid = row
            print(f"Start Line: {log_lines_start}, End Line: {log_lines_end}, Time: {time}, Address: {address}, Operation: {operation}, Data: {data}, Valid: {valid}")
