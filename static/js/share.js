let message = {
    "attachment":{
      "type":"template",
      "payload":{
        "template_type":"generic",
        "elements": [{
        "title":"I miss you! Let's hang out :)",
        "default_action":{
          "type":"web_url",
          "url": "https://catchupbot.com"
        },
        }]
      }
    }
  };
messenger_extensions = true;
  window.extAsyncInit = function () {
    MessengerExtensions.beginShareFlow(function(share_response) {
        // User dismissed without error, but did they share the message?
        if(share_response.is_sent){
          // The user actually did share. 
          // Perhaps close the window w/ requestCloseBrowser().
           }
          //
          MessengerExtensions.requestCloseBrowser(function success() {
  // webview closed
   }, function error(err) {
  //   // an error occurred
     });},
      function(errorCode, errorMessage) {      
      // An error occurred in the process
      alert(errorMessage)
      
      },
      message,
      "current_thread");

  }
