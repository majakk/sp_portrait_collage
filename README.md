# Portrait Classification and PDF Generator

Automated tool for classifying student portrait photos by background color and generating PDF collages for printing.

## Overview

This tool processes student portrait photographs from game development courses and:
- **Classifies portraits** by background color (green for game design students, orange for game graphics students)
- **Generates PDF collages** with all portraits arranged on single A4 pages
- **Auto-corrects** ambiguous classifications to ensure accuracy

## Requirements

- Python 3.7 or higher
- Required Python packages:
  - `Pillow` (image processing)
  - `reportlab` (PDF generation)

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install Pillow reportlab
   ```

2. **Verify installation:**
   ```bash
   python process_portraits.py --help
   ```

## Directory Structure

```
portraits/
├── SP23/                    # 2023 portraits
│   ├── *.png               # Portrait images
│   └── portrait_groups.json # Classification results (generated)
├── SP24/                    # 2024 portraits
│   ├── *.png
│   └── portrait_groups.json
├── SP25/                    # 2025 portraits
│   ├── *.png
│   └── portrait_groups.json
├── Collages/                # Output folder (auto-created)
│   ├── speldesignstudenter_sp23.pdf
│   ├── spelgrafikstudenter_sp23.pdf
│   ├── speldesignstudenter_sp24.pdf
│   ├── spelgrafikstudenter_sp24.pdf
│   ├── speldesignstudenter_sp25.pdf
│   └── spelgrafikstudenter_sp25.pdf
├── process_portraits.py     # Main script
├── README.md                # This file
└── CLAUDE.md                # Technical documentation
```

## Usage

### Process All Years

Process all years (SP23, SP24, SP25) at once:

```bash
python process_portraits.py --all
```

### Process Single Year

Process a specific year:

```bash
python process_portraits.py 23   # Process SP23
python process_portraits.py 24   # Process SP24
python process_portraits.py 25   # Process SP25
```

### Advanced Options

```bash
# Disable automatic corrections
python process_portraits.py --all --no-auto-correct

# Use custom threshold for classification (-10 to 0, default -10)
python process_portraits.py 23 --threshold -8

# Specify custom output folder
python process_portraits.py --all --output MyCollages
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `year` | Year to process (23, 24, 25) | - |
| `--all` | Process all years | false |
| `--no-auto-correct` | Disable automatic corrections | false (enabled) |
| `--threshold N` | G-R difference threshold (-10 to 0) | -10 |
| `--output FOLDER` | Output folder for PDFs | Collages |
| `--help` | Show help message | - |

## How It Works

### 1. Image Analysis

The tool analyzes the bottom 5% of each portrait image to detect the background color behind the student's name:

- **Green background** → Game Design Students (Speldesignstudenter)
- **Orange/Red background** → Game Graphics Students (Spelgrafikstudenter)

### 2. Color Classification Algorithm

The algorithm:
1. Samples the bottom 5% of each portrait
2. Calculates average RGB values
3. Compares Red (R) and Green (G) channels
4. Classifies based on the difference (G-R):
   - If **G > R by 5+ points** → Green
   - If **R > G by 5+ points** → Orange
   - If **difference is < 5 points** → Uses additional heuristics

### 3. Automatic Corrections

By default, the tool applies automatic corrections to handle ambiguous cases:

- Portraits with **G-R difference ≥ -10** are moved from orange to green
- This threshold can be adjusted using `--threshold`
- Use `--no-auto-correct` to disable this feature

### 4. PDF Generation

Creates optimized A4 portrait-mode PDFs:
- Automatically calculates optimal grid layout
- Includes title and portrait count
- Single page per group for easy printing

## Output Files

### JSON Classification Data

Each year folder gets a `portrait_groups.json` file containing:

```json
{
  "green_group": ["SP23\\filename1.png", ...],
  "orange_group": ["SP23\\filename2.png", ...],
  "unknown_group": [],
  "stats": {
    "green_count": 37,
    "orange_count": 37,
    "unknown_count": 0,
    "total": 74
  }
}
```

