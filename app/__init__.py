#===========================================================
# APP NAME HERE
# By YOUR NAME HERE
#===========================================================

from flask import Flask, request, session, render_template, flash, redirect, send_file, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from os import getenv
from io import BytesIO
import html
from app.helpers import *
import os
import uuid
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads')


# Create the app
app = Flask(__name__)


#===========================================================
# App Routes Handlers
#===========================================================

#-----------------------------------------------------------
# Welcome page
#-----------------------------------------------------------
@app.get("/")
def show_welcome():
    return render_template("pages/welcome.jinja")


#-----------------------------------------------------------
# Creature list page - Show all the creatures
#-----------------------------------------------------------
@app.get("/creatures")
def show_all_creatures():
    with connect_db() as db:
        sql = """
            SELECT id, species, name, image_file
            FROM creatures
        """
        params = ()
        creatures = db.execute(sql, params).fetchall()

        return render_template("pages/creature_list.jinja", creatures=creatures)


#-----------------------------------------------------------
# Help page - Show some help
#-----------------------------------------------------------
@app.get("/help")
def show_help():

    flash("Flash test message")
    flash("Flash test message with a longer bit of text")
    flash("Success test message", "success")
    flash("Error test message", "error")

    return render_template("pages/help.jinja")

#-----------------------------------------------------------
# New Creature Page - Show new creature form
#-----------------------------------------------------------
@app.get("/new/creature")
def show_creature_form():

    return render_template("pages/creature_form.jinja")


#-----------------------------------------------------------
# New Creature Form - Handle new creature form
#-----------------------------------------------------------
@app.post("/new/creature")
def add_creature():
    # Get the normal text fields from the form
    name = request.form.get('name', '').strip()
    name = html.escape(name)
    species = request.form.get('species', '').strip()
    species = html.escape(species)

    # Get the file selected via the form
    image = request.files.get('image', None)
    if not image or image.filename == '':
        flash("There was a problem uploading the image", "error")
        return redirect("/new/creature")

    # Sanitise filename and make it unique
    filename = secure_filename(image.filename)
    random_prefix = uuid.uuid4().hex[:12]
    unique_filename = f"{random_prefix}_{filename}"

    # Get the path of the upload folder
    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)

    # Save file to disk
    image.save(filepath)

    # Add the form data and the upload filename to the DB
    with connect_db() as db:
        sql = "INSERT INTO creatures (name, species, image_file) VALUES (?, ?, ?)"
        params = (name, species, unique_filename)
        db.execute(sql, params)

        flash(f"'{name}' the '{species}' added", "success")
        return redirect("/new/creature")


#-----------------------------------------------------------
# Search creatures
#-----------------------------------------------------------
@app.get("/search")
def process_search():
    search_term = request.args.get('q','')
    search_match = f"%{search_term}%"
    search_species = request.args.get('species','')
    species_match = f"%{search_species}%"

    with connect_db() as db:
        sql = """
            SELECT id, species, name, image_file
            FROM creatures
            WHERE name LIKE ?
            AND species LIKE ?
        """
        params = (search_match, species_match)
        creatures = db.execute(sql, params).fetchall()
        sql2 = """
                SELECT DISTINCT species FROM creatures ORDER BY species ASC
            """
        params2 = ()
        species = db.execute(sql2, params2).fetchall()
        species_list = [creature['species'] for creature in species]

        return render_template("pages/creature_list.jinja", creatures=creatures, search_term=search_term, species_list=species_list, species=search_species)


#-----------------------------------------------------------
# Handle creature delete
#-----------------------------------------------------------
@app.get("/delete/<int:id>")
def delete_creature(id):
        with connect_db() as db:
            sql = "SELECT name FROM creatures WHERE id=?"
            params = (id,)
            creature = db.execute(sql, params).fetchone()
            sql2 = "DELETE FROM creatures WHERE id=?"
            delete = db.execute(sql2, params)
            flash(f"Creature {creature.name} <i>desposed</i>", 'success')

        return redirect("/creatures")

#===========================================================
# Configure the app
#===========================================================
load_dotenv()
app.config.from_prefixed_env()
init_logging(app)
init_text_filters(app)
init_date_filters(app)
init_error_handlers(app)
init_database()
register_commands(app)

