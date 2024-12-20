#!/usr/bin/env python3

import os
import json
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import unquote
from jinja2 import Template

MASTER_INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Albums</title>
    <style>
        body {
            font-family: "Futura", "Helvetica", sans-serif;
            margin: 0;
            padding: 0;
            background-color: #ede6db;
            color: #2c2a29;
        }
        .container {
            width: 80%;
            margin: 20px auto;
            background: #fff;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        ul {
            list-style: none;
            padding: 0;
        }
        li {
            margin-bottom: 15px;
        }
        a {
            color: #d87c43;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        h1 {
            font-size: 2.5em;
            font-weight: bold;
            color: #6a5c4e;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Albums</h1>
        <ul>
            {% for album in albums %}
            <li><a href="/album/{{ album }}">{{ album }}</a></li>
            {% endfor %}
        </ul>
    </div>
</body>
</html>
"""

ALBUM_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ album_id }}</title>
    <style>
        body {
            font-family: "Futura", "Helvetica", sans-serif;
            margin: 0;
            padding: 0;
            background-color: #ede6db;
            color: #2c2a29;
        }
        .container {
            max-width: 1200px;
            margin: 20px auto;
            background: #fff;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }
        .gallery-item {
            width: 150px; /* Fixed thumbnail width */
            height: 150px; /* Fixed thumbnail height */
            overflow: hidden;
            border-radius: 5px;
            background: #f4efe9;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .gallery-item img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        a {
            color: #d87c43;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        h1 {
            font-size: 2.2em;
            font-weight: bold;
            color: #6a5c4e;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Album: {{ album_id }}</h1>
        <div class="gallery">
            {% for photo in photos %}
            <div class="gallery-item">
                <a href="/album/{{ album_id }}/photo/{{ photo['id'] }}"><img src="/albums/{{ album_id }}/{{ photo['id'] }}.jpg" alt="{{ photo['title'] }}"></a>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

PHOTO_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: "Futura", "Helvetica", sans-serif;
            margin: 0;
            padding: 0;
            background-color: #ede6db;
            color: #2c2a29;
        }
        .container {
            width: 80%;
            margin: 20px auto;
            background: #fff;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            text-align: center;
        }
        img {
            max-width: 100%;
            height: auto;
            margin-bottom: 20px;
            border-radius: 5px;
        }
        nav {
            display: flex;
            justify-content: space-between;
            margin-top: 20px;
        }
        a {
            color: #d87c43;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        h1 {
            font-size: 2.5em;
            font-weight: bold;
            color: #6a5c4e;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ title }}</h1>
        <img src="/albums/{{ album_id }}/{{ photo_id }}.jpg" alt="{{ title }}">
        <p>{{ description }}</p>
        <p>{{ date_taken }}</p>
        <p><a href="https://www.flickr.com/photos/{{ owner_id }}" target="_blank">{{ owner }}</a></p>
        <p><a href="{{ original_link }}" target="_blank">View on Flickr</a></p>
        <nav>
            {% if prev_photo %}
            <a href="/album/{{ album_id }}/photo/{{ prev_photo }}">← Previous</a>
            {% endif %}
            {% if next_photo %}
            <a href="/album/{{ album_id }}/photo/{{ next_photo }}">Next →</a>
            {% endif %}
        </nav>
    </div>
</body>
</html>
"""


class AlbumServerHandler(SimpleHTTPRequestHandler):
  def do_GET(self):
    if self.path == "/":
      self.serve_master_index()
    elif self.path.startswith("/album/") and "/photo/" not in self.path:
      album_id = self.path.split("/")[2]
      self.serve_album(album_id)
    elif self.path.startswith("/album/") and "/photo/" in self.path:
      parts = self.path.split("/")
      album_id = parts[2]
      photo_id = parts[4]
      self.serve_photo(album_id, photo_id)
    elif self.path.startswith("/albums/"):
      self.serve_local_file()
    else:
      self.send_error(404, "Page not found")

  def serve_local_file(self):
    # Serve images or other files in the /albums directory
    file_path = unquote(self.path.lstrip("/"))
    if not os.path.exists(file_path):
      self.send_error(404, "File not found")
      return

    mime_type = "application/octet-stream"
    if file_path.endswith(".jpg"):
      mime_type = "image/jpeg"

    self.send_response(200)
    self.send_header("Content-type", mime_type)
    self.end_headers()
    with open(file_path, "rb") as f:
      self.wfile.write(f.read())

  def serve_master_index(self):
    albums_dir = "albums"
    albums = [
        album for album in os.listdir(albums_dir)
        if os.path.isdir(os.path.join(albums_dir, album))
    ]

    template = Template(MASTER_INDEX_TEMPLATE)
    master_index_html = template.render(albums=albums)

    self.send_response(200)
    self.send_header("Content-type", "text/html")
    self.end_headers()
    self.wfile.write(master_index_html.encode("utf-8"))

  def serve_album(self, album_id):
    album_dir = os.path.join("albums", album_id)
    if not os.path.exists(album_dir):
      self.send_error(404, "Album not found")
      return

    metadata_files = [f for f in os.listdir(album_dir) if f.endswith(".json")]
    photos = []
    for metadata_file in metadata_files:
      with open(os.path.join(album_dir, metadata_file), "r") as f:
        metadata = json.load(f)
        photos.append({
            "id": metadata["id"],
            "title": metadata["title"]["_content"],
        })

    template = Template(ALBUM_TEMPLATE)
    album_html = template.render(album_id=album_id, photos=photos)

    self.send_response(200)
    self.send_header("Content-type", "text/html")
    self.end_headers()
    self.wfile.write(album_html.encode("utf-8"))

  def serve_photo(self, album_id, photo_id):
    album_dir = os.path.join("albums", album_id)
    metadata_file = os.path.join(album_dir, f"{photo_id}.json")
    if not os.path.exists(metadata_file):
      self.send_error(404, "Photo not found")
      return

    with open(metadata_file, "r") as f:
      metadata = json.load(f)

    metadata_files = sorted(
        [f.replace(".json", "") for f in os.listdir(album_dir) if f.endswith(".json")]
    )
    photo_index = metadata_files.index(photo_id)
    prev_photo = metadata_files[photo_index - 1] if photo_index > 0 else None
    next_photo = metadata_files[photo_index + 1] if photo_index < len(metadata_files) - 1 else None

    template = Template(PHOTO_TEMPLATE)
    photo_html = template.render(
        album_id=album_id,
        photo_id=photo_id,
        title=metadata["title"]["_content"],
        description=metadata["description"]["_content"],
        date_taken=metadata["dates"]["taken"],
        owner=metadata["owner"]["username"],
        owner_id=metadata["owner"]["nsid"],
        original_link=metadata["urls"]["url"][0]["_content"],
        prev_photo=prev_photo,
        next_photo=next_photo,
    )

    self.send_response(200)
    self.send_header("Content-type", "text/html")
    self.end_headers()
    self.wfile.write(photo_html.encode("utf-8"))


def run_server(port=8000):
  os.chdir(os.path.dirname(__file__))
  handler = AlbumServerHandler
  httpd = HTTPServer(("localhost", port), handler)
  print(f"Serving albums at http://localhost:{port}")
  httpd.serve_forever()


if __name__ == "__main__":
  run_server()
