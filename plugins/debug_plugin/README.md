# Debug Plugin

This plugin can be inserted at any point in a pipeline to probe and log the current context and config. All logs are written to `logs/debug_plugins.log` in structured JSON format.

## Features
- Logs `context`, `config`, and `pipeline` information on each run.
- Thread-safe logging.
- UI endpoint to view the log file (`/plugins/debug_plugin/status`).

## Usage
- Add `debug_plugin` to your pipeline at any point to inspect what is passed.
- View the log in the UI or by opening `logs/debug_plugins.log`.

## Security
- No secrets or sensitive information should be stored in config/context.
- Log file is only accessible to users with file access or via the status endpoint.

## Testing
- Unit tests should be added for run and logging logic.

## Structure
- `__init__.py`: Main entry and log logic.
- `config_ui.py`: FastAPI route for log display.
