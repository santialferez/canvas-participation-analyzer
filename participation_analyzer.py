"""
Canvas Participation Analyzer - Core Analysis Functions
"""

import requests
import pandas as pd
from collections import defaultdict
from datetime import datetime
import re
import config


def clean_html(text):
    """Remove HTML tags and clean up text content"""
    if not text:
        return ""
    # Remove HTML tags
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', text)
    # Replace HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&amp;', '&')
    # Clean up whitespace
    text = ' '.join(text.split())
    return text


def get_replies_from_entry(entry):
    """Extract replies that are already included in the entry data"""
    replies = []
    
    # Check for recent_replies (Canvas often includes them)
    recent_replies = entry.get('recent_replies', [])
    if recent_replies:
        replies.extend(recent_replies)
    
    # Check for replies field
    direct_replies = entry.get('replies', [])
    if direct_replies:
        replies.extend(direct_replies)
    
    return replies


def is_professor(user_name, user_id, professor_names, professor_ids):
    """Check if a user is identified as a professor"""
    return (
        user_name in professor_names or 
        str(user_id) in map(str, professor_ids) or
        any(prof_name.lower() in user_name.lower() for prof_name in professor_names)
    )


def get_forum_participation(course_id, headers, professor_names=None, professor_ids=None):
    """
    Analyze student participation in discussion forums
    
    Args:
        course_id: Canvas course ID
        headers: API headers with authorization
        professor_names: List of professor names to exclude
        professor_ids: List of professor user IDs to exclude
    
    Returns:
        pandas DataFrame with forum participation data (students only)
    """
    
    if professor_names is None:
        professor_names = config.PROFESSOR_NAMES
    if professor_ids is None:
        professor_ids = config.PROFESSOR_IDS
    
    if config.SHOW_PROGRESS:
        print("📋 ANALYZING DISCUSSION FORUMS...")
        print(f"   Professor filter: {professor_names}")
        print("="*60)
    
    # Dictionary to store participation data
    participation_data = defaultdict(lambda: {
        'user_id': None,
        'user_name': '',
        'is_professor': False,
        'total_participations': 0,
        'main_posts': 0,
        'replies': 0,
        'topics_participated': set(),
        'first_participation': None,
        'last_participation': None
    })
    
    # Get all discussion topics
    topics_url = f"{config.CANVAS_BASE_URL}/courses/{course_id}/discussion_topics"
    topics_response = requests.get(topics_url, headers=headers)
    
    if topics_response.status_code != 200:
        print(f"❌ Error fetching discussion topics: {topics_response.status_code}")
        print(f"Response: {topics_response.text}")
        return pd.DataFrame(columns=['user_id', 'user_name', 'topic_id', 'topic_title', 'entry_type', 'timestamp'])
    
    try:
        topics = topics_response.json()
    except ValueError as e:
        print(f"❌ Error parsing JSON response: {e}")
        print(f"Response content: {topics_response.text}")
        return pd.DataFrame(columns=['user_id', 'user_name', 'topic_id', 'topic_title', 'entry_type', 'timestamp'])
    
    if not isinstance(topics, list):
        print(f"❌ Unexpected response format. Expected list, got {type(topics)}")
        print(f"Response: {topics}")
        return pd.DataFrame(columns=['user_id', 'user_name', 'topic_id', 'topic_title', 'entry_type', 'timestamp'])
    
    total_entries_processed = 0
    
    for topic in topics:
        topic_id = topic['id']
        topic_title = topic['title']
        
        if config.SHOW_PROGRESS:
            print(f"   Processing: {topic_title}")
        
        # Get entries for this topic
        entries_url = f"{config.CANVAS_BASE_URL}/courses/{course_id}/discussion_topics/{topic_id}/entries"
        entries_response = requests.get(entries_url, headers=headers)
        
        if entries_response.status_code == 200:
            try:
                entries = entries_response.json()
            except ValueError as e:
                if config.SHOW_PROGRESS:
                    print(f"   Error parsing entries JSON for topic {topic_title}: {e}")
                continue
            
            def process_entry(entry, is_reply=False):
                nonlocal total_entries_processed
                
                user_id = entry.get('user_id')
                user_name = entry.get('user_name', '')
                created_at = entry.get('created_at')
                
                if user_id and user_name:
                    # Check if this is the professor
                    is_prof = is_professor(user_name, user_id, professor_names, professor_ids)
                    
                    # Initialize or update user data
                    user_data = participation_data[user_id]
                    user_data['user_id'] = user_id
                    user_data['user_name'] = user_name
                    user_data['is_professor'] = is_prof
                    user_data['total_participations'] += 1
                    user_data['topics_participated'].add(topic_title)
                    
                    if is_reply:
                        user_data['replies'] += 1
                    else:
                        user_data['main_posts'] += 1
                    
                    # Track participation dates
                    if created_at:
                        if user_data['first_participation'] is None or created_at < user_data['first_participation']:
                            user_data['first_participation'] = created_at
                        if user_data['last_participation'] is None or created_at > user_data['last_participation']:
                            user_data['last_participation'] = created_at
                    
                    total_entries_processed += 1
                
                # Process replies
                replies = get_replies_from_entry(entry)
                for reply in replies:
                    process_entry(reply, is_reply=True)
            
            # Process all main entries
            for entry in entries:
                process_entry(entry, is_reply=False)
    
    if config.SHOW_PROGRESS:
        print(f"   Total entries processed: {total_entries_processed}")
    
    # Convert to DataFrame
    df_data = []
    for user_id, data in participation_data.items():
        df_data.append({
            'user_id': data['user_id'],
            'user_name': data['user_name'],
            'is_professor': data['is_professor'],
            'forum_participations': data['total_participations'],
            'forum_main_posts': data['main_posts'],
            'forum_replies': data['replies'],
            'forum_topics_count': len(data['topics_participated']),
            'first_forum_participation': data['first_participation'],
            'last_forum_participation': data['last_participation']
        })
    
    df = pd.DataFrame(df_data)
    
    if not df.empty:
        # Sort by total participations (descending)
        df = df.sort_values('forum_participations', ascending=False).reset_index(drop=True)
        
        # Show professor activity and filter
        if config.EXCLUDE_PROFESSOR:
            professor_data = df[df['is_professor'] == True]
            if not professor_data.empty and config.SHOW_PROGRESS:
                print(f"\n👨‍🏫 PROFESSOR FORUM ACTIVITY (excluded from student analysis):")
                for _, prof in professor_data.iterrows():
                    print(f"   {prof['user_name']}: {prof['forum_participations']} participations")
            
            # Return only student data
            student_df = df[df['is_professor'] == False].reset_index(drop=True)
            if config.SHOW_PROGRESS:
                print(f"\n📊 Forum results: {len(student_df)} students")
            
            return student_df
        else:
            return df
    
    return df


