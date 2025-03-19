# Twitter API Limitations

## Language Field
The Twitter API doesn't consistently provide language information for tweets. In our database, only about 0.02% of tweets have language information. The API returns null for the lang field in most cases.

## View Count Field
The Twitter API provides view count data for approximately 47% of tweets. The availability of this data varies and may depend on the age and type of tweet.

## Historical Data Limitations
The Twitter API has limitations on retrieving older tweets. Tweets from several years ago (like those from 2017) may not be accessible through the API.

## Handling Missing Data
Our code is designed to handle these limitations gracefully:
- It attempts to extract all available fields from the API
- It stores whatever data is available
- It handles null values appropriately

No code changes are needed to address these limitations as they are inherent to the Twitter API itself.
