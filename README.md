# Canvas Participation Analyzer

A simple Python library to analyze and grade student participation in Canvas courses. Tracks student activity across discussion forums and internal messages, automatically excluding professor activity.

## Features

- 📊 **Multi-channel Analysis**: Track participation in both discussion forums and internal messages
- 👨‍🏫 **Professor Filtering**: Automatically identifies and excludes professor activity
- 📅 **Date Filtering**: Analyze participation within specific time periods
- 📈 **Multiple Grading Schemes**: Tiered, linear, logarithmic, and custom grading options
- 📁 **Easy Export**: Generate CSV files ready for gradebook integration
- 🎯 **Student Roster Integration**: Merge with official class rosters

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/your-username/canvas-participation-analyzer
cd canvas-participation-analyzer

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Edit `config.py` with your Canvas settings:

```python
# Canvas API Configuration
CANVAS_BASE_URL = "https://your-canvas-instance.edu/api/v1"
CANVAS_API_TOKEN = ""  # Set your token here

# Course settings
COURSE_ID = 12345  # TODO: Update this with your course ID

# Professor identification
PROFESSOR_NAMES = ["Professor Name"]
PROFESSOR_IDS = [12345]

# Analysis settings
SEMESTER_START_DATE = "2024-01-15"
DEFAULT_GRADING_SCHEME = "tiered"
```

**Alternative:** Create a `.env` file for your API token:

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your Canvas token
CANVAS_API_TOKEN=your_canvas_api_token_here
```

### 3. Basic Usage

**Option 1: Run the example script**
```bash
python example_usage.py
```

**Option 2: Use the Jupyter notebook**
```bash
jupyter notebook example_usage.ipynb
```

**Option 3: Use the library directly**
```python
import config
from participation_analyzer import analyze_participation
from grading_schemes import apply_grading_scheme

# Analyze participation (uses config.py settings)
participation_data = analyze_participation(
    course_id=config.COURSE_ID,
    canvas_token=config.CANVAS_API_TOKEN
)

# Apply grading scheme
graded_data = apply_grading_scheme(participation_data, config.DEFAULT_GRADING_SCHEME)

# Export results
graded_data.to_csv("participation_grades.csv", index=False)
```

## Usage Examples

### Complete Workflow

```python
import config
from participation_analyzer import analyze_participation
from grading_schemes import apply_grading_scheme, load_student_roster

# 1. Analyze participation
participation_data = analyze_participation(
    course_id=config.COURSE_ID,
    canvas_token=config.CANVAS_API_TOKEN
)

# 2. Load student roster (optional)
student_roster = load_student_roster("data_files/lista.csv")

# 3. Apply grading with roster
graded_data = apply_grading_scheme(
    participation_data, 
    scheme_name=config.DEFAULT_GRADING_SCHEME,
    student_roster=student_roster
)

# 4. Export final grades
graded_data.to_csv("participation_grades_final.csv", index=False)

print(f"✅ Graded {len(graded_data)} students")
print(f"Average grade: {graded_data['grade'].mean():.2f}")
```

### Custom Analysis Options

```python
from participation_analyzer import get_forum_participation, get_message_participation

# Analyze only forums
forum_data = get_forum_participation(
    course_id=12345,
    headers={"Authorization": "Bearer your_token"}
)

# Analyze only messages from specific date
message_data = get_message_participation(
    course_id=12345,
    headers={"Authorization": "Bearer your_token"},
    start_date="2024-02-01"
)
```

### Compare Grading Schemes

```python
from grading_schemes import preview_grading_schemes

