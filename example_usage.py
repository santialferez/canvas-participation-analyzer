#!/usr/bin/env python3
"""
Complete example of Canvas participation analysis workflow

This script demonstrates how to:
1. Analyze student participation in Canvas forums and messages
2. Apply different grading schemes
3. Integrate with student roster
4. Export results for gradebook

Usage:
    python example_usage.py
"""

import os
import sys
from dotenv import load_dotenv
from participation_analyzer import analyze_participation, export_participation_data
from grading_schemes import apply_grading_scheme, load_student_roster, preview_grading_schemes, export_graded_data
import config

# Load environment variables from .env file
load_dotenv()


def main():
    print("🎯 Canvas Participation Analyzer - Example Usage")
    print("=" * 60)
    
    # Configuration from config.py
    COURSE_ID = config.COURSE_ID
    CANVAS_TOKEN = config.CANVAS_API_TOKEN
    
    if not CANVAS_TOKEN:
        print("❌ Error: Canvas API token not found!")
        print("Please set CANVAS_API_TOKEN environment variable or update config.py")
        sys.exit(1)
    
    print(f"📋 Course ID: {COURSE_ID}")
    print(f"🔑 Canvas Token: {'*' * 10}{CANVAS_TOKEN[-4:] if len(CANVAS_TOKEN) > 4 else 'NOT_SET'}")
    print(f"🎓 Professor filter: {config.PROFESSOR_NAMES}")
    print(f"📅 Start date: {config.SEMESTER_START_DATE}")
    print()
    
    try:
        # Step 1: Analyze participation
        print("Step 1: Analyzing participation...")
        participation_data = analyze_participation(
            course_id=COURSE_ID,
            canvas_token=CANVAS_TOKEN,
            include_forums=config.INCLUDE_FORUMS,
            include_messages=config.INCLUDE_MESSAGES
        )
        
        if participation_data.empty:
            print("⚠️  No participation data found.")
            print("Possible causes:")
            print("  • Check your course ID and API token")
            print("  • Ensure you have permissions to access the course")
            print("  • The course might not have any forum discussions or messages")
            print("  • Try running: python example_usage.py check")
            return
        
        # Step 2: Export raw participation data
        print("\nStep 2: Exporting raw participation data...")
        export_participation_data(participation_data, "raw_participation_data.csv")
        
        # Step 3: Preview grading schemes
        print("\nStep 3: Previewing grading schemes...")
        max_participations = participation_data['total_participations'].max()
        preview_range = list(range(0, min(int(max_participations) + 2, 12)))
        preview_grading_schemes(preview_range)
        
        # Step 4: Load student roster (optional)
        print("\nStep 4: Loading student roster...")
        student_roster = load_student_roster("data_files/lista.csv")
        
        # Step 5: Apply grading scheme
        print("\nStep 5: Applying grading scheme...")
        graded_data = apply_grading_scheme(
            participation_data,
            scheme_name=config.DEFAULT_GRADING_SCHEME,
            student_roster=student_roster
        )
        
        # Step 6: Export final grades
        print("\nStep 6: Exporting final grades...")
        export_graded_data(graded_data, "participation_grades_final.csv")
        
        # Step 7: Show summary
        print("\n" + "=" * 60)
        print("📊 ANALYSIS SUMMARY")
        print("=" * 60)
        
        total_students = len(graded_data)
        avg_grade = graded_data['grade'].mean()
        avg_participation = graded_data['total_participations'].mean()
        
        print(f"Total students: {total_students}")
        print(f"Average participation: {avg_participation:.1f}")
        print(f"Average grade: {avg_grade:.2f}")
        print(f"Grade range: {graded_data['grade'].min():.1f} - {graded_data['grade'].max():.1f}")
        
        # Show top participants
        print(f"\nTop 5 participants:")
        top_participants = graded_data.nlargest(5, 'total_participations')
        for i, (_, student) in enumerate(top_participants.iterrows(), 1):
            name = student.get('user_name', 'Unknown')
            participations = student['total_participations']
            grade = student['grade']
            print(f"  {i}. {name}: {participations} participations → {grade:.1f}")
        
        # Show activity levels
        print(f"\nActivity level distribution:")
        if 'activity_level' in graded_data.columns:
            activity_counts = graded_data['activity_level'].value_counts()
            for level, count in activity_counts.items():
                percentage = (count / total_students) * 100
                print(f"  {level}: {count} students ({percentage:.1f}%)")
        
        # Show grade distribution
        print(f"\nGrade distribution:")
        grade_counts = graded_data['grade'].value_counts().sort_index()
        for grade, count in grade_counts.items():
            percentage = (count / total_students) * 100
            print(f"  {grade:.1f}: {count} students ({percentage:.1f}%)")
        
        print("\n✅ Analysis complete!")
        print(f"📁 Files created:")
        print(f"  • raw_participation_data.csv")
        print(f"  • participation_grades_final.csv")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        if config.VERBOSE:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def demo_grading_schemes():
    """
    Demonstrate different grading schemes with sample data
    """
    print("\n🎯 Grading Schemes Demonstration")
    print("=" * 50)
    
    # Sample participation data
    sample_participations = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    
    print("Sample participation counts:", sample_participations)
    print()
    
    # Preview all schemes
    preview_grading_schemes(sample_participations)
    
    print("\n📊 Recommendations:")
    print("• Tiered: Best for encouraging participation with clear milestones")
    print("• Linear: Fair proportional grading")
    print("• Logarithmic: Very generous to low participation")
    print("• Square Root: Balanced approach")
    print("• Percentage: Simple percentage-based")


def check_configuration():
    """
    Check if the configuration is set up correctly
    """
    print("\n🔧 Configuration Check")
    print("=" * 30)
    
    # Check API token
    token = config.CANVAS_API_TOKEN
    if token:
        print(f"✅ Canvas API token: Set (ends with {token[-4:]})")
    else:
        print("❌ Canvas API token: Not set")
        print("   Set CANVAS_API_TOKEN in config.py or as environment variable")
    
    # Check course ID
    print(f"📋 Course ID: {config.COURSE_ID}")
    
    # Check Canvas URL
    print(f"✅ Canvas URL: {config.CANVAS_BASE_URL}")
    
    # Check professor settings
    print(f"✅ Professor names: {config.PROFESSOR_NAMES}")
    print(f"✅ Professor IDs: {config.PROFESSOR_IDS}")
    
    # Check date settings
    print(f"✅ Start date: {config.SEMESTER_START_DATE}")
    
    # Check grading scheme
    print(f"✅ Default grading scheme: {config.DEFAULT_GRADING_SCHEME}")
    
    # Check data files
    roster_file = "data_files/lista.csv"
    if os.path.exists(roster_file):
        print(f"✅ Student roster: Found ({roster_file})")
    else:
        print(f"⚠️  Student roster: Not found ({roster_file})")
        print("   This is optional but recommended")


if __name__ == "__main__":
    # Check if user wants to run specific demos
    if len(sys.argv) > 1:
        if sys.argv[1] == "demo":
            demo_grading_schemes()
        elif sys.argv[1] == "check":
            check_configuration()
        else:
            print("Usage:")
            print("  python example_usage.py       # Run full analysis")
            print("  python example_usage.py demo  # Show grading schemes")
            print("  python example_usage.py check # Check configuration")
    else:
        # Run full analysis
        main()