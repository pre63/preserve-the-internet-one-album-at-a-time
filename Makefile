.PHONY: install run serve clean help

# Variables
album_id ?= 

# Install dependencies
install:
	@python3 -m venv .venv
	@. .venv/bin/activate && pip install -r requirements.txt

# Run the album downloader
run:
ifndef album_id
	@echo "Error: album_id is not set. Use 'make run album_id=your_album_id'."
	@exit 1
endif
	@. .venv/bin/activate && python album_download.py $(album_id)

# Serve the downloaded albums
serve:
	@. .venv/bin/activate && python album_server.py

# Clean downloaded albums (optional: adjust the path as needed)
clean:
	@rm -rf downloaded_albums/

# Display help
help:
	@echo "Available commands:"
	@echo "  make install           Install the required dependencies."
	@echo "  make run album_id=... Run the album downloader with the specified album_id."
	@echo "  make serve             Start the local server to view downloaded albums."
	@echo "  make clean             Remove downloaded albums."
	@echo "  make help              Show this help message."