def get_message_participation(course_id, headers, start_date=None, professor_names=None, professor_ids=None):
    """
    Analyze student participation in internal messages (conversations)
    
    Args:
        course_id: Canvas course ID
        headers: API headers with authorization
        start_date: Filter messages from this date onwards
        professor_names: List of professor names to exclude
        professor_ids: List of professor user IDs to exclude
    
    Returns:
        pandas DataFrame with message participation data (students only)
    """
    
    if professor_names is None:
        professor_names = config.PROFESSOR_NAMES
    if professor_ids is None:
        professor_ids = config.PROFESSOR_IDS
    if start_date is None:
        start_date = config.SEMESTER_START_DATE
    
    # Convert start_date to datetime if it's a string
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    
    if config.SHOW_PROGRESS:
        print(f"\n📧 ANALYZING INTERNAL MESSAGES...")
        print(f"   Professor filter: {professor_names}")
        print(f"   From date: {start_date.strftime('%Y-%m-%d')}")
        print("="*60)
    
    # Dictionary to store message participation data
    message_data = defaultdict(lambda: {
        'user_id': None,
        'user_name': '',
        'is_professor': False,
        'total_messages': 0,
        'conversations_initiated': 0,
        'conversations_participated': set(),
        'first_message': None,
        'last_message': None
    })
    
    # Get conversations with pagination
    page = 1
    per_page = 100
    total_conversations = 0
    processed_messages = 0
    
    while True:
        conversations_url = f"{config.CANVAS_BASE_URL}/conversations"
        params = {
            'per_page': per_page,
            'page': page,
            'include[]': ['participant_avatars']
        }
        
        if course_id:
            params['filter[]'] = f'course_{course_id}'
        
        try:
            response = requests.get(conversations_url, headers=headers, params=params)
            
            if response.status_code != 200:
                if config.SHOW_PROGRESS:
                    print(f"   Error fetching conversations: {response.status_code}")
                break
                
            try:
                conversations = response.json()
            except ValueError as e:
                if config.SHOW_PROGRESS:
                    print(f"   Error parsing conversations JSON: {e}")
                break
            
            if not conversations:
                break
                
            if config.SHOW_PROGRESS:
                print(f"   Processing page {page} ({len(conversations)} conversations)...")
            
            for conv in conversations:
                conv_id = conv.get('id')
                last_message_at = conv.get('last_message_at')
                
                # Filter by date if specified
                if start_date and last_message_at:
                    conv_date = datetime.strptime(last_message_at[:19], '%Y-%m-%dT%H:%M:%S')
                    if conv_date < start_date:
                        continue
                
                total_conversations += 1
                
                # Get detailed conversation messages
                messages_url = f"{config.CANVAS_BASE_URL}/conversations/{conv_id}"
                try:
                    msg_response = requests.get(messages_url, headers=headers)
                    if msg_response.status_code == 200:
                        try:
                            conv_detail = msg_response.json()
                        except ValueError as e:
                            if config.SHOW_PROGRESS:
                                print(f"   Error parsing conversation detail JSON: {e}")
                            continue
                        messages = conv_detail.get('messages', [])
                        
                        for i, message in enumerate(messages):
                            author_id = message.get('author_id')
                            
                            if author_id:
                                # Get participant info for this author
                                participants = conv_detail.get('participants', [])
                                author_name = "Unknown User"
                                
                                for participant in participants:
                                    if participant.get('id') == author_id:
                                        author_name = participant.get('name', 'Unknown User')
                                        break
                                
                                # Check if this is the professor
                                is_prof = is_professor(author_name, author_id, professor_names, professor_ids)
                                
                                # Initialize or update user data
                                user_data = message_data[author_id]
                                user_data['user_id'] = author_id
                                user_data['user_name'] = author_name
                                user_data['is_professor'] = is_prof
                                user_data['total_messages'] += 1
                                user_data['conversations_participated'].add(conv_id)
                                
                                # Track if this user initiated the conversation (first message)
                                if i == len(messages) - 1:  # Messages are in reverse order
                                    user_data['conversations_initiated'] += 1
                                
                                # Track message dates
                                created_at = message.get('created_at')
                                if created_at:
                                    if user_data['first_message'] is None or created_at < user_data['first_message']:
                                        user_data['first_message'] = created_at
                                    if user_data['last_message'] is None or created_at > user_data['last_message']:
                                        user_data['last_message'] = created_at
                                
                                processed_messages += 1
                
                except Exception as e:
                    continue
            
            page += 1
            
            # Break if we got fewer results than requested (last page)
            if len(conversations) < per_page:
                break
                
        except Exception as e:
            if config.SHOW_PROGRESS:
                print(f"   Error fetching conversations page {page}: {e}")
            break
    
    if config.SHOW_PROGRESS:
        print(f"   Total conversations processed: {total_conversations}")
        print(f"   Total messages processed: {processed_messages}")
    
    # Convert to DataFrame
    df_data = []
    for user_id, data in message_data.items():
        df_data.append({
            'user_id': data['user_id'],
            'user_name': data['user_name'],
            'is_professor': data['is_professor'],
            'messages_total': data['total_messages'],
            'messages_initiated': data['conversations_initiated'],
            'messages_conversations_count': len(data['conversations_participated']),
            'first_message': data['first_message'],
            'last_message': data['last_message']
        })
    
    df = pd.DataFrame(df_data)
    
    if not df.empty:
        # Sort by total messages (descending)
        df = df.sort_values('messages_total', ascending=False).reset_index(drop=True)
        
        # Show professor activity and filter
        if config.EXCLUDE_PROFESSOR:
            professor_data = df[df['is_professor'] == True]
            if not professor_data.empty and config.SHOW_PROGRESS:
                print(f"\n👨‍🏫 PROFESSOR MESSAGE ACTIVITY (excluded from student analysis):")
                for _, prof in professor_data.iterrows():
                    print(f"   {prof['user_name']}: {prof['messages_total']} messages")
            
            # Return only student data
            student_df = df[df['is_professor'] == False].reset_index(drop=True)
            if config.SHOW_PROGRESS:
                print(f"\n📧 Message results: {len(student_df)} students")
            
            return student_df
        else:
            return df
    
    return df


