import argparse
import sqlite3
import os
import sys

class DataStore:
    def __init__(self, db_path='bountycatch.db'):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;")  # Enable foreign key support
        self.cursor = self.conn.cursor()
        self._initialize_db()

    def _initialize_db(self):
        # Create projects table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            );
        ''')

        # Create subdomains table with unique constraint per project
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS subdomains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                UNIQUE(project_id, name),
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );
        ''')

        # Create FTS5 virtual table for subdomains
        self.cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS subdomains_fts USING fts5(name, content='subdomains', content_rowid='id');
        ''')

        # Create triggers to keep FTS table in sync
        self.cursor.executescript('''
            CREATE TRIGGER IF NOT EXISTS subdomains_ai AFTER INSERT ON subdomains BEGIN
                INSERT INTO subdomains_fts(rowid, name) VALUES (new.id, new.name);
            END;
            
            CREATE TRIGGER IF NOT EXISTS subdomains_ad AFTER DELETE ON subdomains BEGIN
                DELETE FROM subdomains_fts WHERE rowid = old.id;
            END;
            
            CREATE TRIGGER IF NOT EXISTS subdomains_au AFTER UPDATE ON subdomains BEGIN
                UPDATE subdomains_fts SET name = new.name WHERE rowid = old.id;
            END;
        ''')
        self.conn.commit()

    def add_project(self, project_name):
        try:
            self.cursor.execute('INSERT INTO projects (name) VALUES (?);', (project_name,))
            self.conn.commit()
            print(f"Project '{project_name}' added successfully.")
            return True
        except sqlite3.IntegrityError:
            print(f"Project '{project_name}' already exists.")
            return False

    def search_projects(self, query):
        # Use LIKE for simple pattern matching
        pattern = f"%{query}%"
        self.cursor.execute('SELECT name FROM projects WHERE name LIKE ? ORDER BY name;', (pattern,))
        return [row[0] for row in self.cursor.fetchall()]

    def add_subdomain(self, project_name, subdomain):
        project_id = self.get_project_id(project_name)
        if project_id is None:
            print(f"Project '{project_name}' does not exist. Creating it.")
            created = self.add_project(project_name)
            if not created:
                return False  # If project exists after trying to create, proceed
            project_id = self.get_project_id(project_name)
        
        try:
            self.cursor.execute('INSERT INTO subdomains (project_id, name) VALUES (?, ?);', (project_id, subdomain))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Duplicate entry

    def add_subdomains_bulk(self, project_name, subdomains):
        project_id = self.get_project_id(project_name)
        if project_id is None:
            print(f"Project '{project_name}' does not exist. Creating it.")
            created = self.add_project(project_name)
            if not created:
                return 0, 0  # If project exists after trying to create
            project_id = self.get_project_id(project_name)
        
        new_domains = 0
        duplicate_domains = 0
        for subdomain in subdomains:
            subdomain = subdomain.strip()
            if subdomain:
                added = self.add_subdomain(project_name, subdomain)
                if added:
                    new_domains += 1
                else:
                    duplicate_domains += 1
        return new_domains, duplicate_domains

    def get_subdomains(self, project_name):
        project_id = self.get_project_id(project_name)
        if project_id is None:
            print(f"Project '{project_name}' does not exist.")
            return []
        self.cursor.execute('SELECT name FROM subdomains WHERE project_id = ? ORDER BY name;', (project_id,))
        return [row[0] for row in self.cursor.fetchall()]

    def count_subdomains(self, project_name):
        project_id = self.get_project_id(project_name)
        if project_id is None:
            print(f"Project '{project_name}' does not exist.")
            return 0
        self.cursor.execute('SELECT COUNT(*) FROM subdomains WHERE project_id = ?;', (project_id,))
        return self.cursor.fetchone()[0]

    def delete_project(self, project_name):
        self.cursor.execute('DELETE FROM projects WHERE name = ?;', (project_name,))
        changes = self.conn.total_changes
        self.conn.commit()
        return changes > 0

    def project_exists(self, project_name):
        self.cursor.execute('SELECT 1 FROM projects WHERE name = ?;', (project_name,))
        return self.cursor.fetchone() is not None

    def get_project_id(self, project_name):
        self.cursor.execute('SELECT id FROM projects WHERE name = ?;', (project_name,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def search_subdomains(self, project_name, query):
        project_id = self.get_project_id(project_name)
        if project_id is None:
            print(f"Project '{project_name}' does not exist.")
            return []
        # Use parameterized query to prevent SQL injection and handle query properly
        self.cursor.execute('''
            SELECT subdomains.name 
            FROM subdomains_fts 
            JOIN subdomains ON subdomains_fts.rowid = subdomains.id
            WHERE subdomains.project_id = ? AND subdomains_fts MATCH ?;
        ''', (project_id, query))
        return [row[0] for row in self.cursor.fetchall()]

    def close(self):
        self.conn.close()

class Project:
    def __init__(self, datastore, name):
        self.datastore = datastore
        self.name = name

    def add_domains_from_file(self, filename):
        if not os.path.exists(filename):
            print(f"File '{filename}' does not exist.")
            return
        with open(filename, 'r') as file:
            subdomains = [line.strip() for line in file if line.strip()]
        new_domains, duplicate_domains = self.datastore.add_subdomains_bulk(self.name, subdomains)
        total_domains = new_domains + duplicate_domains
        duplicate_percentage = (duplicate_domains / total_domains) * 100 if total_domains > 0 else 0
        printf(f"Total domains passed: {total_domains}")
        print(f"{duplicate_domains} out of {total_domains} domains were duplicates ({duplicate_percentage:.2f}%).")
        print(f"Total new domains added: {new_domains}")

    def add_domains_from_list(self, subdomains_list):
        subdomains = [sd.strip() for sd in subdomains_list.split(',') if sd.strip()]
        if not subdomains:
            print("No valid subdomains provided.")
            return
        new_domains, duplicate_domains = self.datastore.add_subdomains_bulk(self.name, subdomains)
        total_domains = new_domains + duplicate_domains
        duplicate_percentage = (duplicate_domains / total_domains) * 100 if total_domains > 0 else 0
        print(f"{duplicate_domains} out of {total_domains} domains were duplicates ({duplicate_percentage:.2f}%).")

    def get_domains(self):
        return self.datastore.get_subdomains(self.name)

    def count_domains(self):
        if not self.datastore.project_exists(self.name):
            print(f"Error: Project '{self.name}' does not exist.")
            return
        count = self.datastore.count_subdomains(self.name)
        print(f"There are {count} subdomains in the project '{self.name}'.")

    def delete(self):
        print(f"Attempting to delete project '{self.name}'...")
        deleted = self.datastore.delete_project(self.name)
        if not deleted:
            print(f"No such project '{self.name}' to delete.")
        else:
            print(f"Project '{self.name}' deleted successfully.")

    def search_domains(self, query):
        results = self.datastore.search_subdomains(self.name, query)
        if results:
            print(f"Search results for '{query}' in project '{self.name}':")
            for domain in results:
                print(domain)
        else:
            print(f"No subdomains match the query '{query}' in project '{self.name}'.")

    def search_projects(self, query):
        results = self.datastore.search_projects(query)
        if results:
            print(f"Search results for projects matching '{query}':")
            for project in results:
                print(project)
        else:
            print(f"No projects match the query '{query}'.")

def main():
    parser = argparse.ArgumentParser(description="Manage bug bounty targets with SQLite")
    subparsers = parser.add_subparsers(dest='operation', help='Operation to perform')

    # Add Project
    parser_add_project = subparsers.add_parser('add-project', help='Add a new project (top-level domain)')
    parser_add_project.add_argument('-p', '--project', required=True, help='The project name')

    # Add Subdomains
    parser_add = subparsers.add_parser('add', help='Add subdomains to a project')
    parser_add.add_argument('-p', '--project', required=True, help='The project name')
    group = parser_add.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--file', help='The file containing domains')
    group.add_argument('-d', '--domains', help='Comma-separated list of domains to add')

    # Print Subdomains
    parser_print = subparsers.add_parser('print', help='Print subdomains of a project')
    parser_print.add_argument('-p', '--project', required=True, help='The project name')

    # Count Subdomains
    parser_count = subparsers.add_parser('count', help='Count subdomains of a project')
    parser_count.add_argument('-p', '--project', required=True, help='The project name')

    # Delete Project
    parser_delete = subparsers.add_parser('delete', help='Delete a project and its subdomains')
    parser_delete.add_argument('-p', '--project', required=True, help='The project name')

    # Search Subdomains
    parser_search = subparsers.add_parser('search', help='Search subdomains within a project')
    parser_search.add_argument('-p', '--project', required=True, help='The project name')
    parser_search.add_argument('-q', '--query', required=True, help='Search query for subdomains')

    # Search Projects
    parser_search_projects = subparsers.add_parser('search-projects', help='Search for projects (domains)')
    parser_search_projects.add_argument('-q', '--query', required=True, help='Search query for projects')

    # Common argument for database path
    parser.add_argument('--db', help='Path to SQLite database file', default='bountycatch.db')

    args = parser.parse_args()

    if args.operation is None:
        parser.print_help()
        sys.exit(1)

    datastore = DataStore(db_path=args.db)

    # Initialize Project object if operation requires it
    if args.operation in ['add', 'print', 'count', 'delete', 'search']:
        project = Project(datastore, args.project)

    def add_project_operation():
        datastore.add_project(args.project)

    def add_subdomains_operation():
        if args.file:
            project.add_domains_from_file(args.file)
        elif args.domains:
            project.add_domains_from_list(args.domains)
        else:
            print("You must provide either a file with the 'add' operation using -f/--file or a comma-separated list using -d/--domains.")
            return

    def print_operation():
        domains = project.get_domains()
        if domains:
            print(f"Subdomains for project '{args.project}':")
            for domain in domains:
                print(domain)
        else:
            print(f"No subdomains found for project '{args.project}'.")

    def delete_operation():
        project.delete()

    def count_operation():
        project.count_domains()

    def search_subdomains_operation():
        if args.query is None:
            print("You must provide a search query with the 'search' operation using -q or --query.")
            return
        project.search_domains(args.query)

    def search_projects_operation():
        if args.query is None:
            print("You must provide a search query with the 'search-projects' operation using -q or --query.")
            return
        # Initialize a temporary Project object without a specific project
        temp_project = Project(datastore, "")
        temp_project.search_projects(args.query)

    operations = {
        'add-project': add_project_operation,
        'add': add_subdomains_operation,
        'print': print_operation,
        'delete': delete_operation,
        'count': count_operation,
        'search': search_subdomains_operation,
        'search-projects': search_projects_operation
    }

    operation_function = operations.get(args.operation)
    if operation_function:
        operation_function()
    else:
        print(f"Invalid operation: {args.operation}")
        parser.print_help()

    datastore.close()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
