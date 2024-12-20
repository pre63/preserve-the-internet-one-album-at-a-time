#!/usr/bin/env python3

import os
import sys
import json
import requests

"""
Replace with your API key
You can get an anonymous key for public data access from your browser 
  inspector for API requests as `api_key`.
"""
API_KEY = "8c7914821492f676d9bbd6ddb68cc62b"


def fetch_photoset_photos(api_key, photoset_id):
  url = "https://api.flickr.com/services/rest/"
  params = {
      "method": "flickr.photosets.getPhotos",
      "api_key": api_key,
      "photoset_id": photoset_id,
      "extras": "url_o,url_l,url_c,url_z,url_m",  # Request multiple sizes
      "format": "json",
      "nojsoncallback": "1"
  }
  response = requests.get(url, params=params)
  response.raise_for_status()
  data = response.json()

  if data.get("stat") != "ok":
    raise Exception(f"Flickr API error: {data.get('message')}")

  photos = data["photoset"]["photo"]

  # Add an index to each photo to preserve album order
  for idx, photo in enumerate(photos):
    photo["index"] = idx

  return photos


def fetch_photo_info(api_key, photo_id):
  url = "https://api.flickr.com/services/rest/"
  params = {
      "method": "flickr.photos.getInfo",
      "api_key": api_key,
      "photo_id": photo_id,
      "format": "json",
      "nojsoncallback": "1"
  }
  response = requests.get(url, params=params)
  response.raise_for_status()
  data = response.json()

  if data.get("stat") != "ok":
    raise Exception(f"Flickr API error: {data.get('message')} for photo ID {photo_id}")

  return data["photo"]


def determine_best_photo_url(photo_info):
  sizes = ["url_o", "url_l", "url_c", "url_z", "url_m"]  # Order of preference
  for size in sizes:
    if size in photo_info:
      return photo_info[size]
  raise Exception("No downloadable photo URL found")


def download_photo(url, save_path):
  response = requests.get(url, stream=True)
  response.raise_for_status()
  with open(save_path, "wb") as f:
    for chunk in response.iter_content(chunk_size=8192):
      f.write(chunk)


def save_metadata(metadata, save_path):
  with open(save_path, "w") as f:
    json.dump(metadata, f, indent=4)


def main(argv):
  if len(argv) < 2:
    print("Usage: script.py <photoset-id>")
    sys.exit(1)

  photoset_id = argv[1]

  if not API_KEY:
    print("No API key found")
    sys.exit(1)

  try:
    photos = fetch_photoset_photos(API_KEY, photoset_id)
  except Exception as e:
    print(f"Error fetching photos: {e}")
    sys.exit(1)

  album_dir = os.path.join("albums", photoset_id)
  os.makedirs(album_dir, exist_ok=True)

  for photo in photos:
    photo_id = photo["id"]
    try:
      print(f"Fetching detailed info for photo ID {photo_id}...")
      photo_info = fetch_photo_info(API_KEY, photo_id)

      # Determine the best photo URL
      photo_url = determine_best_photo_url(photo)
      if not photo_url:
        print(f"Warning: No downloadable photo URL found for photo ID {photo_id}")
        continue

      # Save photo and metadata
      file_name = f"{photo_id}.jpg"
      metadata_file = f"{photo_id}.json"
      photo_path = os.path.join(album_dir, file_name)
      metadata_path = os.path.join(album_dir, metadata_file)

      print(f"Downloading photo {photo_url} to {photo_path}...")
      download_photo(photo_url, photo_path)

      print(f"Saving metadata to {metadata_path}...")
      save_metadata(photo_info, metadata_path)

    except Exception as e:
      print(f"Error processing photo {photo_id}: {e}")


if __name__ == "__main__":
  main(sys.argv)
