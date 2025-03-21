import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re
from collections import Counter

def process_emails(service, messages):
    """Process email messages into a pandas DataFrame."""
    if not messages:
        return pd.DataFrame()

    # Process messages in chunks to avoid overloading
    email_data = []
    total = len(messages)

    for i, msg in enumerate(messages):
        message_id = msg['id']
        message_detail = service.users().messages().get(
            userId='me', 
            id=message_id, 
            format='full'
        ).execute()

        # Extract message data
        payload = message_detail.get('payload', {})
        headers = payload.get('headers', [])

        # Get header values
        subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), '')
        from_email = next((header['value'] for header in headers if header['name'].lower() == 'from'), '')
        to_email = next((header['value'] for header in headers if header['name'].lower() == 'to'), '')
        date_str = next((header['value'] for header in headers if header['name'].lower() == 'date'), '')
        message_id_header = next((header['value'] for header in headers if header['name'].lower() == 'message-id'), '')
        in_reply_to = next((header['value'] for header in headers if header['name'].lower() == 'in-reply-to'), '')

        # Clean from/to fields to extract email
        from_email = extract_email_address(from_email)
        to_email = extract_email_address(to_email)

        # Parse date
        try:
            date = pd.to_datetime(date_str, errors='coerce')
            if pd.isna(date):
                date = datetime.fromtimestamp(int(message_detail['internalDate']) / 1000)
        except:
            # Fallback to internal date if parsing fails
            try:
                date = datetime.fromtimestamp(int(message_detail['internalDate']) / 1000)
            except:
                date = pd.NaT

        # Extract labels
        labels = message_detail.get('labelIds', [])

        # Determine if sent or received
        is_sent = 'SENT' in labels

        # Extract body
        body = extract_body(payload)

        # Word count
        word_count = len(body.split()) if body else 0

        # Get thread ID
        thread_id = message_detail.get('threadId', '')

        # Store the data
        email_data.append({
            'id': message_id,
            'thread_id': thread_id,
            'subject': subject,
            'from': from_email,
            'to': to_email,
            'date': date,
            'is_sent': is_sent,
            'labels': labels,
            'body': body[:500],  # Limit body text size
            'word_count': word_count,
            'message_id_header': message_id_header,
            'in_reply_to': in_reply_to,
            'importance': 'high' if any(h.get('name', '').lower() == 'importance' and h.get('value', '').lower() == 'high' for h in headers) else 'normal',
            'has_attachments': bool(payload.get('parts', [])),
            'read': 'UNREAD' not in labels,
            'thread_size': 1  # Will be updated later
        })

    # Create dataframe and sort by date
    df = pd.DataFrame(email_data)
    if not df.empty:
        df = df.sort_values('date', ascending=False).reset_index(drop=True)

    return df

def extract_email_address(text):
    """Extract email address from text."""
    match = re.search(r'[\w\.-]+@[\w\.-]+', text)
    if match:
        return match.group(0).lower()
    return text.lower()

def extract_body(payload):
    """Extract body text from payload."""
    if not payload:
        return ""

    # Check if this part has a body
    if 'body' in payload and 'data' in payload['body']:
        from base64 import urlsafe_b64decode
        data = payload['body']['data']
        try:
            decoded_data = urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            return decoded_data
        except:
            return ""

    # If not, check for multipart content
    if 'parts' in payload:
        text_content = ""
        for part in payload['parts']:
            # Recursively extract content from parts
            text_content += extract_body(part)
        return text_content

    return ""

def categorize_emails(df):
    """Categorize emails based on content and labels."""
    # Make a copy to avoid modifying the original
    df = df.copy()

    # Initialize category column
    df['category'] = 'Other'

    # Common keywords for categories
    categories = {
        'Newsletter': ['newsletter', 'update', 'weekly', 'monthly', 'subscription'],
        'Promotional': ['offer', 'discount', 'sale', 'promotion', 'deal', 'save', 'buy', 'purchase'],
        'Social': ['facebook', 'twitter', 'instagram', 'linkedin', 'social', 'connect', 'friend', 'follow'],
        'Finance': ['payment', 'invoice', 'bill', 'receipt', 'transaction', 'financial', 'bank', 'credit', 'debit'],
        'Travel': ['flight', 'booking', 'reservation', 'hotel', 'travel', 'trip', 'vacation', 'journey'],
        'Shopping': ['order', 'shipping', 'delivery', 'track', 'product', 'item', 'purchase'],
        'Work': ['project', 'meeting', 'deadline', 'report', 'client', 'presentation', 'team'],
        'Personal': ['hey', 'hello', 'hi', 'family', 'friend', 'personal']
    }

    # Check labels first
    for idx, row in df.iterrows():
        labels = row['labels']
        subject = str(row['subject']).lower()
        body = str(row['body']).lower()

        # Gmail categories based on labels
        if 'CATEGORY_SOCIAL' in labels:
            df.at[idx, 'category'] = 'Social'
        elif 'CATEGORY_PROMOTIONS' in labels:
            df.at[idx, 'category'] = 'Promotional'
        elif 'CATEGORY_UPDATES' in labels:
            df.at[idx, 'category'] = 'Newsletter'
        elif 'CATEGORY_FORUMS' in labels:
            df.at[idx, 'category'] = 'Forums'
        elif 'CATEGORY_PERSONAL' in labels:
            df.at[idx, 'category'] = 'Personal'
        elif 'SENT' in labels:
            df.at[idx, 'category'] = 'Sent'
        else:
            # Check keywords in subject and body
            for category, keywords in categories.items():
                if any(keyword in subject for keyword in keywords) or any(keyword in body for keyword in keywords):
                    df.at[idx, 'category'] = category
                    break

    return df

