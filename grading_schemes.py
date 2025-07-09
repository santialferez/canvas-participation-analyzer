"""
Grading schemes for Canvas participation analysis
"""

import pandas as pd
import numpy as np
import config


def tiered_grading(participations):
    """
    Tiered grading scheme - generous at middle/top, 0 for no participation
    Based on the custom scheme from the original notebook
    
    Args:
        participations: Number of total participations
    
    Returns:
        float: Grade from 0.0 to 5.0
    """
    if participations == 0:
        return 0.0  # No credit for 0 participation
    elif participations == 1:
        return 2.0  # Some credit for minimal participation
    elif participations == 2:
        return 2.5
    elif participations == 3:
        return 3.0
    elif participations == 4:
        return 3.5
    elif participations == 5:
        return 4.0
    elif participations == 6:
        return 4.5
    else:  # 7+ participations
        return 5.0  # Maximum grade for high participation


def linear_grading(participations, max_participations=11, min_grade=1.0, max_grade=5.0):
    """
    Linear scaling with a minimum floor
    
    Args:
        participations: Number of total participations
        max_participations: Maximum observed participations for scaling
        min_grade: Minimum grade to assign
        max_grade: Maximum grade to assign
    
    Returns:
        float: Grade from min_grade to max_grade
    """
    if participations == 0:
        return min_grade  # Floor for 0 participation
    else:
        # Linear scale from min_grade+0.5 to max_grade for 1-max participations
        return min_grade + 0.5 + (participations - 1) * (max_grade - min_grade - 0.5) / (max_participations - 1)


def logarithmic_grading(participations, min_grade=1.0, max_grade=5.0):
    """
    Logarithmic scaling - very generous to lower participations
    
    Args:
        participations: Number of total participations
        min_grade: Minimum grade to assign
        max_grade: Maximum grade to assign
    
    Returns:
        float: Grade from min_grade to max_grade
    """
    if participations == 0:
        return min_grade
    else:
        # Logarithmic scaling
        max_log = np.log(12)  # log(11+1)
        current_log = np.log(participations + 1)
        normalized = current_log / max_log
        return min_grade + normalized * (max_grade - min_grade)


def square_root_grading(participations, max_participations=11, min_grade=0.5, max_grade=5.0):
    """
    Square root scaling - more generous to lower participations
    
    Args:
        participations: Number of total participations
        max_participations: Maximum observed participations for scaling
        min_grade: Minimum grade to assign
        max_grade: Maximum grade to assign
    
    Returns:
        float: Grade from min_grade to max_grade
    """
    if participations == 0:
        return min_grade
    else:
        # Square root scaling gives more generous grades for lower participation
        normalized = np.sqrt(participations) / np.sqrt(max_participations)
        return min_grade + normalized * (max_grade - min_grade)


def percentage_grading(participations, max_participations=11, min_grade=0.0, max_grade=5.0):
    """
    Simple percentage-based grading
    
    Args:
        participations: Number of total participations
        max_participations: Maximum observed participations for scaling
        min_grade: Minimum grade to assign
        max_grade: Maximum grade to assign
    
    Returns:
        float: Grade from min_grade to max_grade
    """
    if participations == 0:
        return min_grade
    else:
        percentage = min(participations / max_participations, 1.0)
        return min_grade + percentage * (max_grade - min_grade)


def apply_grading_scheme(participation_data, scheme_name="tiered", student_roster=None):
    """
    Apply a grading scheme to participation data
    
    Args:
        participation_data: DataFrame with participation data
        scheme_name: Name of grading scheme to use
        student_roster: Optional DataFrame with complete student list
    
    Returns:
        pandas DataFrame with grades applied
    """
    
    # Available grading schemes
    schemes = {
        'tiered': tiered_grading,
        'linear': linear_grading,
        'logarithmic': logarithmic_grading,
        'square_root': square_root_grading,
        'percentage': percentage_grading
    }
    
    if scheme_name not in schemes:
        raise ValueError(f"Unknown grading scheme: {scheme_name}. Available: {list(schemes.keys())}")
    
    grading_function = schemes[scheme_name]
    
    # Make a copy to avoid modifying original data
    graded_data = participation_data.copy()
    
    # Apply grading scheme
    if 'total_participations' in graded_data.columns:
        graded_data['grade'] = graded_data['total_participations'].apply(grading_function)
    else:
        raise ValueError("DataFrame must contain 'total_participations' column")
    
    # If student roster is provided, merge to include all students
    if student_roster is not None:
        # Ensure roster has the right column names
        if 'ID' in student_roster.columns and 'user_id' not in student_roster.columns:
            student_roster = student_roster.rename(columns={'ID': 'user_id'})
        
        # Ensure user_id columns have the same data type for merging
        # Convert both to the same type (int64)
        try:
            student_roster['user_id'] = student_roster['user_id'].astype(int)
            graded_data['user_id'] = graded_data['user_id'].astype(int)
        except (ValueError, TypeError) as e:
            print(f"⚠️  Warning: Could not convert user_id to integer: {e}")
            # Fallback: convert both to string
            student_roster['user_id'] = student_roster['user_id'].astype(str)
            graded_data['user_id'] = graded_data['user_id'].astype(str)
        
        # Merge with roster
        graded_data = pd.merge(student_roster, graded_data, on='user_id', how='left')
        
        # Fill NaN values for students with no participation
        numeric_columns = graded_data.select_dtypes(include=[np.number]).columns
        graded_data[numeric_columns] = graded_data[numeric_columns].fillna(0)
        
        # Apply grading to students with 0 participation
        graded_data['grade'] = graded_data['total_participations'].apply(grading_function)
    
    # Round grades to 1 decimal place
    graded_data['grade'] = graded_data['grade'].round(1)
    
    if config.SHOW_PROGRESS:
        print(f"\n📊 GRADING APPLIED ({scheme_name.upper()} SCHEME):")
        print(f"   Total students: {len(graded_data)}")
        print(f"   Average grade: {graded_data['grade'].mean():.2f}")
        print(f"   Grade range: {graded_data['grade'].min():.1f} - {graded_data['grade'].max():.1f}")
        
        # Grade distribution
        grade_counts = graded_data['grade'].value_counts().sort_index()
        print(f"   Grade distribution:")
        for grade, count in grade_counts.items():
            print(f"      {grade:.1f}: {count} students")
    
    return graded_data


