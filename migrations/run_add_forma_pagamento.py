#!/usr/bin/env python3
"""
Runner to apply the forma_pagamento migration without importing the full application package.

Usage: run this inside the project root or container where the app code lives:
    python migrations/run_add_forma_pagamento.py

This creates a minimal Flask app, initializes the SQLAlchemy `db` from `models`,
and executes the `upgrade()` function from `migrations/000_add_forma_pagamento.py`.
"""
import importlib.util
import os
from flask import Flask

# Ensure working directory is project root
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

from models import db

# Load the migration module
spec = importlib.util.spec_from_file_location('mig', os.path.join('migrations', '000_add_forma_pagamento.py'))
mig = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mig)

# Create a minimal Flask app and configure it
app = Flask(__name__)
try:
    app.config.from_object('config.Config')
except Exception:
    print('Warning: failed to load config.Config; continuing with Flask defaults')

# Initialize extensions
db.init_app(app)

with app.app_context():
    print('Running migration: upgrade()')
    mig.upgrade()
    print('Migration upgrade() finished')
