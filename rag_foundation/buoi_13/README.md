# Wiki Risk Graph Project

This project builds a Wiki Risk Graph using Markdown (for Obsidian viewing) and imports it into Neo4j for Graph RAG analysis.

## Setup
```bash
pip install pandas neo4j python-dotenv
```

## Running the project

Please run the scripts in the following order:

1. **Inspect Data**
   ```bash
   python scripts/inspect_data.py
   ```
   Checks raw CSV data to ensure data integrity and outputs statistics.

2. **Build Entities and Relations**
   ```bash
   python scripts/build_entities.py
   ```
   Transforms raw CSVs into normalized `outputs/entities.csv` and `outputs/relations.csv`.

3. **Build Wiki Markdown**
   ```bash
   python scripts/build_wiki.py
   ```
   Generates the Obsidian-compatible Markdown vault inside the `wiki/` directory.

4. **Validate Wiki**
   ```bash
   python scripts/validate_wiki.py
   ```
   Validates the generated markdown files and saves a report to `outputs/wiki_validation_report.md`.

5. **Open with Obsidian**
   - Open Obsidian
   - Click "Open folder as vault"
   - Select the `wiki/` directory
   - Open `Home.md`
   - Use the **Graph View** feature to visualize the knowledge graph.

6. **Load to Neo4j**
   ```bash
   python scripts/load_neo4j.py
   ```
   Imports the generated nodes and edges into Neo4j database using Cypher queries. Make sure Neo4j is running locally and the `.env` configuration is correct.
