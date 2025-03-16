// Twitter profile client for extracting profile data using agent-twitter-client
import { Scraper } from 'agent-twitter-client';
import fs from 'fs';

async function extractProfileData(username) {
  console.log(`Extracting profile data for @${username}`);
  
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
    
    // Get profile information
    let profile = null;
    try {
      profile = await scraper.getProfile(username);
      console.log(`Got profile for @${username}`);
    } catch (error) {
      console.warn(`Could not get profile for @${username}: ${error.message}`);
    }
    
    // Return the profile data and user ID
    return {
      userId,
      profile
    };
    
  } catch (error) {
    console.error(`Error extracting profile for @${username}:`, error.message);
    return { userId: null, profile: null };
  }
}

// Handle command line arguments
const username = process.argv[2];
const outputFile = process.argv[3] || 'profile_data.json';

if (!username) {
  console.error('Usage: node twitter_profile_client.js <username> [outputFile]');
  process.exit(1);
}

// Run the extraction function
extractProfileData(username)
  .then(result => {
    // Save profile data to a JSON file
    fs.writeFileSync(outputFile, JSON.stringify(result, null, 2), 'utf8');
    console.log(`Profile data saved to ${outputFile}`);
  })
  .catch(error => {
    console.error('Error:', error.message);
    process.exit(1);
  });
