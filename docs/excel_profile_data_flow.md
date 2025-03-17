# Excel Profile Data Flow

This document explains the complete data flow from Excel processing to database storage, focusing on tweet_count and profile data.

## Overview

The Excel processing workflow involves several steps:

1. Reading an Excel file with Twitter URLs and KOL character data
2. Normalizing Twitter URLs (converting x.com to twitter.com)
3. Extracting Twitter handles from URLs
4. Retrieving Twitter profile data using the Twitter profile client
5. Updating the url_tracking table with profile data
6. Creating or updating kol_character records with character data
7. Linking kol_character records to url_tracking records

## Detailed Flow

### 1. Excel File Processing

The process starts with an Excel file containing Twitter URLs and KOL character data:

```python
# In process_excel_with_profile.py
def process_excel_file(excel_path, db_path=None):
    """Process an Excel file with Twitter profile data"""
    # Read Excel file
    df = pd.read_excel(excel_path)
    
    # Process each row
    for index, row in df.iterrows():
        # Get Twitter URL
        twitter_url = row.get('Twitter url')
        
        # Normalize URL
        normalized_url = normalize_twitter_url(twitter_url)
        
        # Extract handle from URL
        handle = extract_handle_from_url(normalized_url)
        
        # Get user ID from Twitter client
        user_id = get_user_id(handle)
        
        # Update URL in tracking database
        url_tracking_id = update_url_in_tracking(normalized_url, handle, user_id, db_path)
        
        # Update KOL character data
        update_kol_character(row, handle, url_tracking_id, db_path)
        
        # Update profile data
        update_profile_data(normalized_url, handle, db_path)
```

### 2. URL Normalization

URLs are normalized to ensure consistency:

```python
# In url_utils.py
def normalize_twitter_url(url):
    """Normalize Twitter URL to standard format"""
    if not url:
        return None
    
    # Convert x.com to twitter.com
    if 'x.com' in url:
        url = url.replace('x.com', 'twitter.com')
    
    # Convert nitter.net to twitter.com
    if 'nitter.net' in url:
        url = url.replace('nitter.net', 'twitter.com')
    
    # Ensure URL starts with https://
    if not url.startswith('http'):
        url = 'https://' + url
    
    return url
```

### 3. Twitter Profile Data Retrieval

Profile data is retrieved using the Twitter profile client:

```javascript
// In twitter_profile_client.js
async function getProfileData(handle) {
    // Get profile data from Twitter
    const userData = await twitterClient.getUserByUsername(handle);
    
    // Extract profile data
    const profile = {
        tweetsCount: userData.statuses_count || 0,
        followersCount: userData.followers_count || 0,
        followingCount: userData.friends_count || 0,
        // Other profile fields...
    };
    
    return {
        userId: userData.id_str,
        profile: profile
    };
}
```

```python
# In update_profile_data.py
def get_profile_data(self, handle):
    """Get profile data for a Twitter handle"""
    # Run Twitter profile client
    profile_data = self._run_twitter_profile_client(handle)
    
    if profile_data:
        # Extract profile data
        profile = profile_data.get('profile', {})
        
        return {
            'user_id': profile_data.get('userId'),
            'screen_name': handle,
            'followers_count': profile.get('followersCount', 0),
            'following_count': profile.get('followingCount', 0) or profile.get('friendsCount', 0),
            'tweet_count': profile.get('tweetsCount', 0) or profile.get('statusesCount', 0),
            # Other profile fields...
        }
```

### 4. Database Update

Profile data is updated in the url_tracking table:

```python
# In update_profile_data.py
def update_profile_in_db(self, url, profile_data):
    """Update profile data in the database"""
    # Build update query
    update_fields = []
    update_values = []
    
    for key, value in profile_data.items():
        if key != 'url':  # Skip the URL field
            update_fields.append(f"{key} = ?")
            update_values.append(value)
    
    # Add URL for WHERE clause
    update_values.append(url)
    
    # Execute update query
    update_query = f'''
    UPDATE url_tracking 
    SET {', '.join(update_fields)}
    WHERE url = ?
    '''
    
    cursor.execute(update_query, update_values)
```

### 5. KOL Character Update

