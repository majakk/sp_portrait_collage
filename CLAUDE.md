# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is an automated portrait classification and PDF generation system for student photographs from game development courses at a Swedish educational institution. The repository processes portraits from multiple academic years (SP23, SP24, SP25, etc.) and organizes them by student program:

- **Speldesignstudenter** (Game Design Students) - Green background
- **Spelgrafikstudenter** (Game Graphics Students) - Orange/Red background

## Main Script

**`process_portraits.py`** - The primary entry point for all operations

This script handles:
- Image analysis and color classification
- Automatic correction of ambiguous cases
- PDF collage generation (portrait A4 mode)
- Processing single or multiple years

### Quick Start

```bash
# Process all years
python process_portraits.py --all

# Process single year
python process_portraits.py 23   # or 24, 25

# See all options
python process_portraits.py --help
```

## Directory Structure

```
portraits/
├── SP23/, SP24/, SP25/      # Year folders with portrait PNGs
├── Collages/                 # Generated PDF output
├── process_portraits.py      # Main script
├── README.md                 # User documentation
└── CLAUDE.md                 # This file
```

## File Naming Convention

Portrait images follow this pattern:
```
{lastname}{firstname}_{studentid}_{submissionid}_{coursecode}-{details}.png
```

Example: `adambertil_46030_1577942_SP25-Intro_till_MTA-Porträttfoto-Adam_Bertil.png`

- **Filename prefix**: lastname + firstname (lowercase, no spaces)
- **Student ID**: 5-digit identifier
- **Submission ID**: 7-digit identifier
- **Course code**: e.g., SP25-Intro_till_MTA
- **Assignment**: typically "Porträttfoto" (Portrait Photo)
- **Full name**: Student's actual name
- **Version suffix**: Optional -1, -2, -3 for resubmissions

## Color Classification Algorithm

### How It Works

1. **Sampling**: Analyzes bottom 5% of each image (where name/background is)
2. **RGB Analysis**: Calculates average R, G, B values
3. **Classification Logic**:
   - If G > R by 5+ points → Green (Game Design)
   - If R > G by 5+ points → Orange (Game Graphics)
   - If difference < 5 points → Uses saturation heuristics

4. **Auto-Correction**: By default, moves portraits with G-R ≥ -10 to green group

### Threshold Values

- **-10**: Default, balanced approach
- **-8 to -5**: More lenient, moves more to green
- **-12 to -15**: Stricter, only clear green cases

## Output Files

### Classification Data

Each year folder gets a `portrait_groups.json`:

```json
{
  "green_group": ["SP23\\student1.png", ...],
  "orange_group": ["SP23\\student2.png", ...],
  "stats": {
    "green_count": 37,
    "orange_count": 37,
    "total": 74
  }
}
```

### PDF Collages

Generated in `Collages/`:
- `speldesignstudenter_sp23.pdf` - Green group
- `spelgrafikstudenter_sp23.pdf` - Orange group
- (Same pattern for each year)

## Common Development Tasks

### Adding Support for New Year

1. Create folder: `mkdir SP26`
2. Add portrait PNGs to `SP26/`
3. Run: `python process_portraits.py 26`

### Modifying Classification Algorithm

Edit `process_portraits.py`, function `get_bottom_color()`:
- Adjust `MIN_DIFF` (currently 5) for sensitivity
- Change sampling region (currently 5% = `height * 0.05`)
- Modify RGB comparison logic

### Adjusting PDF Layout

Edit `create_collage_pdf_portrait()` function:
- Change `margin`, `spacing`, `title_height` for layout
- Modify grid calculation for different arrangements
- Update page size (currently `A4`)

### Manual Classification Corrections

1. Edit `SPxx/portrait_groups.json`
2. Move filenames between `green_group` and `orange_group`
3. Update `stats` counts
4. Re-run: `python process_portraits.py xx`

## Dependencies

- **Python 3.7+**
- **Pillow**: Image processing and analysis
- **reportlab**: PDF generation

Install: `pip install Pillow reportlab`

## Legacy Scripts (Deprecated)

The following scripts were used during development but are now integrated into `process_portraits.py`:

- `analyze_portraits.py` - Original analyzer
- `create_pdf_collages.py` - Landscape PDF generator
- `create_pdf_portrait.py` - Portrait PDF generator
- `process_year.py` - Year processor
- `fix_groups.py` - Manual corrections
- `fix_sp25_groups.py` - SP25 specific fixes
- `auto_fix_classifications.py` - Auto-corrections
- `review_classifications.py` - Review tool
- `show_all_orange.py` - Diagnostic tool

These can be safely removed as all functionality is in `process_portraits.py`.

## Technical Notes

### Image Analysis
- Uses PIL/Pillow for image processing
- Samples only the bottom 5% for efficiency
- Handles RGB, RGBA, and grayscale images
- Gracefully handles corrupted images

### PDF Generation
- Uses reportlab for PDF creation
- Portrait A4 orientation (595 x 842 points)
- Automatic grid optimization based on image count
- Preserves aspect ratio of portraits
- Single page per group for easy printing

### Error Handling
- Corrupted images are logged but don't stop processing
- Missing folders are skipped with warnings
- Unicode handling for Swedish characters (UTF-8)

## Future Enhancements

Potential improvements:
- Landscape PDF option (use old `create_pdf_collages.py` logic)
- GUI interface for manual review/corrections
- Batch processing from command file
- Export to other formats (HTML gallery, etc.)
- Machine learning for improved classification

## Support & Debugging

1. **Check logs**: Script prints detailed progress
2. **Review JSON**: Examine `portrait_groups.json` for classification data
3. **Adjust threshold**: Try different `--threshold` values
4. **Disable auto-correct**: Use `--no-auto-correct` to see raw classification
5. **Manual override**: Edit JSON files directly when needed
