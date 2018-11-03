window.extAsyncInit = function () {
    // the Messenger Extensions JS SDK is done loading 
    console.log("SDK done loading!")
    MessengerExtensions.getContext('348666849024201',
        function success(thread_context) {
            $.post("https://catchupbot.com/testing", {'hi': 'hello'}, function(data, status){
                console.log("sent")
            })
        },
        function error(err) {
            // error
        }
    );
};