KOL character data is updated in the kol_character table:

```python
# In process_excel_with_profile.py
def update_kol_character(row, handle, url_tracking_id, db_path):
    """Update KOL character data in the database"""
    # Extract character data from Excel row
    character_data = {
        'kol_id': row.get('kol_id'),
        'kol_screen_name': handle,
        'bio': row.get('bio'),
        'lore': row.get('lore'),
        'knowledge': row.get('knowledge'),
        'postExamples': row.get('postExamples'),
        'topics': row.get('topics'),
        'style_all': row.get('style_all'),
        'style_chat': row.get('style_chat'),
        'style_post': row.get('style_post'),
        'adjectives': row.get('adjectives'),
        'url_tracking_id': url_tracking_id
    }
    
    # Check if record exists
    cursor.execute("SELECT id FROM kol_character WHERE url_tracking_id = ?", (url_tracking_id,))
    existing_record = cursor.fetchone()
    
    if existing_record:
        # Update existing record
        update_fields = []
        update_values = []
        
        for key, value in character_data.items():
            if key != 'url_tracking_id':  # Skip the url_tracking_id field
                update_fields.append(f"{key} = ?")
                update_values.append(value)
        
        # Add url_tracking_id for WHERE clause
        update_values.append(url_tracking_id)
        
        update_query = f'''
        UPDATE kol_character 
        SET {', '.join(update_fields)}
        WHERE url_tracking_id = ?
        '''
        
        cursor.execute(update_query, update_values)
    else:
        # Insert new record
        insert_query = f'''
        INSERT INTO kol_character ({', '.join(character_data.keys())})
        VALUES ({', '.join(['?' for _ in character_data])})
        '''
        
        cursor.execute(insert_query, list(character_data.values()))
```

## Data Verification

The data can be verified using the display_url_tracking_record.py script:

```python
# In display_url_tracking_record.py
def display_joined_record(db_path, screen_name=None, url=None):
    """Display joined record from url_tracking and kol_character tables"""
    # Get url_tracking record
    url_tracking_query = "SELECT * FROM url_tracking WHERE "
    params = []
    
    if screen_name:
        url_tracking_query += "screen_name = ? COLLATE NOCASE"
        params = [screen_name]
    else:
        url_tracking_query += "url LIKE ? COLLATE NOCASE"
        params = [f"%{url}%"]
    
    cursor.execute(url_tracking_query, params)
    url_tracking_row = cursor.fetchone()
    
    # Get url_tracking column names
    cursor.execute("PRAGMA table_info(url_tracking)")
    url_tracking_columns = [row[1] for row in cursor.fetchall()]
    
    # Create a dictionary for url_tracking data
    url_tracking_data = {url_tracking_columns[i]: url_tracking_row[i] for i in range(len(url_tracking_columns))}
    
    # Get the url_tracking_id
    url_tracking_id = url_tracking_data.get('id')
    
    # Get kol_character record
    kol_character_data = {}
    if url_tracking_id is not None:
        cursor.execute("SELECT * FROM kol_character WHERE url_tracking_id = ?", [url_tracking_id])
        kol_character_row = cursor.fetchone()
        
        if kol_character_row:
            # Get kol_character column names
            cursor.execute("PRAGMA table_info(kol_character)")
            kol_character_columns = [row[1] for row in cursor.fetchall()]
            
            # Create a dictionary for kol_character data
            kol_character_data = {kol_character_columns[i]: kol_character_row[i] for i in range(len(kol_character_columns))}
    
    # Display results
    print(f"\n=== Joined Record for {'@' + screen_name if screen_name else url} ===")
    
    # Display url_tracking columns
    print("\n--- URL Tracking Fields ---")
    for col, value in url_tracking_data.items():
        print(f"{col}: {value}")
    
    # Display kol_character columns
    print("\n--- KOL Character Fields ---")
    if kol_character_data:
        for col, value in kol_character_data.items():
            print(f"{col}: {value}")
    else:
        print("No KOL character data found for this record")
```

## Conclusion

The Excel processing workflow successfully retrieves and stores tweet_count and other profile data in the url_tracking table. The data flow is complete and works as expected, with tweet_count being correctly stored in the database.
