"""
Delete the gather_plugin config for a given pipeline from the database.
Usage: python3 scripts/delete_gather_plugin_config.py [pipeline]
If pipeline is not provided, defaults to 'default'.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.plugin_config_repo import PluginConfigRepo
from db.config_storage import ConfigStorage

def main():
    pipeline = sys.argv[1] if len(sys.argv) > 1 else 'default'
    repo = PluginConfigRepo(ConfigStorage())
    repo.delete_plugin_config('gather_plugin', pipeline)
    print(f"Deleted gather_plugin config for pipeline '{pipeline}'")

if __name__ == "__main__":
    main()
