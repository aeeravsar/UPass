#!/bin/bash

# Convert all SVG files to PNG using rsvg-convert
# This creates white icons with transparent backgrounds for Windows compatibility

echo "Converting SVG icons to PNG format..."

for svg in *.svg; do
    if [ -f "$svg" ]; then
        png_file="${svg%.svg}.png"
        echo "Converting $svg -> $png_file"
        rsvg-convert "$svg" -w 16 -h 16 -o "$png_file"
    fi
done

echo "Conversion complete!"
echo "PNG files created:"
ls -la *.png