### PDF Collages

Generated in the `Collages/` folder:

- `speldesignstudenter_sp23.pdf` - Green group for 2023
- `spelgrafikstudenter_sp23.pdf` - Orange group for 2023
- (Same pattern for SP24 and SP25)

## Adding New Years

To process portraits for a new year (e.g., SP26):

1. **Create year folder:**
   ```bash
   mkdir SP26
   ```

2. **Add portrait images:**
   - Place all PNG portrait files in `SP26/`
   - Filenames should follow the pattern: `lastname_studentid_submissionid_coursecode_details.png`

3. **Run processing:**
   ```bash
   python process_portraits.py 26
   ```

4. **Output:**
   - Classification data: `SP26/portrait_groups.json`
   - PDF collages: `Collages/speldesignstudenter_sp26.pdf` and `Collages/spelgrafikstudenter_sp26.pdf`

## Troubleshooting

### Problem: "No PNG files found"

**Solution:** Ensure portrait images are directly in the year folder (e.g., `SP23/*.png`) and not in subfolders.

### Problem: Wrong classifications

**Solution:**
1. Try adjusting the threshold: `python process_portraits.py 23 --threshold -8`
2. Manually review `portrait_groups.json` and edit if needed
3. Re-run with `--no-auto-correct` if automatic corrections are causing issues

### Problem: PDF generation fails

**Solution:**
1. Check that all image files can be opened
2. Ensure `Pillow` and `reportlab` are installed correctly
3. Verify sufficient disk space for output

### Problem: Unicode/encoding errors on Windows

**Solution:** The script automatically handles UTF-8 encoding. If issues persist, ensure your terminal supports UTF-8.

## Manual Corrections

If you need to manually correct classifications:

1. **Edit the JSON file:**
   Open `SPxx/portrait_groups.json` in a text editor

2. **Move portraits between groups:**
   - Cut the filename from `orange_group`
   - Paste it into `green_group` (or vice versa)

3. **Update statistics:**
   ```json
   "stats": {
     "green_count": 38,    // Update this
     "orange_count": 36,   // And this
     ...
   }
   ```

4. **Regenerate PDFs:**
   ```bash
   python process_portraits.py 23
   ```

## Technical Details

### Image Sampling

- **Sampling region:** Bottom 5% of image
- **Why 5%?** The name background bar typically occupies 3-8% of the image height
- **Sampling method:** Average RGB of all pixels in the region

### Classification Thresholds

| Threshold | Description | Use Case |
|-----------|-------------|----------|
| -15 | Very strict | Only move clearly green portraits |
| -10 | Standard (default) | Balanced approach |
| -8 | Lenient | Move more ambiguous cases to green |
| -5 | Very lenient | Maximum green classification |

### Grid Layout Algorithm

The tool automatically calculates optimal grid dimensions:
- Aims for a layout matching the A4 aspect ratio
- Ensures more rows than columns (portrait mode)
- Maximizes image size while fitting on one page

## Example Workflow

### New academic year workflow:

```bash
# 1. Create folder and add images
mkdir SP26
# (Copy portrait PNG files to SP26/)

# 2. Process portraits
python process_portraits.py 26

# 3. Review output
# Check: Collages/speldesignstudenter_sp26.pdf
# Check: Collages/spelgrafikstudenter_sp26.pdf

# 4. If corrections needed
# Edit SP26/portrait_groups.json manually
# Then re-run:
python process_portraits.py 26

# 5. Print the PDFs!
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review `CLAUDE.md` for technical details
3. Examine `portrait_groups.json` for classification data
4. Contact the system administrator

## License

Internal tool for educational institution use.

## Version History

- **v1.0** - Initial release with automatic classification
- **v1.1** - Added auto-correction with configurable thresholds
- **v1.2** - Improved algorithm accuracy (5% sampling region)
- **v2.0** - Consolidated into single script with CLI interface

---

**Last Updated:** 2025-01-13