def get_email_metrics(df):
    """Calculate various email metrics from the dataframe."""
    metrics = {}

    # Basic counts
    metrics["total_emails"] = len(df)
    metrics["sent_emails"] = df['is_sent'].sum()
    metrics["received_emails"] = metrics["total_emails"] - metrics["sent_emails"]

    # Date range
    if not df.empty:
        date_range = (df['date'].max() - df['date'].min()).days
        metrics["date_range_days"] = max(1, date_range)  # Avoid division by zero
        metrics["avg_daily_volume"] = metrics["total_emails"] / metrics["date_range_days"]
    else:
        metrics["date_range_days"] = 0
        metrics["avg_daily_volume"] = 0

    # Word counts
    metrics["avg_word_count"] = df['word_count'].mean() if 'word_count' in df.columns else 0

    # Category distribution
    if 'category' in df.columns:
        metrics["category_counts"] = df['category'].value_counts().to_dict()

    # Sender analysis
    metrics["unique_senders"] = df['from'].nunique()
    metrics["top_senders"] = df['from'].value_counts().head(10).to_dict()

    # Thread metrics
    metrics["unique_threads"] = df['thread_id'].nunique()
    metrics["avg_thread_length"] = df.groupby('thread_id').size().mean()

    return metrics

def analyze_response_times(df):
    """Analyze response times within email threads."""
    if df.empty or 'thread_id' not in df.columns:
        return pd.DataFrame()

    # Create a copy of the dataframe
    thread_df = df.copy()

    # Sort by thread_id and date
    thread_df = thread_df.sort_values(['thread_id', 'date'])

    # Group by thread_id
    thread_groups = thread_df.groupby('thread_id')

    response_data = []

    for thread_id, group in thread_groups:
        if len(group) < 2:
            continue

        for i in range(1, len(group)):
            prev_email = group.iloc[i-1]
            curr_email = group.iloc[i]

            # Skip if the emails are not a conversation (same sender responding to themselves)
            if prev_email['from'] == curr_email['from']:
                continue

            # Compute response time
            response_time_seconds = (curr_email['date'] - prev_email['date']).total_seconds()
            response_time_hours = response_time_seconds / 3600

            # Skip if response time is negative (emails out of order) or too long (> 7 days)
            if response_time_hours < 0 or response_time_hours > 168:  # 7 days
                continue

            response_data.append({
                'thread_id': thread_id,
                'response_time_hours': response_time_hours,
                'responder': curr_email['from'],
                'original_sender': prev_email['from'],
                'response_date': curr_email['date'],
                'is_sent_by_me': curr_email['is_sent']
            })

    return pd.DataFrame(response_data)

def extract_common_words(df, column='subject', n=100):
    """Extract most common words from a text column."""
    if df.empty or column not in df.columns:
        return Counter()

    # Combine all text
    all_text = ' '.join(df[column].astype(str).tolist())

    # Clean text and tokenize
    text = re.sub(r'[^\w\s]', '', all_text.lower())
    words = text.split()

    # Remove common stop words
    stop_words = {'the', 'and', 're', 'to', 'a', 'in', 'for', 'of', 'on', 'with', 'is', 'your', 
                 'from', 'this', 'that', 'you', 'it', 'at', 'are', 'be', 'as', 'by', 'or', 'an',
                 'will', 'can', 'has', 'have', 'had', 'was', 'were', 'been', 'my', 'our', 'i', 'we',
                 'they', 'their', 'he', 'she', 'his', 'her', 'its', 'am', 'me', 'us', 'him'}

    filtered_words = [word for word in words if word not in stop_words and len(word) > 2]

    # Count and return most common
    word_counts = Counter(filtered_words)
    return word_counts.most_common(n)