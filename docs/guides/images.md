# Image / File Uploading and Access

How you deal with images / files depends on the size / number of them...

- Relatively small images / files (100kB or less), and not too many of them:
    - Store these **directly in the database** as **Binary Large OBject (BLOB)** data
    - See the BLOB method below

- Large images / files, and/or many of them:
    - Database BLOBs would result in a very large SQLite database file
    - **Upload the files** to a folder
    - Store os **reference to the uploaded file** in the DB
    - See the Upload method below



## Form which Allows File Uploads

If a form is uploading images / files, it needs to be a `multipart` form.

In addition, the file input control should specify the type(s) of file that can be uploaded using the `accept` parameter. Examples:
- **PNG** images only: `"image/png"`
- **Common image** types: `"image/png, image/jpeg, image/gif, image/webp"`
- **All image** types: `"image/*"`
- **Text** files only: `".txt"`
- **Word** files only: `".docx"`


```html
<form method="post" action="/club" enctype="multipart/form-data">
    <label>
        Name
        <input name="name" type="text" required>
    </label>

    <label>
        Logo
        <input
            name="logo"
            type="file"
            accept="image/png, image/jpeg, image/gif, image/webp"
            required
        >
    </label>

    <button>Add Club</button>
</form>
```


## BLOB Method - Images in DB

In this method, we store the image / file data directly in the DB as a **BLOB**.

**Benefits:**
- Simpler deployment - everything in one database file
- File / image data is deleted automatically when records are deleted
- Easy to back up the DB including all image / file data
- No file permission issues or filesystem complexity

**Trade-offs:**
- Database can grow very large - Uses a lot of memory
- Query performance degrades - SQLite loads entire rows into memory
- Cannot use web server's efficient static file serving


### Setup the database

Define the DB schema with a **BLOB** field, and in the case of images, you will need to store the **[MIME type](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/MIME_types/Common_types)** to identify the image type when accessing it...

```sql
CREATE TABLE clubs (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT NOT NULL,
    logo_data BLOB NOT NULL,
    logo_mime TEXT NOT NULL
)
```

### Setup a form processing route and function

Most data submitted by a form is accessed via `request.form.get(...)`. The uploaded image / file data is handled separately from the other form data values, coming via `request.files.get(...)`...

```python
@app.post("/club")
def add_club():
    # Get the normal text fields from the form
    name = request.form.get('name', '').strip()
    name = html.escape(name)

    # Get the file selected via the form
    logo = request.files.get('logo', None)
    if not logo or logo.filename == '':
        flash("There was a problem uploading the image", "error")
        return redirect("/")

    # Get the file binary data, and the file MIME type
    logo_data = logo.read()
    logo_mime = logo.mimetype

    # Add the form data and file binary data to DB
    with connect_db() as db:
        sql = """
            INSERT INTO clubs (name, logo_data, logo_mime)
            VALUES (?, ?, ?)
        """
        params = (name, logo_data, logo_mime)
        db.execute(sql, params)

        flash(f"Club '{name}' added", "success")
        return redirect("/")
```

### Serve uploaded images using `<img>`

When accessing database entries, **do not request the image data** along with other data values. Instead, **use a separate HTTP request for the image data via an `<img>` tag** on the page you want to show the image, and provide a dedicated route for this...

#### 1. Get data for the page (but *not* the image)

```python
@app.get('/club/<int:id>')
def get_club(id):
    with connect_db() as db:
        sql = "SELECT name FROM clubs WHERE id=?"
        params = (id,)
        club = db.execute(sql, params).fetchone()

        return render_template("pages/club.jinja", club=club)
```

#### 2. Template to show data with an `<img>` tag

The source of the image is set to a special image loading route, `/club/{{ club.id }}/logo`...

```jinja
{% raw %}{# Show the club info and request image... #}

<h1>Welcome to '{{ club.name }}' Club!</h1>

<img src="/club/{{ club.id }}/logo" alt="{{ club.name }} logo">    {% endraw %}
```
<!-- Ignore the `raw` and `endraw` tags in these Jinja code snippets - they are required for GitHub Pages -->

#### 3. Route to serve up the image

This route retrieves the image data and MIME type, then creates an image file and returns this...

