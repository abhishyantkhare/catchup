let message = {
    "attachment":{
      "type":"template",
      "payload":{
        "template_type":"generic",
        "elements": [{
          "buttons":[{
            "type":"web_url",
            "url":"https://catchupbot.com",
            "title":"Let's Catch Up!"
          }]
        }]
      }
    }
  };

  window.extAsyncInit = function () {
    MessengerExtensions.beginShareFlow(function(share_response) {
        // User dismissed without error, but did they share the message?
        if(share_response.is_sent){
          // The user actually did share. 
          // Perhaps close the window w/ requestCloseBrowser().
        }
      }, 
      function(errorCode, errorMessage) {      
      // An error occurred in the process
      
      },
      message,
      "current_thread");

  }