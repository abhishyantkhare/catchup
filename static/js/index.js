
window.extAsyncInit = function () {
    // the Messenger Extensions JS SDK is done loading 
    console.log("SDK done loading!")
    MessengerExtensions.getContext('348666849024201',
        function success(thread_context) {
            console.log(thread_context)
	    $.ajax({
		type: "POST",
		url: "https://catchupbot.com/testing",
		dataType: "json",
		data: JSON.stringify(thread_context),
		contentType: 'application/json'
		})
        },
        function error(err) {
            // error
            console.log(err)
        }
    );
};
