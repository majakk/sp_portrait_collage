#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Portrait Classification and PDF Generator

This script processes student portrait photos, classifies them by background color
(green for game design students, orange for game graphics students), and generates
PDF collages for printing.

Usage:
    python process_portraits.py [year]
    python process_portraits.py --all
    python process_portraits.py --help

Examples:
    python process_portraits.py 23                           # Process SP23 only (portrait mode)
    python process_portraits.py --all                        # Process all years (portrait mode)
    python process_portraits.py 25 --threshold -8            # Custom threshold for SP25
    python process_portraits.py 23 --orientation landscape   # Generate landscape PDFs
    python process_portraits.py --all --orientation both     # Generate both portrait and landscape
"""

import os
import sys
import io
import json
import math
import argparse
from pathlib import Path
from PIL import Image
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# Set UTF-8 encoding for console output on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def get_bottom_color(image_path):
    """
    Analyze the bottom portion of an image to detect the dominant background color.

    Returns:
        tuple: (color_type, rgb_tuple) where color_type is 'green', 'orange', or 'unknown'
    """
    with Image.open(image_path) as img:
        width, height = img.size

        # Sample the bottom 5% of the image where the name background should be
        bottom_height = int(height * 0.05)
        bottom_region = img.crop((0, height - bottom_height, width, height))

        # Convert to RGB if necessary
        if bottom_region.mode != 'RGB':
            bottom_region = bottom_region.convert('RGB')

        # Calculate average color from all pixels
        pixels = list(bottom_region.getdata())
        r_sum, g_sum, b_sum = 0, 0, 0
        pixel_count = len(pixels)

        for r, g, b in pixels:
            r_sum += r
            g_sum += g
            b_sum += b

        avg_r = r_sum / pixel_count
        avg_g = g_sum / pixel_count
        avg_b = b_sum / pixel_count

        # Classification algorithm
        MIN_DIFF = 5  # Minimum difference between R and G channels
        MIN_VALUE = 100  # Minimum brightness threshold

        r_g_diff = avg_g - avg_r  # Positive means more green

        # Green: G must be noticeably higher than R
        if r_g_diff >= MIN_DIFF and avg_g > avg_b and avg_g > MIN_VALUE:
            return 'green', (int(avg_r), int(avg_g), int(avg_b))

        # Orange: R must be noticeably higher than G
        elif r_g_diff <= -MIN_DIFF and avg_r > avg_b and avg_r > MIN_VALUE:
            return 'orange', (int(avg_r), int(avg_g), int(avg_b))

        # Ambiguous cases: R and G are very close
        elif abs(r_g_diff) < MIN_DIFF:
            saturation = min(avg_r, avg_g) - avg_b
            if saturation > 30:  # Sufficient color saturation
                # Slight preference to green if very close
                if avg_g >= avg_r - 2:
                    return 'green', (int(avg_r), int(avg_g), int(avg_b))
                else:
                    return 'orange', (int(avg_r), int(avg_g), int(avg_b))

        return 'unknown', (int(avg_r), int(avg_g), int(avg_b))


def analyze_portraits(year_folder, verbose=True):
    """
    Analyze all portrait images in a year folder and categorize by background color.

    Args:
        year_folder: Path to folder containing portrait images
        verbose: Print detailed progress

    Returns:
        dict: Results with green_group, orange_group, and stats
    """
    year_path = Path(year_folder)
    green_group = []
    orange_group = []
    unknown_group = []

    # Get all PNG files
    png_files = list(year_path.glob('*.png'))

    if verbose:
        print(f"Analyzing {len(png_files)} portrait images in {year_folder}...")

    for png_file in png_files:
        try:
            color_type, rgb = get_bottom_color(png_file)

            if color_type == 'green':
                green_group.append(str(png_file))
                if verbose:
                    print(f"[GREEN] {png_file.name[:50]}... (RGB: {rgb})")
            elif color_type == 'orange':
                orange_group.append(str(png_file))
                if verbose:
                    print(f"[ORANGE] {png_file.name[:50]}... (RGB: {rgb})")
            else:
                unknown_group.append(str(png_file))
                if verbose:
                    print(f"[UNKNOWN] {png_file.name[:50]}... (RGB: {rgb})")

        except Exception as e:
            print(f"[ERROR] processing {png_file.name}: {e}")
            unknown_group.append(str(png_file))

    # Save results to JSON
    results = {
        'green_group': green_group,
        'orange_group': orange_group,
        'unknown_group': unknown_group,
        'stats': {
            'green_count': len(green_group),
            'orange_count': len(orange_group),
            'unknown_count': len(unknown_group),
            'total': len(png_files)
        }
    }

    output_file = year_path / 'portrait_groups.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    if verbose:
        print(f"\n{'='*60}")
        print(f"Analysis complete for {year_folder}!")
        print(f"Green background: {len(green_group)} portraits")
        print(f"Orange/Red background: {len(orange_group)} portraits")
        print(f"Unknown/Unclear: {len(unknown_group)} portraits")
        print(f"Results saved to {output_file}")
        print(f"{'='*60}\n")

    return results


def create_collage_pdf_portrait(image_paths, output_pdf, title):
    """
    Create a single-page PDF collage in portrait mode.

    Args:
        image_paths: List of image file paths
        output_pdf: Output PDF filename
        title: Title for the PDF
    """
    if not image_paths:
        print(f"No images to process for {output_pdf}")
        return

    total_images = len(image_paths)
    page_width, page_height = A4
    margin = 20
    title_height = 30
    spacing = 5

    available_width = page_width - (2 * margin)
    available_height = page_height - (2 * margin) - title_height

    # Calculate optimal grid dimensions for portrait
    page_aspect = available_width / available_height
    base = math.sqrt(total_images)
    cols = math.ceil(base * math.sqrt(page_aspect))
    rows = math.ceil(total_images / cols)

    # Ensure we have appropriate portrait layout
    while cols > rows:
        cols -= 1
        if cols < 1:
            cols = 1
            break
        rows = math.ceil(total_images / cols)

    print(f"Arranging {total_images} images in {cols}x{rows} grid (portrait optimized)")

    # Calculate image dimensions
    img_width = (available_width - ((cols - 1) * spacing)) / cols
    sample_img = Image.open(image_paths[0])
    aspect_ratio = sample_img.height / sample_img.width
    img_height = img_width * aspect_ratio

    # Check if height fits
    total_height_needed = (img_height * rows) + ((rows - 1) * spacing)
    if total_height_needed > available_height:
        img_height = (available_height - ((rows - 1) * spacing)) / rows
        img_width = img_height / aspect_ratio

    # Create PDF
    c = canvas.Canvas(str(output_pdf), pagesize=A4)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, page_height - margin, f"{title}")
    c.setFont("Helvetica", 9)
    c.drawString(margin, page_height - margin - 15, f"Total: {total_images} portraits")

    y_start = page_height - margin - title_height

    for idx, img_path in enumerate(image_paths):
        row = idx // cols
        col = idx % cols
        x_pos = margin + (col * (img_width + spacing))
        y_pos_img = y_start - (row * (img_height + spacing)) - img_height

        try:
            img = Image.open(img_path)
            img_reader = ImageReader(img)
            c.drawImage(img_reader, x_pos, y_pos_img,
                      width=img_width, height=img_height,
                      preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Error processing {img_path}: {e}")

    c.showPage()
    c.save()
    print(f"Created {output_pdf} with {total_images} portraits on 1 page")


def create_collage_pdf_landscape(image_paths, output_pdf, title):
    """
    Create a single-page PDF collage in landscape mode.

    Args:
        image_paths: List of image file paths
        output_pdf: Output PDF filename
        title: Title for the PDF
    """
    if not image_paths:
        print(f"No images to process for {output_pdf}")
        return

    total_images = len(image_paths)

    # Use landscape A4
    page_width, page_height = landscape(A4)
    margin = 20
    title_height = 30
    spacing = 5

    # Calculate available space
    available_width = page_width - (2 * margin)
    available_height = page_height - (2 * margin) - title_height

    # Calculate optimal grid dimensions for landscape
    # Aim for a grid that matches the page aspect ratio (width > height)
    page_aspect = available_width / available_height

    # Start with square root and adjust for landscape
    base = math.sqrt(total_images)
    cols = math.ceil(base * math.sqrt(page_aspect))
    rows = math.ceil(total_images / cols)

    # Ensure we don't have too many rows - keep it landscape-oriented
    while rows > cols / 1.5:
        cols += 1
        rows = math.ceil(total_images / cols)

    print(f"Arranging {total_images} images in {cols}x{rows} grid (landscape optimized)")

    # Calculate image dimensions to fit the grid
    img_width = (available_width - ((cols - 1) * spacing)) / cols

    # Load first image to get aspect ratio
    sample_img = Image.open(image_paths[0])
    aspect_ratio = sample_img.height / sample_img.width
    img_height = img_width * aspect_ratio

    # Check if height fits, if not, recalculate based on height
    total_height_needed = (img_height * rows) + ((rows - 1) * spacing)
    if total_height_needed > available_height:
        # Recalculate based on height constraint
        img_height = (available_height - ((rows - 1) * spacing)) / rows
        img_width = img_height / aspect_ratio

    # Create PDF
    c = canvas.Canvas(str(output_pdf), pagesize=landscape(A4))

    # Draw title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, page_height - margin, f"{title}")
    c.setFont("Helvetica", 9)
    c.drawString(margin, page_height - margin - 15, f"Total: {total_images} portraits")

    # Draw images in grid
    y_start = page_height - margin - title_height

    for idx, img_path in enumerate(image_paths):
        row = idx // cols
        col = idx % cols

        x_pos = margin + (col * (img_width + spacing))
        y_pos_img = y_start - (row * (img_height + spacing)) - img_height

        try:
            # Draw image
            img = Image.open(img_path)
            img_reader = ImageReader(img)
            c.drawImage(img_reader, x_pos, y_pos_img,
                      width=img_width, height=img_height,
                      preserveAspectRatio=True, mask='auto')

        except Exception as e:
            print(f"Error processing {img_path}: {e}")

    c.showPage()
    c.save()
    print(f"Created {output_pdf} with {total_images} portraits on 1 page")


def apply_auto_corrections(year_folder, year_code, threshold=-10, verbose=True):
    """
    Automatically move ambiguous portraits from orange to green based on RGB threshold.

    Args:
        year_folder: Path to year folder
        year_code: Year code (e.g., 'SP23')
        threshold: G-R difference threshold (default -10)
        verbose: Print detailed progress

    Returns:
        int: Number of portraits moved
    """
    json_file = Path(year_folder) / 'portrait_groups.json'

    with open(json_file, 'r', encoding='utf-8') as f:
        groups = json.load(f)

    if verbose:
        print(f"\nApplying auto-corrections with threshold {threshold}...")
        print(f"Original: Green={groups['stats']['green_count']}, Orange={groups['stats']['orange_count']}")

    to_move = []

    # Check each orange member
    for img_path in groups['orange_group']:
        try:
            with Image.open(img_path) as img:
                width, height = img.size
                bottom_height = int(height * 0.05)
                bottom_region = img.crop((0, height - bottom_height, width, height))

                if bottom_region.mode != 'RGB':
                    bottom_region = bottom_region.convert('RGB')

                pixels = list(bottom_region.getdata())
                r_sum, g_sum, b_sum = 0, 0, 0

                for r, g, b in pixels:
                    r_sum += r
                    g_sum += g
                    b_sum += b

                avg_r = r_sum / len(pixels)
                avg_g = g_sum / len(pixels)
                diff = avg_g - avg_r

                if diff >= threshold:
                    filename = Path(img_path).name
                    name_part = filename.split('_')[0]
                    to_move.append(img_path)
                    if verbose:
                        print(f"  Moving: {name_part:<40} G-R={diff:+.1f}")
        except Exception as e:
            print(f"Error analyzing {img_path}: {e}")

    # Perform the moves
    for img_path in to_move:
        groups['orange_group'].remove(img_path)
        groups['green_group'].append(img_path)

    # Update stats and sort
    groups['stats']['green_count'] = len(groups['green_group'])
    groups['stats']['orange_count'] = len(groups['orange_group'])
    groups['green_group'].sort()
    groups['orange_group'].sort()

    # Save
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(groups, f, indent=2, ensure_ascii=False)

    if verbose:
        print(f"Moved {len(to_move)} portraits")
        print(f"Updated: Green={groups['stats']['green_count']}, Orange={groups['stats']['orange_count']}")

    return len(to_move)


def process_year(year_folder, year_code, output_folder='Collages', auto_correct=True, threshold=-10, orientation='portrait'):
    """
    Main processing function: analyze portraits and create PDFs.

    Args:
        year_folder: Path to folder containing portrait images
        year_code: Year code for titles (e.g., 'SP23')
        output_folder: Output folder for PDF collages
        auto_correct: Apply automatic corrections for ambiguous cases
        threshold: G-R difference threshold for auto-corrections
        orientation: PDF orientation ('portrait', 'landscape', or 'both')
    """
    print(f"\n{'#'*60}")
    print(f"Processing {year_code}")
    print(f"{'#'*60}\n")

    # Analyze portraits
    results = analyze_portraits(year_folder, verbose=True)

    # Apply auto-corrections if requested
    if auto_correct:
        moved = apply_auto_corrections(year_folder, year_code, threshold=threshold, verbose=True)
        if moved > 0:
            # Reload results after corrections
            json_file = Path(year_folder) / 'portrait_groups.json'
            with open(json_file, 'r', encoding='utf-8') as f:
                results = json.load(f)

    # Create output folder if needed
    output_path = Path(output_folder)
    output_path.mkdir(exist_ok=True)

    # Create PDFs
    print(f"\nGenerating PDFs...")

    # Portrait mode PDFs
    if orientation in ['portrait', 'both']:
        if results['green_group']:
            suffix = '' if orientation == 'portrait' else '_portrait'
            output_pdf = output_path / f'speldesignstudenter_{year_code.lower()}{suffix}.pdf'
            create_collage_pdf_portrait(
                results['green_group'],
                output_pdf,
                f'Speldesignstudenter {year_code}'
            )

        if results['orange_group']:
            suffix = '' if orientation == 'portrait' else '_portrait'
            output_pdf = output_path / f'spelgrafikstudenter_{year_code.lower()}{suffix}.pdf'
            create_collage_pdf_portrait(
                results['orange_group'],
                output_pdf,
                f'Spelgrafikstudenter {year_code}'
            )

    # Landscape mode PDFs
    if orientation in ['landscape', 'both']:
        if results['green_group']:
            suffix = '' if orientation == 'landscape' else '_landscape'
            output_pdf = output_path / f'speldesignstudenter_{year_code.lower()}{suffix}.pdf'
            create_collage_pdf_landscape(
                results['green_group'],
                output_pdf,
                f'Speldesignstudenter {year_code}'
            )

        if results['orange_group']:
            suffix = '' if orientation == 'landscape' else '_landscape'
            output_pdf = output_path / f'spelgrafikstudenter_{year_code.lower()}{suffix}.pdf'
            create_collage_pdf_landscape(
                results['orange_group'],
                output_pdf,
                f'Spelgrafikstudenter {year_code}'
            )

    print(f"\n{'='*60}")
    print(f"Completed processing {year_code}")
    print(f"PDFs saved to {output_folder}/")
    print(f"{'='*60}\n")


def main():
    """Main entry point with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description='Process student portrait photos and generate PDF collages.',
        epilog='Example: python process_portraits.py --all'
    )

    parser.add_argument(
        'year',
        nargs='?',
        help='Year to process (e.g., 23, 24, 25) or --all for all years'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all years (SP23, SP24, SP25)'
    )

    parser.add_argument(
        '--no-auto-correct',
        action='store_true',
        help='Disable automatic corrections for ambiguous classifications'
    )

    parser.add_argument(
        '--threshold',
        type=int,
        default=-10,
        help='G-R threshold for auto-corrections (default: -10)'
    )

    parser.add_argument(
        '--output',
        default='Collages',
        help='Output folder for PDF collages (default: Collages)'
    )

    parser.add_argument(
        '--orientation',
        choices=['portrait', 'landscape', 'both'],
        default='portrait',
        help='PDF orientation: portrait, landscape, or both (default: portrait)'
    )

    args = parser.parse_args()

    # Determine which years to process
    years_to_process = []

    if args.all or (args.year and args.year.lower() == 'all'):
        years_to_process = [('SP23', '23'), ('SP24', '24'), ('SP25', '25')]
    elif args.year:
        year_num = args.year.strip()
        years_to_process = [(f'SP{year_num}', year_num)]
    else:
        parser.print_help()
        return

    # Process each year
    for year_folder, year_num in years_to_process:
        year_path = Path(year_folder)
        if not year_path.exists():
            print(f"Warning: {year_folder} folder not found, skipping...")
            continue

        # Check if there are PNG files
        png_files = list(year_path.glob('*.png'))
        if not png_files:
            print(f"Warning: No PNG files found in {year_folder}, skipping...")
            continue

        process_year(
            year_folder,
            year_folder,
            output_folder=args.output,
            auto_correct=not args.no_auto_correct,
            threshold=args.threshold,
            orientation=args.orientation
        )


if __name__ == '__main__':
    main()
