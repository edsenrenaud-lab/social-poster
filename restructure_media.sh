#!/bin/bash
# Restructures Media/ for the TCWA Days 34-63 campaign.
# Run this from the root of your social-poster repo:
#   bash restructure_media.sh
#
# What it does:
#   1. Renames + moves all 30 FB cards from Media/7158987651357969486/
#      into Media/tcwa/day{N}.jpg, based on verified quote-text matching
#      (the numbered filenames were NOT in day order - confirmed by
#      reading each image's actual text).
#   2. Renames + moves all 12 carousels' 7 slides each from their
#      individual Media/day{N}-carousel-1/ folders into
#      Media/tcwa/day{N}-carousel-{1-7}.png (kept as .png, matching
#      the real file format Canva exported).
#   3. Removes the now-empty source folders.
#   4. Does NOT touch Media/tcwa/Day N.mp4, Media/tcwa/Jpeg/, or
#      test1/2/3.jpg - those are left exactly as they are.
#
# Safe to review before running: every line below is an explicit,
# individual mv command - nothing is done with a loop or pattern
# that could silently do the wrong thing.

set -e  # stop immediately if anything fails, rather than continuing on a bad state

echo "Renaming and moving FB cards..."

mv "Media/7158987651357969486/14_Day 1.jpg" "Media/tcwa/day34.jpg"
mv "Media/7158987651357969486/6_Day 1.jpg"  "Media/tcwa/day35.jpg"
mv "Media/7158987651357969486/21_Day 1.jpg" "Media/tcwa/day36.jpg"
mv "Media/7158987651357969486/10_Day 1.jpg" "Media/tcwa/day37.jpg"
mv "Media/7158987651357969486/29_Day 1.jpg" "Media/tcwa/day38.jpg"
mv "Media/7158987651357969486/11_Day 1.jpg" "Media/tcwa/day39.jpg"
mv "Media/7158987651357969486/20_Day 1.jpg" "Media/tcwa/day40.jpg"
mv "Media/7158987651357969486/7_Day 1.jpg"  "Media/tcwa/day41.jpg"
mv "Media/7158987651357969486/19_Day 1.jpg" "Media/tcwa/day42.jpg"
mv "Media/7158987651357969486/30_Day 1.jpg" "Media/tcwa/day43.jpg"
mv "Media/7158987651357969486/8_Day 1.jpg"  "Media/tcwa/day44.jpg"
mv "Media/7158987651357969486/12_Day 1.jpg" "Media/tcwa/day45.jpg"
mv "Media/7158987651357969486/22_Day 1.jpg" "Media/tcwa/day46.jpg"
mv "Media/7158987651357969486/4_Day 1.jpg"  "Media/tcwa/day47.jpg"
mv "Media/7158987651357969486/24_Day 1.jpg" "Media/tcwa/day48.jpg"
mv "Media/7158987651357969486/26_Day 1.jpg" "Media/tcwa/day49.jpg"
mv "Media/7158987651357969486/17_Day 1.jpg" "Media/tcwa/day50.jpg"
mv "Media/7158987651357969486/23_Day 1.jpg" "Media/tcwa/day51.jpg"
mv "Media/7158987651357969486/3_Day 1.jpg"  "Media/tcwa/day52.jpg"
mv "Media/7158987651357969486/27_Day 1.jpg" "Media/tcwa/day53.jpg"
mv "Media/7158987651357969486/16_Day 1.jpg" "Media/tcwa/day54.jpg"
mv "Media/7158987651357969486/2_Day 1.jpg"  "Media/tcwa/day55.jpg"
mv "Media/7158987651357969486/5_Day 1.jpg"  "Media/tcwa/day56.jpg"
mv "Media/7158987651357969486/18_Day 1.jpg" "Media/tcwa/day57.jpg"
mv "Media/7158987651357969486/15_Day 1.jpg" "Media/tcwa/day58.jpg"
mv "Media/7158987651357969486/1_Day 1.jpg"  "Media/tcwa/day59.jpg"
mv "Media/7158987651357969486/25_Day 1.jpg" "Media/tcwa/day60.jpg"
mv "Media/7158987651357969486/28_Day 1.jpg" "Media/tcwa/day61.jpg"
mv "Media/7158987651357969486/9_Day 1.jpg"  "Media/tcwa/day62.jpg"
mv "Media/7158987651357969486/13_Day 1.jpg" "Media/tcwa/day63.jpg"

echo "Removing now-empty FB card source folder..."
rmdir "Media/7158987651357969486"

echo "Renaming and moving carousel slides..."

for day in 35 39 42 44 46 51 53 56 58 60 62; do
  mv "Media/day${day}-carousel-1/Day 1.png"     "Media/tcwa/day${day}-carousel-1.png"
  mv "Media/day${day}-carousel-1/Day 1 (2).png" "Media/tcwa/day${day}-carousel-2.png"
  mv "Media/day${day}-carousel-1/Day 1 (3).png" "Media/tcwa/day${day}-carousel-3.png"
  mv "Media/day${day}-carousel-1/Day 1 (4).png" "Media/tcwa/day${day}-carousel-4.png"
  mv "Media/day${day}-carousel-1/Day 1 (5).png" "Media/tcwa/day${day}-carousel-5.png"
  mv "Media/day${day}-carousel-1/Day 1 (6).png" "Media/tcwa/day${day}-carousel-6.png"
  mv "Media/day${day}-carousel-1/Day 1 (7).png" "Media/tcwa/day${day}-carousel-7.png"
  rmdir "Media/day${day}-carousel-1"
done

# Day 37's carousel folder was downloaded with different filenames
# (2.png through 7.png, no parentheses) - same slide order, different names.
mv "Media/day37-carousel-1/Day 1.png" "Media/tcwa/day37-carousel-1.png"
mv "Media/day37-carousel-1/2.png"     "Media/tcwa/day37-carousel-2.png"
mv "Media/day37-carousel-1/3.png"     "Media/tcwa/day37-carousel-3.png"
mv "Media/day37-carousel-1/4.png"     "Media/tcwa/day37-carousel-4.png"
mv "Media/day37-carousel-1/5.png"     "Media/tcwa/day37-carousel-5.png"
mv "Media/day37-carousel-1/6.png"     "Media/tcwa/day37-carousel-6.png"
mv "Media/day37-carousel-1/7.png"     "Media/tcwa/day37-carousel-7.png"
rmdir "Media/day37-carousel-1"

echo "Done. Final structure:"
find Media/tcwa -maxdepth 1 -type f -name "day*" | sort
