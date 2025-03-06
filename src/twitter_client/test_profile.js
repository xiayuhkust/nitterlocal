// Test script to check if we can retrieve profile information
import { Scraper } from 'agent-twitter-client';
import fs from 'fs';

async function getProfileInfo(username) {
  console.log(`Getting profile info for @${username}`);
  
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
    
    return {
      userId,
      profile
    };
    
  } catch (error) {
    console.error(`Error getting profile for @${username}:`, error.message);
    return { userId: null, profile: null };
  }
}

// Handle command line arguments
const username = process.argv[2];
const outputFile = process.argv[3] || 'profile.json';

if (!username) {
  console.error('Usage: node test_profile.js <username> [outputFile]');
  process.exit(1);
}

// Run the function
getProfileInfo(username)
  .then(result => {
    // Save profile to a JSON file
    fs.writeFileSync(outputFile, JSON.stringify(result, null, 2), 'utf8');
    console.log(`Profile saved to ${outputFile}`);
  })
  .catch(error => {
    console.error('Error:', error.message);
    process.exit(1);
  });
