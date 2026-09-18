#!/bin/bash
# Renames the 19 daily video files for Days 35-53 to match the
# Media/tcwa/day{N}.mp4 convention.
# Run from the root of your social-poster repo:
#   bash rename_videos.sh

set -e

echo "Renaming video files..."

mv "Media/tcwa/TCWA Day 35 IGTT.mp4"      "Media/tcwa/day35.mp4"
mv "Media/tcwa/TCWA Day 36 FB Card.mp4"   "Media/tcwa/day36.mp4"
mv "Media/tcwa/TCWA Day 37 FB Card.mp4"   "Media/tcwa/day37.mp4"
mv "Media/tcwa/TCWA Day 38 FB Card.mp4"   "Media/tcwa/day38.mp4"
mv "Media/tcwa/TCWA Day 39 FB Card.mp4"   "Media/tcwa/day39.mp4"
mv "Media/tcwa/TCWA Day 40 FB Card.mp4"   "Media/tcwa/day40.mp4"
mv "Media/tcwa/TCWA Day 41 FB Card.mp4"   "Media/tcwa/day41.mp4"
mv "Media/tcwa/TCWA Day 42 FB Card.mp4"   "Media/tcwa/day42.mp4"
mv "Media/tcwa/TCWA Day 43 FB Card.mp4"   "Media/tcwa/day43.mp4"
mv "Media/tcwa/TCWA Day 44 FB Card.mp4"   "Media/tcwa/day44.mp4"
mv "Media/tcwa/TCWA Day 45 FB Card.mp4"   "Media/tcwa/day45.mp4"
mv "Media/tcwa/TCWA Day 46 FB Card.mp4"   "Media/tcwa/day46.mp4"
mv "Media/tcwa/TCWA Day 47 FB Card.mp4"   "Media/tcwa/day47.mp4"
mv "Media/tcwa/TCWA Day 48 FB Card.mp4"   "Media/tcwa/day48.mp4"
mv "Media/tcwa/TCWA Day 49 FB Card.mp4"   "Media/tcwa/day49.mp4"
mv "Media/tcwa/TCWA Day 50 FB Card.mp4"   "Media/tcwa/day50.mp4"
mv "Media/tcwa/TCWA Day 51 FB Card.mp4"   "Media/tcwa/day51.mp4"
mv "Media/tcwa/TCWA Day 52 FB Card.mp4"   "Media/tcwa/day52.mp4"
mv "Media/tcwa/TCWA Day 53 FB Card.mp4"   "Media/tcwa/day53.mp4"

echo "Done. Final video files:"
find Media/tcwa -maxdepth 1 -name "day*.mp4" | sort
