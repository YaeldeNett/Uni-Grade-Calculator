# 🎓 Uni Grade Calculator

A desktop application to track and calculate your university grades across multiple subjects and semesters.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)

## Features

- **Multi-Subject Tracking** - Manage grades across multiple subjects in one place
- **Semester Organization** - Save and load different semesters as separate files
- **Assessment Management** - Add, edit, and delete assignments, exams, and other assessments
- **Grade Calculations** - Automatically calculates:
  - Current weighted average
  - Contribution to final grade
  - Required average on remaining assessments to pass
- **Visual Progress** - Progress bar visualization showing your grade contributions (requires matplotlib)
- **Customizable Pass Mark** - Set your own pass threshold (default: 50%)
- **Auto-Save** - Changes are automatically saved when you close the app

## Installation

### Option 1: Windows Installer (Recommended)

1. Download `GradeCalculator_Setup.exe` from the [`dist`](./dist) folder
2. Run the installer and follow the prompts
3. Launch from your desktop shortcut or Start Menu

### Option 2: Run from Source

1. Clone this repository:

   ```bash
   git clone https://github.com/YOUR_USERNAME/GradeCalculator.git
   cd GradeCalculator
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

## Dependencies

| Package        | Required | Purpose                                           |
| -------------- | -------- | ------------------------------------------------- |
| `ttkbootstrap` | Optional | Modern themed UI (falls back to standard tkinter) |
| `matplotlib`   | Optional | Progress visualization graph                      |

## Usage

1. **Create a Semester** - Click the `+` button to start a new semester
2. **Add Subjects** - Click "Add" in the Subjects panel to add your courses
3. **Add Assessments** - Select a subject and click "Add Assessment" to add assignments, exams, etc.
4. **Enter Marks** - Edit assessments to record your grades as you receive them
5. **Track Progress** - Watch your statistics update in real-time

### Statistics Explained

- **Completed Weight**: Percentage of assessments you've completed
- **Contribution**: Points contributed to your final grade so far
- **Current Average**: Your average mark on completed assessments
- **Required to Pass**: The average you need on remaining assessments to hit your pass mark

## Project Structure

```
GradeCalculator/
├── main.py           # Application entry point
├── ui.py             # User interface (tkinter/ttkbootstrap)
├── models.py         # Data models (GradeBook, Subject, Assessment)
├── calculations.py   # Grade calculation logic
├── installer.py      # Windows installer builder script
├── icon.png          # Application icon
├── icon.ico          # Windows icon
├── saves/            # Your semester save files (JSON)
└── dist/             # Built installer
```

## Building from Source

To build the Windows installer yourself:

1. Install PyInstaller:

   ```bash
   pip install pyinstaller
   ```

2. Run the build command:

   ```bash
   pyinstaller --onefile --windowed --icon=icon.ico --add-data "icon.png;." --add-data "icon.ico;." main.py
   ```

3. Run the installer script:
   ```bash
   python installer.py
   ```
