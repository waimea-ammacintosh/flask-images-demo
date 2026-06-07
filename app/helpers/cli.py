#============================================================================
# Custom Flask CLI commands for project management
#
# Provides commands:
#  - flask db-reset   Delete and recreate database
#  - flask db-clear   Clear all data (with confirmation)
#  - flask db-show    Shows the DB schema and data
#  - flask db-schema  Shows the DB schema
#  - flask db-data    Shows the DB data
#============================================================================

import click
from app.helpers.db import db_reset, db_clear, db_show, db_schema, db_data
from app.helpers.log import get_console, get_logger

console = get_console()
logger  = get_logger()


def _confirm_action(message):
    """Prompt user to confirm a destructive action"""
    console.print(f"[red]This will {message}...[/red]")
    if not click.confirm("Are you sure?"):
        console.print("[yellow]Cancelled.[/yellow]")
        return False
    return True


def register_commands(app):
    """Register custom Flask CLI commands"""

    @app.cli.command('db-reset')
    def cli_db_reset():
        """Delete and recreate the database with seed data"""
        if not _confirm_action("delete and recreate the database"):
            return
        db_reset()


    @app.cli.command('db-clear')
    def cli_db_clear():
        """Clear all data from all tables (but keep structure)"""
        if not _confirm_action("delete all existing data in the database"):
            return
        db_clear()


    @app.cli.command('db-show')
    def cli_db_show():
        """Display all table schema and data"""
        db_show()


    @app.cli.command('db-schema')
    def cli_cli_db_show_schema():
        """Display all table schema"""
        db_schema()


    @app.cli.command('db-data')
    def db_show_data():
        """Display all table data"""
        db_data()