def preview_grading_schemes(participations_range=None):
    """
    Preview how different grading schemes would work
    
    Args:
        participations_range: List of participation counts to test
    
    Returns:
        pandas DataFrame with comparison of schemes
    """
    
    if participations_range is None:
        participations_range = list(range(0, 12))
    
    # Create comparison table
    comparison_data = {'Participations': participations_range}
    
    schemes = {
        'Tiered': tiered_grading,
        'Linear': linear_grading,
        'Logarithmic': logarithmic_grading,
        'Square Root': square_root_grading,
        'Percentage': percentage_grading
    }
    
    for scheme_name, scheme_func in schemes.items():
        comparison_data[scheme_name] = [round(scheme_func(p), 2) for p in participations_range]
    
    comparison_df = pd.DataFrame(comparison_data)
    
    print("Comparison of grading schemes:")
    print(comparison_df.to_string(index=False))
    
    return comparison_df


def export_graded_data(graded_data, filename=None):
    """
    Export graded participation data to CSV
    
    Args:
        graded_data: DataFrame with graded participation data
        filename: Output filename (optional)
    
    Returns:
        str: Filename of exported file
    """
    
    if filename is None:
        filename = "participation_grades_final.csv"
    
    # Select core columns for export
    core_columns = ['user_id', 'user_name', 'total_participations', 'grade']
    
    # Add Student column if it exists (from roster)
    if 'Student' in graded_data.columns:
        core_columns.insert(1, 'Student')
    
    # Filter columns that exist in the DataFrame
    export_columns = [col for col in core_columns if col in graded_data.columns]
    export_df = graded_data[export_columns]
    
    # Sort by grade (descending)
    export_df = export_df.sort_values('grade', ascending=False)
    
    export_df.to_csv(filename, index=False)
    
    if config.SHOW_PROGRESS:
        print(f"\n💾 Graded data exported to: {filename}")
        print(f"   Records: {len(export_df)}")
        print(f"   Columns: {export_columns}")
    
    return filename


def get_grading_statistics(graded_data):
    """
    Get detailed statistics about the grading results
    
    Args:
        graded_data: DataFrame with graded participation data
    
    Returns:
        dict: Statistics about the grading
    """
    
    stats = {
        'total_students': len(graded_data),
        'average_grade': graded_data['grade'].mean(),
        'median_grade': graded_data['grade'].median(),
        'min_grade': graded_data['grade'].min(),
        'max_grade': graded_data['grade'].max(),
        'std_grade': graded_data['grade'].std(),
        'students_with_zero': (graded_data['grade'] == 0).sum(),
        'students_with_max': (graded_data['grade'] == graded_data['grade'].max()).sum(),
        'grade_distribution': graded_data['grade'].value_counts().sort_index().to_dict()
    }
    
    return stats


def load_student_roster(filename):
    """
    Load student roster from CSV file
    
    Args:
        filename: Path to CSV file with student roster
    
    Returns:
        pandas DataFrame with student roster
    """
    
    try:
        roster = pd.read_csv(filename)
        
        # Standardize column names
        if 'ID' in roster.columns:
            roster = roster.rename(columns={'ID': 'user_id'})
        
        if config.SHOW_PROGRESS:
            print(f"📋 Student roster loaded: {len(roster)} students")
        
        return roster
        
    except FileNotFoundError:
        if config.SHOW_PROGRESS:
            print(f"⚠️  Student roster file not found: {filename}")
        return None
    except Exception as e:
        if config.SHOW_PROGRESS:
            print(f"❌ Error loading student roster: {e}")
        return None