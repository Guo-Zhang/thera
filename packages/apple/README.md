# quanttide-apple

Apple ecosystem Python SDK - Shortcuts-based integration for Notes, Contacts, Calendar, Reminders.

## Installation

```bash
pip install quanttide-apple
```

## Usage

```python
from quanttide_apple import NotesAdapter, run_shortcut, list_shortcuts

# List all shortcuts
shortcuts = list_shortcuts()

# Run a shortcut
result = run_shortcut("My Shortcut")

# Use Notes adapter
notes = NotesAdapter()
data = notes.fetch(folder="思考")
```
