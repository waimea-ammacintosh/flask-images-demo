# Project Structure

```filetree
├── README.md            # Project README
│
├── Dockerfile           # Define environment and launch Flask
│
├── docker-compose.yml   # Docker run configuration
│
├── requirements.txt     # Python modules required
│
├── app/                 # Flask application
│   │
│   ├── __init__.py      # Routes and app logic
│   │
│   ├── .env             # Environment values
│   │
│   ├── templates/       # Jinja2 templates
│   │   ├── pages/       # Full page templates
│   │   └── partials/    # Reusable template parts
│   │
│   ├── static/          # Files to be served directly
│   │   ├── css/         # CSS stylesheets
│   │   ├── images/      # Images
│   │   └── js/          # Javascript files
│   │
│   ├── db/              # Database files
│   │   ├── config.py    # Database schema & seed data
│   │   └── data.sqlite  # SQLite database
│   │
│   └── helpers/         # Helper files (don't modify)
│
└── docs/                # Project documentation
    └── guides/          # Helpful guides
```
