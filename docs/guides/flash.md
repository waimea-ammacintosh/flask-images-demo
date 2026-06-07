# Flash Messages

Give feedback to the user after operations / errors.

## Show Messages

```python
flash("Message")
flash("Success message", "success")
flash("Error message", "error")
```
*Note: the message is shown upon next page load*

## Display Messages in a Page

```jinja
{% raw %}{# Show flash messages from any previous events #}
{% include "partials/messages.jinja" %}     {% endraw %}
```
<!-- Ignore the `raw` and `endraw` tags in these Jinja code snippets - they are required for GitHub Pages -->

*Note: you can modify the code for this template partial if needed*

Messages are styled by default via the `messages.css` stylesheet, but you can customise this as you like.
