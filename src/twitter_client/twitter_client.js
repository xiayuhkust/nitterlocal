// Twitter client for extracting tweets using agent-twitter-client
import { Scraper } from 'agent-twitter-client';
import fs from 'fs';

async function extractTweets(username, maxTweets = 50) {
  console.log(`Extracting tweets for @${username} (max: ${maxTweets})`);
  
  try {
    // Create a new scraper instance
    const scraper = new Scraper();
    
    // Extract tweets from account
    const tweets = scraper.getTweets(username, maxTweets);
    
    // Store tweets in an array
    const extractedTweets = [];
    let count = 0;
    
    for await (const tweet of tweets) {
      count++;
      console.log(`Processing tweet ${count} from @${username}: ${tweet.id}`);
      
      extractedTweets.push({
        id: tweet.id,
        text: tweet.text,
        timestamp: tweet.timestamp,
        timeParsed: tweet.timeParsed ? tweet.timeParsed.toISOString() : null,
        likes: tweet.likes,
        retweets: tweet.retweets,
        replies: tweet.replies,
        views: tweet.views,
        conversationId: tweet.conversationId,
        hashtags: tweet.hashtags,
        mentions: tweet.mentions,
        urls: tweet.urls,
        isReply: tweet.isReply,
        isRetweet: tweet.isRetweet,
        isQuoted: tweet.isQuoted,
        media: {
          photos: tweet.photos,
          videos: tweet.videos
        }
      });
      
      // Break if we've reached the maximum number of tweets
      if (count >= maxTweets) {
        console.log(`Reached maximum of ${maxTweets} tweets`);
        break;
      }
    }
    
    console.log(`Successfully extracted ${extractedTweets.length} tweets from @${username}`);
    
    return extractedTweets;
    
  } catch (error) {
    console.error(`Error extracting tweets for @${username}:`, error.message);
    return [];
  }
}

// Handle command line arguments
const username = process.argv[2];
const maxTweets = parseInt(process.argv[3] || '50');
const outputFile = process.argv[4] || 'tweets.json';

if (!username) {
  console.error('Usage: node twitter_client.js <username> [maxTweets] [outputFile]');
  process.exit(1);
}

// Run the extraction function
extractTweets(username, maxTweets)
  .then(tweets => {
    // Save tweets to a JSON file
    fs.writeFileSync(outputFile, JSON.stringify(tweets, null, 2), 'utf8');
    console.log(`Tweets saved to ${outputFile}`);
  })
  .catch(error => {
    console.error('Error:', error.message);
    process.exit(1);
  });
