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

async function extractReplies(username, maxTweets = 50) {
  console.log(`Extracting replies for @${username} (max: ${maxTweets})`);
  
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
    
    // Filter to only include replies
    const extractedReplies = [];
    let count = 0;
    
    for await (const tweet of tweetsAndReplies) {
      if (tweet.isReply) {
        count++;
        console.log(`Processing reply ${count} from @${username}: ${tweet.id}`);
        
        extractedReplies.push({
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
          console.log(`Reached maximum of ${maxTweets} replies`);
          break;
        }
      }
    }
    
    console.log(`Successfully extracted ${extractedReplies.length} replies from @${username}`);
    
    // Return replies and user ID
    return {
      tweets: extractedReplies,
      userId: userId
    };
    
  } catch (error) {
    console.error(`Error extracting replies for @${username}:`, error.message);
    return { tweets: [], userId: null };
  }
}

async function extractRepliesToUser(username, maxTweets = 50) {
  console.log(`Extracting replies to @${username} (max: ${maxTweets})`);
  
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
    
    // Get the user's tweets first
    const userTweets = [];
    const tweets = scraper.getTweets(username, 20); // Get a reasonable number of tweets to search for replies
    
    console.log(`Fetching recent tweets from @${username} to find replies...`);
    
    for await (const tweet of tweets) {
      userTweets.push(tweet.id);
      if (userTweets.length >= 20) break; // Limit to 20 tweets to avoid excessive API calls
    }
    
    console.log(`Found ${userTweets.length} tweets from @${username}`);
    
    // Use search to find replies to these tweets
    const extractedReplies = [];
    let count = 0;
    
    for (const tweetId of userTweets) {
      // Search for replies to this tweet
      const searchQuery = `to:${username} conversation_id:${tweetId}`;
      console.log(`Searching for replies with query: ${searchQuery}`);
      
      try {
        const searchResults = scraper.searchTweets(searchQuery, Math.ceil(maxTweets / userTweets.length));
        
        for await (const reply of searchResults) {
          // Skip if this is from the user themselves
          if (reply.username && reply.username.toLowerCase() === username.toLowerCase()) {
            continue;
          }
          
          count++;
          console.log(`Processing reply ${count} to @${username}: ${reply.id}`);
          
          extractedReplies.push({
            id: reply.id,
            text: reply.text,
            timestamp: reply.timestamp,
            timeParsed: reply.timeParsed ? reply.timeParsed.toISOString() : null,
            likes: reply.likes,
            retweets: reply.retweets,
            replies: reply.replies,
            views: reply.views,
            conversationId: reply.conversationId || tweetId,
            hashtags: reply.hashtags,
            mentions: reply.mentions,
            urls: reply.urls,
            isReply: true,
            isRetweet: reply.isRetweet,
            isQuoted: reply.isQuoted,
            inReplyToStatusId: tweetId,
            author: reply.username || 'unknown', // The author is the replying user
            media: {
              photos: reply.photos,
              videos: reply.videos
            }
          });
          
          // Break if we've reached the maximum number of tweets
          if (count >= maxTweets) {
            console.log(`Reached maximum of ${maxTweets} replies`);
            break;
          }
        }
      } catch (error) {
        console.warn(`Error searching for replies to tweet ${tweetId}: ${error.message}`);
        continue;
      }
      
      // Break if we've reached the maximum number of tweets
      if (count >= maxTweets) {
        break;
      }
    }
    
    console.log(`Successfully extracted ${extractedReplies.length} replies to @${username}`);
    
    // Return replies and user ID
    return {
      tweets: extractedReplies,
      userId: userId
    };
    
  } catch (error) {
    console.error(`Error extracting replies to @${username}:`, error.message);
    return { tweets: [], userId: null };
  }
}

// Handle command line arguments
const username = process.argv[2];
const maxTweets = parseInt(process.argv[3] || '50');
const outputFile = process.argv[4] || 'tweets.json';
const getReplies = process.argv.includes('--replies');
const getRepliesToUser = process.argv.includes('--replies-to');

if (!username) {
  console.error('Usage: node twitter_client.js <username> [maxTweets] [outputFile] [--replies|--replies-to]');
  process.exit(1);
}

// Run the extraction function
let extractionFunction = extractTweets;
if (getReplies) extractionFunction = extractReplies;
if (getRepliesToUser) extractionFunction = extractRepliesToUser;

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
