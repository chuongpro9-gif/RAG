import sys
import os
from pathlib import Path

def print_result(name, is_pass, detail=""):
    status = "[PASS]" if is_pass else "[FAIL]"
    print(f"{status} {name}: {detail}")
    return is_pass

def check_env():
    print("--- BƯỚC 0: KIỂM TRA MÔI TRƯỜNG ---")
    all_pass = True

    # 1. Python version
    py_ver = sys.version.split(' ')[0]
    all_pass &= print_result("Python", True, py_ver)

    # 2. Virtual environment
    in_venv = sys.prefix != sys.base_prefix
    print_result("Virtual environment", in_venv, sys.prefix)
    # Don't strictly fail if not in venv, but it's good to know.

    # 3. Data files
    base_dir = Path(__file__).parent
    metadata_path = base_dir / "ner_kb" / "metadata.csv"
    content_path = base_dir / "ner_kb" / "content.csv"
    
    has_metadata = metadata_path.exists()
    has_content = content_path.exists()
    
    all_pass &= print_result("metadata.csv", has_metadata, str(metadata_path))
    all_pass &= print_result("content.csv", has_content, str(content_path))

    # 4. Python packages
    packages = ["pandas", "bs4", "dotenv", "google.genai", "neo4j"]
    missing_packages = []
    for pkg in packages:
        try:
            __import__(pkg)
        except ImportError:
            missing_packages.append(pkg)
            
    if missing_packages:
        all_pass &= print_result("Python packages", False, f"Missing: {', '.join(missing_packages)}")
    else:
        all_pass &= print_result("Python packages", True, "All required packages installed")

    # 5. .env Configuration
    from dotenv import load_dotenv
    env_path = base_dir / ".env"
    has_env = env_path.exists()
    if has_env:
        load_dotenv(env_path)
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    all_pass &= print_result("Gemini configuration", bool(gemini_key), "GEMINI_API_KEY is set (value hidden)" if gemini_key else "Missing GEMINI_API_KEY")

    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USER")
    neo4j_pwd = os.getenv("NEO4J_PASSWORD")
    
    has_neo4j_config = bool(neo4j_uri and neo4j_user and neo4j_pwd)
    all_pass &= print_result("Neo4j configuration", has_neo4j_config, "Neo4j URI/USER/PASSWORD are set (values hidden)" if has_neo4j_config else "Missing Neo4j config in .env")

    # 6. Test Neo4j connection (if config exists and package is installed)
    if has_neo4j_config and "neo4j" not in missing_packages:
        from neo4j import GraphDatabase
        try:
            driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pwd))
            driver.verify_connectivity()
            print_result("Neo4j connectivity", True, "Successfully connected to Neo4j")
            driver.close()
        except Exception as e:
            all_pass &= print_result("Neo4j connectivity", False, f"Connection failed: {e}")
            
    print("-" * 35)
    if all_pass:
        print("ALL PASSED! Ready for Bước 1.")
    else:
        print("SOME CHECKS FAILED. Please fix them before proceeding.")

if __name__ == "__main__":
    check_env()
