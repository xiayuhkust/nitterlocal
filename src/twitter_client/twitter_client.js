// Twitter client for extracting tweets using agent-twitter-client
import { Scraper } from 'agent-twitter-client';
import fs from 'fs';

async function extractTweets(username, maxTweets = 50) {
  console.log(`Extracting tweets for @${username} (max: ${maxTweets})`);
  
  try {
    // Create a new scraper instance
    const scraper = new Scraper();
    
    // Get user ID from username
    let userId = null;
    try {
      userId = await scraper.getUserIdByScreenName(username);
      console.log(`User ID for @${username}: ${userId}`);
    } catch (error) {
      console.warn(`Could not get user ID for @${username}: ${error.message}`);
    }
    
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
        inReplyToStatusId: tweet.inReplyToStatusId,
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
    
    // Return tweets and user ID
    return {
      tweets: extractedTweets,
      userId: userId
    };
    
  } catch (error) {
    console.error(`Error extracting tweets for @${username}:`, error.message);
    return { tweets: [], userId: null };
  }
}

async function extractTweetsAndReplies(username, maxTweets = 50) {
  console.log(`Extracting tweets and replies for @${username} (max: ${maxTweets})`);
  
  try {
    // Create a new scraper instance
    const scraper = new Scraper();
    
    // Get user ID from username
    let userId = null;
    try {
      userId = await scraper.getUserIdByScreenName(username);
      console.log(`User ID for @${username}: ${userId}`);
    } catch (error) {
      console.warn(`Could not get user ID for @${username}: ${error.message}`);
    }
    
    // Extract tweets and replies from account
    const tweetsAndReplies = scraper.getTweetsAndReplies(username, maxTweets);
    
    // Store tweets in an array
    const extractedTweets = [];
    let count = 0;
    
    for await (const tweet of tweetsAndReplies) {
      count++;
      console.log(`Processing tweet/reply ${count} from @${username}: ${tweet.id} (isReply: ${tweet.isReply})`);
      
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
        inReplyToStatusId: tweet.inReplyToStatusId,
        media: {
          photos: tweet.photos,
          videos: tweet.videos
        }
      });
      
      // Break if we've reached the maximum number of tweets
      if (count >= maxTweets) {
        console.log(`Reached maximum of ${maxTweets} tweets/replies`);
        break;
      }
    }
    
    console.log(`Successfully extracted ${extractedTweets.length} tweets/replies from @${username}`);
    
    // Return tweets and user ID
    return {
      tweets: extractedTweets,
      userId: userId
    };
    
  } catch (error) {
    console.error(`Error extracting tweets and replies for @${username}:`, error.message);
    return { tweets: [], userId: null };
  }
}

// Handle command line arguments
const username = process.argv[2];
const maxTweets = parseInt(process.argv[3] || '50');
const outputFile = process.argv[4] || 'tweets.json';
const includeReplies = process.argv.includes('--include-replies');

if (!username) {
  console.error('Usage: node twitter_client.js <username> [maxTweets] [outputFile] [--include-replies]');
  process.exit(1);
}

// Run the appropriate extraction function
const extractionFunction = includeReplies ? extractTweetsAndReplies : extractTweets;

extractionFunction(username, maxTweets)
  .then(result => {
    // Save tweets and user ID to a JSON file
    fs.writeFileSync(outputFile, JSON.stringify(result, null, 2), 'utf8');
    console.log(`Tweets and user ID saved to ${outputFile}`);
  })
  .catch(error => {
    console.error('Error:', error.message);
    process.exit(1);
  });
