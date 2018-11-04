
window.extAsyncInit = function () {
    // the Messenger Extensions JS SDK is done loading 
    console.log("SDK done loading!")
    MessengerExtensions.getContext('348666849024201',
        function success(thread_context) {
            console.log(thread_context)
            tid = thread_context.tid
	    $.ajax({
		type: "GET",
        url: "https://catchupbot.com/getchat?id=" + tid,
        success: function getSuccess(data, status, jqXHR) {
            console.log(data)
            if(!(data.credentials === "NONE")) {
                console.log("stored in DB!")
            }
            else{
                data = {'chat_id': tid}
                $.ajax({
                    type: "POST",
                    url: "https://catchupbot.com/storechat",
                    data: JSON.stringify(data),
                    contentType: 'application/json'
                })
            }
        }
		})
        },
        function error(err) {
            // error
            console.log(err)
        }
    );
};
