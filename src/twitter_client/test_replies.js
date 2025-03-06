// Test script to check if the agent-twitter-client library supports getTweetsAndReplies
import { Scraper } from 'agent-twitter-client';

async function testReplies(username, maxTweets = 5) {
  console.log(`Testing getTweetsAndReplies for @${username} (max: ${maxTweets})`);
  
  try {
    // Create a new scraper instance
    const scraper = new Scraper();
    
    // Check if getTweetsAndReplies method exists
    if (typeof scraper.getTweetsAndReplies !== 'function') {
      console.error('Error: getTweetsAndReplies method does not exist in the Scraper class');
      return;
    }
    
    // Extract tweets and replies from account
    console.log(`Getting tweets and replies for @${username}...`);
    const tweetsAndReplies = scraper.getTweetsAndReplies(username, maxTweets);
    
    // Store tweets in an array
    const extractedTweets = [];
    let count = 0;
    
    for await (const tweet of tweetsAndReplies) {
      count++;
      console.log(`Processing tweet ${count} from @${username}: ${tweet.id}`);
      console.log(`Is reply: ${tweet.isReply}, Conversation ID: ${tweet.conversationId}`);
      
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
        isReply: tweet.isReply,
        replyToId: tweet.replyToId,
        isRetweet: tweet.isRetweet,
        isQuoted: tweet.isQuoted
      });
      
      // Break if we've reached the maximum number of tweets
      if (count >= maxTweets) {
        console.log(`Reached maximum of ${maxTweets} tweets`);
        break;
      }
    }
    
    console.log(`Successfully extracted ${extractedTweets.length} tweets and replies from @${username}`);
    console.log(JSON.stringify(extractedTweets, null, 2));
    
  } catch (error) {
    console.error(`Error testing getTweetsAndReplies for @${username}:`, error.message);
  }
}

// Handle command line arguments
const username = process.argv[2] || 'elonmusk';
const maxTweets = parseInt(process.argv[3] || '5');

// Run the test function
testReplies(username, maxTweets)
  .catch(error => {
    console.error('Error:', error.message);
    process.exit(1);
  });
