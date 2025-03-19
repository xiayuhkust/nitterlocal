/**
 * UUID v4 Polyfill for browsers that don't support crypto.randomUUID
 * This polyfill provides a fallback implementation for the crypto.randomUUID function
 * which is not supported in older browsers.
 */

(function() {
  // Only add the polyfill if the browser doesn't support crypto.randomUUID
  if (typeof crypto !== 'undefined' && !crypto.randomUUID) {
    // Implementation of UUID v4 generation
    crypto.randomUUID = function() {
      return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
        (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
      );
    };
    
    console.log('UUID polyfill loaded for browsers without crypto.randomUUID support');
  }
})();