def create_comprehensive_analysis(forum_df, messages_df):
    """
    Create a comprehensive analysis combining forum and message participation
    
    Args:
        forum_df: DataFrame with forum participation data
        messages_df: DataFrame with internal messages participation data
    
    Returns:
        pandas DataFrame with complete participation data for all students
    """
    
    if config.SHOW_PROGRESS:
        print("\n🔄 CREATING COMPREHENSIVE PARTICIPATION ANALYSIS...")
        print("="*70)
    
    # Get all unique users from both sources
    all_users_data = {}
    
    # Process forum participants
    if not forum_df.empty:
        for _, row in forum_df.iterrows():
            user_id = str(row['user_id'])
            
            all_users_data[user_id] = {
                'user_id': user_id,
                'user_name': row['user_name'],
                'forum_participations': row['forum_participations'],
                'forum_main_posts': row['forum_main_posts'],
                'forum_replies': row['forum_replies'],
                'forum_topics_count': row['forum_topics_count'],
                'messages_total': 0,
                'messages_initiated': 0,
                'messages_conversations_count': 0,
                'first_forum_participation': row.get('first_forum_participation'),
                'last_forum_participation': row.get('last_forum_participation'),
                'first_message': None,
                'last_message': None
            }
    
    # Process message participants
    if not messages_df.empty:
        for _, row in messages_df.iterrows():
            user_id = str(row['user_id'])
            
            if user_id in all_users_data:
                # Update existing user with message data
                all_users_data[user_id]['messages_total'] = row['messages_total']
                all_users_data[user_id]['messages_initiated'] = row['messages_initiated']
                all_users_data[user_id]['messages_conversations_count'] = row['messages_conversations_count']
                all_users_data[user_id]['first_message'] = row.get('first_message')
                all_users_data[user_id]['last_message'] = row.get('last_message')
            else:
                # Add new user from messages only
                all_users_data[user_id] = {
                    'user_id': user_id,
                    'user_name': row['user_name'],
                    'forum_participations': 0,
                    'forum_main_posts': 0,
                    'forum_replies': 0,
                    'forum_topics_count': 0,
                    'messages_total': row['messages_total'],
                    'messages_initiated': row['messages_initiated'],
                    'messages_conversations_count': row['messages_conversations_count'],
                    'first_forum_participation': None,
                    'last_forum_participation': None,
                    'first_message': row.get('first_message'),
                    'last_message': row.get('last_message')
                }
    
    # Convert to DataFrame
    df_data = []
    for user_id, data in all_users_data.items():
        # Calculate total participations
        total_participations = data['forum_participations'] + data['messages_total']
        
        # Determine activity level
        if total_participations >= 15:
            activity_level = "High"
        elif total_participations >= 8:
            activity_level = "Medium"
        elif total_participations >= 1:
            activity_level = "Low"
        else:
            activity_level = "Inactive"
        
        # Determine communication preferences
        has_forum = data['forum_participations'] > 0
        has_messages = data['messages_total'] > 0
        
        if has_forum and has_messages:
            communication_preference = "Both channels"
            uses_both_channels = True
        elif has_forum:
            communication_preference = "Forums only"
            uses_both_channels = False
        elif has_messages:
            communication_preference = "Messages only"
            uses_both_channels = False
        else:
            communication_preference = "No activity"
            uses_both_channels = False
        
        df_data.append({
            'user_id': data['user_id'],
            'user_name': data['user_name'],
            'forum_participations': data['forum_participations'],
            'forum_main_posts': data['forum_main_posts'],
            'forum_replies': data['forum_replies'],
            'forum_topics_count': data['forum_topics_count'],
            'messages_total': data['messages_total'],
            'messages_initiated': data['messages_initiated'],
            'messages_conversations_count': data['messages_conversations_count'],
            'total_participations': total_participations,
            'activity_level': activity_level,
            'communication_preference': communication_preference,
            'uses_both_channels': uses_both_channels,
            'first_forum_participation': data['first_forum_participation'],
            'last_forum_participation': data['last_forum_participation'],
            'first_message': data['first_message'],
            'last_message': data['last_message']
        })
    
    df = pd.DataFrame(df_data)
    
    if not df.empty:
        # Sort by total participations (descending)
        df = df.sort_values('total_participations', ascending=False).reset_index(drop=True)
        
        if config.SHOW_PROGRESS:
            print(f"\n📊 COMPREHENSIVE RESULTS:")
            print(f"   Total students: {len(df)}")
            print(f"   Students with forum activity: {len(df[df['forum_participations'] > 0])}")
            print(f"   Students with message activity: {len(df[df['messages_total'] > 0])}")
            print(f"   Students using both channels: {len(df[df['uses_both_channels'] == True])}")
        
        return df
    
    return df


