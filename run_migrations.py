#!/usr/bin/env python
"""
Simple script to run Django migrations
Usage: python run_migrations.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avvento_hrmis.settings')
django.setup()

# Run migrations
from django.core.management import call_command

print("=" * 70)
print("Running Django Migrations")
print("=" * 70)

try:
    # Run migrate command
    print("\n[1/1] Applying migrations...")
    call_command('migrate', verbosity=2)
    print("\n" + "=" * 70)
    print("✅ ALL MIGRATIONS APPLIED SUCCESSFULLY!")
    print("=" * 70)
    
except Exception as e:
    print("\n" + "=" * 70)
    print("❌ ERROR DURING MIGRATION")
    print("=" * 70)
    print(f"Error: {str(e)}")
    sys.exit(1)