```python
@app.get('/club/<int:id>/logo')
def get_club_logo(id):
    with connect_db() as db:
        sql = "SELECT logo_data, logo_mime FROM clubs WHERE id=?"
        params = (id,)
        logo = db.execute(sql, params).fetchone()

        if not logo:
            return render_template("pages/_404.jinja"), 404

        return make_response(
            send_file(
                BytesIO(logo["logo_data"]),
                mimetype=logo["logo_mime"]
            )
        )
```

*Using a separate HTTP request allows the browser to load and render the page without having to wait for the image data to load (which could take a while)*


### Optional: Provide Download Links for Uploaded Files

If you have allowed files such as `.txt` to be uploaded, you might want to allow these to be downloaded later via a route...

```python
@app.get('/club/<int:id>/info/download')
def download_club_info(id):
    with connect_db() as db:
        sql = "SELECT name, info_doc_data FROM clubs WHERE id=?"
        params = (id,)
        club = db.execute(sql, params).fetchone()

        if not club or not club["info_doc_data"]:
            return render_template("pages/_404.jinja"), 404

        return send_file(
            BytesIO(club["info_doc_data"]),
            mimetype="text/plain",
            download_name=f"{club['name']}-info.txt",
            as_attachment=True
        )
```

---

## Upload Method - Images as Files

In this method, we upload files to `static/uploads/` folder and store only the **filename** in the database.

**Benefits:**
- Flask serves static files efficiently
- Database stays small and fast
- Easy to back up files separately
- Can use CDN or cloud storage later (S3, Azure Blob, etc.)

**Trade-offs:**
- Need to manage file deletion when records are deleted
- File permissions and security considerations
- Requires disk space on server


### Setup the database

Define the DB schema to store the filename of he image / file as a **TEXT** field...


```sql
CREATE TABLE clubs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    logo_filename  TEXT NOT NULL
)
```

### Setup the upload folder

Create `app/static/uploads/` folder.

> [!NOTE]
> You may need to adjust permissions so that Flask can write to the folder, and you may want to add it to `.gitignore`


### Setup a form processing route and function

Most data submitted by a form is accessed via `request.form.get(...)`. The uploaded image / file data is handled separately from the other form data values, coming via `request.files.get(...)`...

Use `secure_filename()` to sanitise uploaded filenames and save to disk...

```python
import os
import uuid
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads')

@app.post("/club")
def add_club():
    # Get the normal text fields from the form
    name = request.form.get('name', '').strip()
    name = html.escape(name)

    # Get the file selected via the form
    logo = request.files.get('logo', None)
    if not logo or logo.filename == '':
        flash("There was a problem uploading the image", "error")
        return redirect("/")

    # Sanitise filename and make it unique
    filename = secure_filename(logo.filename)
    random_prefix = uuid.uuid4().hex[:12]
    unique_filename = f"{random_prefix}_{filename}"

    # Get the path of the upload folder
    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)

    # Save file to disk
    logo.save(filepath)

    # Add the form data and the upload filename to the DB
    with connect_db() as db:
        sql = "INSERT INTO clubs (name, logo_filename) VALUES (?, ?)"
        params = (name, unique_filename)
        db.execute(sql, params)

        flash(f"Club '{name}' added", "success")
        return redirect("/")
```

### Serve images from the upload folder

Simply reference the file in the `static/uploads/` folder...

```jinja
{% raw %}<h1>Welcome to '{{ club.name }}' Club!</h1>

<img src="/static/uploads/{{ club.logo_file }}" alt="{{ club.name }} logo">   {% endraw %}
```
<!-- Ignore the `raw` and `endraw` tags in these Jinja code snippets - they are required for GitHub Pages -->


### Optional: Provide Download Links for Uploaded Files

If you want to force a file download (rather than display in browser), use `send_from_directory()` with `as_attachment=True`...

```python
from flask import send_from_directory

@app.get('/club/<int:id>/info/download')
def download_club_info(id):
    with connect_db() as db:
        sql = "SELECT name, info_filename FROM clubs WHERE id=?"
        params = (id,)
        club = db.execute(sql, params).fetchone()

        if not club or not club["info_filename"]:
            return render_template("pages/_404.jinja"), 404

        return send_from_directory(
            UPLOAD_FOLDER,
            club["info_filename"],
            as_attachment=True,
            download_name=f"{club['name']}-info.txt"
        )
```