import pandas as pd

# Create a simple Excel file with Twitter URLs
df = pd.DataFrame({'twitter_url': ['https://twitter.com/elonmusk']})
df.to_excel('/tmp/test_files/test file with spaces.xlsx', index=False)
print("Test Excel file created successfully")
