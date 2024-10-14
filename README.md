# Bountycatch.py with SQLite Support 🧑‍💻

This repository contains a remix of [adelaramadhina's](https://github.com/adelaramadhina/bountycatchremix) remix of Jason Haddix's  [`bountycatch.py`](https://gist.github.com/jhaddix/91035a01168902e8130a8e1bb383ae1e) script.
## Overview

A script to track multiple domains and their subdomains discovered during recon. It ensures uniqueness of entries upon ingestion and provides full-text search capabilities via FTS5 in SQLite.

## Features

- **Save multiple domains and their subdomains** into a SQLite database from text files or directly via the command line.
- **Eliminate duplicate** domain and subdomain entries.
- **Count the number of unique subdomains** per domain.
- **Delete a project domain entry** along with its subdomains.
- **Search subdomains** using full-text search.
- **Search projects (domains)** based on a query.
- **Add new projects (domains)** directly without needing to add subdomains immediately.


## Prerequisites
Python 3.x

## Setup

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/bountycatch-sqlite.git
   cd bountycatch-sqlite

## Usage
1. Adding a New Project:
  * Add a new top-level domain (project) without adding subdomains immediately:
    * `python3 bountycatch.py add-project --project example.com` or `python3 bountycatch.py add-project -p example.com`
2. Adding Subdomains
  * Add subdomains from a file:
    * `python3 bountycatch.py add --project example.com --file example_subdomains.txt` or `python3 bountycatch.py add -p example.com -f example_subdomains.txt`
  * Add Subdomains from cli:
    * `python3 bountycatch.py add --project example.com --domains "fake.test.com,blue.test.com,cake.test.com,fakecake.test.com"` or `python3 bountycatch.py add -p example.com -d "fake.test.com,blue.test.com,cake.test.com,fakecake.test.com"`
3. Print a Project's/Domain's currently stored subdomains:
  * `python3 bountycatch.py print --project example.com` or `python3 bountycatch.py print -p example.com`
4. Count the total number of subdomains for a Domain/Project:
  * `python3 bountycatch.py count --project example.com` or `python3 bountycatch.py count -p example.com`
5. Delete a Domain/Project:
  * `python3 bountycatch.py delete --project example.com`
6. Search for subodmains within a Domain/Project:
  * `python3 bountycatch.py search --project example.com --query "fake"` or `python3 bountycatch.py search -p example.com -q "fake"`
7. Search for existing Domains/Projects
  * `python3 bountycatch.py search-projects --query "example"` or `python3 bountycatch.py search-projects -q "example"`
8. Specify a Custom Database Path:
  * `python3 bountycatch.py add-project --project example.com --db /path/to/custom.db`

Below are the commands available for Bountycatch:

### Adding Subdomains
To add subdomains for a project:

```bash
python3 bountycatch.py --project xyz.com --o add --file xyz_subdomains.txt
```
### Printing Current Project Data
To display the current project's subdomains:

```
python3 bountycatch.py --project xyz.com -o print
```

### Counting Subdomains
To count the number of subdomains for the current project:

```
python3 bountycatch.py --project xyz.com -o count
```

### Deleting a Subdomain
To delete a specific subdomain from the project:

```bash
python3 bountycatch.py --project xyz.com -o delete 
```


