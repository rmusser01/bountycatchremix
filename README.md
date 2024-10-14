# rmusser01's Bountycatch.py remix 🤸

This repository contains a remix of [adelaramadhina's](https://github.com/adelaramadhina/bountycatchremix) remix of Jason Haddix's  [`bountycatch.py`](https://gist.github.com/jhaddix/91035a01168902e8130a8e1bb383ae1e) script.

## Overview
Script to track Apex + Subdomains discovered during recon.
Deduplicates upon entry. Unique record checking upon ingestion
SQLite as the DB with Full-Text-Search via FTS5,


## Features (as for now)

- Save domains and subdomains into a database from text files.
- Eliminate duplicate domain and subdomain entries.
- Count the number of unique subdomains from a domain.
- Delete a project domain entry.

## Prerequisites
Python

## Usage
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