# Preview different grading schemes
preview_grading_schemes(participations_range=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
```

Output:
```
Comparison of grading schemes:
 Participations  Tiered  Linear  Logarithmic  Square Root  Percentage
              0     0.0    1.00         1.00         0.50        0.00
              1     2.0    1.50         2.12         1.86        0.45
              2     2.5    1.85         2.77         2.42        0.91
              3     3.0    2.20         3.23         2.85        1.36
              4     3.5    2.55         3.59         3.21        1.82
              5     4.0    2.90         3.88         3.53        2.27
              6     4.5    3.25         4.13         3.82        2.73
              7     5.0    3.60         4.35         4.09        3.18
              8     5.0    3.95         4.54         4.34        3.64
              9     5.0    4.30         4.71         4.57        4.09
             10     5.0    4.65         4.86         4.79        4.55
```

## Available Grading Schemes

### Tiered (Recommended)
- **0 participations**: 0.0 (no credit)
- **1 participation**: 2.0 (minimal credit)
- **2-6 participations**: 2.5, 3.0, 3.5, 4.0, 4.5 (graduated)
- **7+ participations**: 5.0 (maximum)

### Linear
- Linear scaling from minimum to maximum grade
- Generous floor for minimal participation

### Logarithmic
- Very generous to students with low participation
- Diminishing returns for high participation

### Square Root
- More generous than linear for lower participation
- Balanced approach

### Percentage
- Simple percentage-based grading
- Proportional to participation level

## File Structure

```
canvas-participation-analyzer/
├── README.md                   # This file
├── config.py                   # Configuration settings
├── participation_analyzer.py   # Core analysis functions
├── grading_schemes.py          # Grading calculation methods
├── example_usage.py           # Complete workflow example (Python script)
├── example_usage.ipynb        # Interactive Jupyter notebook
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
├── CLAUDE.md                  # Development history
└── data_files/               # Example data files
    └── lista.csv.example
```

## Interactive Analysis

The Jupyter notebook (`example_usage.ipynb`) provides an interactive way to:
- Run the analysis step by step
- Visualize participation data and grade distributions
- Experiment with different grading schemes
- See detailed output at each step

All configuration is handled through `config.py` - just update it with your Canvas settings and run the notebook cells.

## Configuration Options

### Canvas Settings
- `CANVAS_BASE_URL`: Your Canvas instance URL
- `CANVAS_API_TOKEN`: Your Canvas API token

### Professor Identification
- `PROFESSOR_NAMES`: List of professor names to exclude
- `PROFESSOR_IDS`: List of professor user IDs to exclude

### Analysis Options
- `SEMESTER_START_DATE`: Filter messages from this date
- `EXCLUDE_PROFESSOR`: Whether to exclude professor from results
- `INCLUDE_FORUMS`: Whether to analyze discussion forums
- `INCLUDE_MESSAGES`: Whether to analyze internal messages

### Display Options
- `SHOW_PROGRESS`: Show progress messages during analysis
- `VERBOSE`: Show detailed debug information

## Getting Your Canvas API Token

1. Log in to your Canvas instance
2. Go to Account → Settings
3. Scroll down to "Approved Integrations"
4. Click "+ New Access Token"
5. Add a purpose description
6. Click "Generate Token"
7. Copy the token and add it to your `.env` file

## Student Roster Format

If using a student roster, the CSV should have these columns:
- `Student`: Full name (e.g., "Last, First")
- `ID`: Canvas user ID

Example:
```csv
Student,ID
"Smith, John",12345
"Doe, Jane",67890
```

## Troubleshooting

### Common Issues

**API Token Issues**
- Ensure your token has the correct permissions
- Check that the token hasn't expired
- Verify the Canvas base URL is correct

**No Participation Data**
- Check that the course ID is correct
- Verify the date filters aren't too restrictive
- Ensure students have actually participated

**Professor Not Filtered**
- Check professor names match exactly
- Add professor user ID to `PROFESSOR_IDS`
- Verify professor identification logic

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Search existing GitHub issues
3. Create a new issue with detailed information

## Changelog

### Version 1.0.0
- Initial release
- Basic participation analysis
- Multiple grading schemes
- Student roster integration
- CSV export functionality