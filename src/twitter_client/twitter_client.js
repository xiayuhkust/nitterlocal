// Twitter client for extracting tweets using agent-twitter-client
import { Scraper } from 'agent-twitter-client';
import fs from 'fs';

async function extractTweets(username, maxTweets = 50, maxReplies = 0) {
  console.log(`Extracting tweets for @${username} (max tweets: ${maxTweets}, max replies: ${maxReplies})`);
  
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
    
    // Extract regular tweets from account
    console.log(`Getting regular tweets for @${username}...`);
    const tweets = scraper.getTweets(username, maxTweets);
    
    // Store tweets in an array
    const extractedTweets = [];
    let count = 0;
    
    for await (const tweet of tweets) {
      count++;
      console.log(`Processing regular tweet ${count}/${maxTweets} from @${username}: ${tweet.id}`);
      
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
        replyToId: tweet.replyToId,
        lang: tweet.lang || null,
        media: {
          photos: tweet.photos,
          videos: tweet.videos
        }
      });
      
      // Break if we've reached the maximum number of tweets
      if (count >= maxTweets) {
        console.log(`Reached maximum of ${maxTweets} regular tweets`);
        break;
      }
    }
    
    console.log(`Successfully extracted ${extractedTweets.length} regular tweets from @${username}`);
    
    // Extract replies if requested
    if (maxReplies > 0) {
      console.log(`Getting replies for @${username}...`);
      
      try {
        // Check if getTweetsAndReplies method exists
        if (typeof scraper.getTweetsAndReplies === 'function') {
          const replies = scraper.getTweetsAndReplies(username, maxReplies);
          
          let replyCount = 0;
          
          for await (const reply of replies) {
            replyCount++;
            console.log(`Processing reply ${replyCount}/${maxReplies} from @${username}: ${reply.id}`);
            
            // Only add if it's actually a reply
            if (reply.isReply) {
              extractedTweets.push({
                id: reply.id,
                text: reply.text,
                timestamp: reply.timestamp,
                timeParsed: reply.timeParsed ? reply.timeParsed.toISOString() : null,
                likes: reply.likes,
                retweets: reply.retweets,
                replies: reply.replies,
                views: reply.views,
                conversationId: reply.conversationId,
                hashtags: reply.hashtags,
                mentions: reply.mentions,
                urls: reply.urls,
                isReply: reply.isReply,
                isRetweet: reply.isRetweet,
                isQuoted: reply.isQuoted,
                replyToId: reply.replyToId,
                lang: reply.lang || null,
                media: {
                  photos: reply.photos,
                  videos: reply.videos
                }
              });
            }
            
            // Break if we've reached the maximum number of replies
            if (replyCount >= maxReplies) {
              console.log(`Reached maximum of ${maxReplies} replies`);
              break;
            }
          }
          
          console.log(`Successfully extracted replies from @${username}`);
        } else {
          console.warn('getTweetsAndReplies method does not exist in the Scraper class');
        }
      } catch (error) {
        console.error(`Error extracting replies for @${username}:`, error.message);
      }
    }
    
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

// Handle command line arguments
const username = process.argv[2];
const maxTweets = parseInt(process.argv[3] || '50');
const maxReplies = parseInt(process.argv[4] || '0');
const outputFile = process.argv[5] || 'tweets.json';

if (!username) {
  console.error('Usage: node twitter_client.js <username> [maxTweets] [maxReplies] [outputFile]');
  process.exit(1);
}

// Run the extraction function
extractTweets(username, maxTweets, maxReplies)
  .then(result => {
    // Save tweets and user ID to a JSON file
    fs.writeFileSync(outputFile, JSON.stringify(result, null, 2), 'utf8');
    console.log(`Tweets and user ID saved to ${outputFile}`);
  })
  .catch(error => {
    console.error('Error:', error.message);
    process.exit(1);
  });