def analyze_participation(course_id, canvas_token, include_forums=True, include_messages=True):
    """
    Main function to analyze student participation in Canvas
    
    Args:
        course_id: Canvas course ID
        canvas_token: Canvas API token
        include_forums: Whether to include forum participation
        include_messages: Whether to include message participation
    
    Returns:
        pandas DataFrame with comprehensive participation data
    """
    
    # Setup API headers
    headers = {
        "Authorization": f"Bearer {canvas_token}"
    }
    
    forum_df = pd.DataFrame()
    messages_df = pd.DataFrame()
    
    # Get forum participation
    if include_forums:
        forum_df = get_forum_participation(course_id, headers)
    
    # Get message participation
    if include_messages:
        messages_df = get_message_participation(course_id, headers)
    
    # Create comprehensive analysis
    comprehensive_df = create_comprehensive_analysis(forum_df, messages_df)
    
    return comprehensive_df


def export_participation_data(df, filename=None):
    """
    Export participation data to CSV file
    
    Args:
        df: DataFrame with participation data
        filename: Output filename (optional)
    
    Returns:
        str: Filename of exported file
    """
    
    if filename is None:
        filename = config.DEFAULT_OUTPUT_FILE
    
    # Export core columns for grading
    export_columns = [
        'user_id', 'user_name', 'forum_participations', 'messages_total', 
        'total_participations', 'activity_level', 'communication_preference'
    ]
    
    # Filter columns that exist in the DataFrame
    available_columns = [col for col in export_columns if col in df.columns]
    export_df = df[available_columns]
    
    export_df.to_csv(filename, index=False)
    
    if config.SHOW_PROGRESS:
        print(f"\n💾 Participation data exported to: {filename}")
        print(f"   Records: {len(export_df)}")
        print(f"   Columns: {len(available_columns)}")
    
    return filename