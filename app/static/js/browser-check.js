/**
 * Simple browser compatibility check
 * This script checks if the browser supports basic features needed for the application
 */
(function() {
  // Check if basic features are supported
  var isCompatible = true;
  var errorMessages = [];
  
  // Check for XMLHttpRequest
  if (typeof XMLHttpRequest === 'undefined') {
    isCompatible = false;
    errorMessages.push('您的浏览器不支持XMLHttpRequest，请使用更现代的浏览器。');
  }
  
  // Check for FormData
  if (typeof FormData === 'undefined') {
    isCompatible = false;
    errorMessages.push('您的浏览器不支持FormData，请使用更现代的浏览器。');
  }
  
  // Display error message if browser is not compatible
  if (!isCompatible) {
    window.onload = function() {
      var container = document.querySelector('.container');
      if (container) {
        var errorDiv = document.createElement('div');
        errorDiv.style.color = '#dc3545';
        errorDiv.style.padding = '20px';
        errorDiv.style.marginBottom = '20px';
        errorDiv.style.backgroundColor = '#f8d7da';
        errorDiv.style.borderRadius = '4px';
        
        var errorTitle = document.createElement('h3');
        errorTitle.textContent = '浏览器兼容性问题';
        errorDiv.appendChild(errorTitle);
        
        for (var i = 0; i < errorMessages.length; i++) {
          var errorPara = document.createElement('p');
          errorPara.textContent = errorMessages[i];
          errorDiv.appendChild(errorPara);
        }
        
        container.insertBefore(errorDiv, container.firstChild);
      }
    };
  }
})();
