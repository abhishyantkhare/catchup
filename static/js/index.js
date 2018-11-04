
window.extAsyncInit = function () {
    // the Messenger Extensions JS SDK is done loading 
    console.log("SDK done loading!")
    MessengerExtensions.getContext('348666849024201',
        function success(thread_context) {
            socket.emit('fbdata_event', 'hello')
        },
        function error(err) {
            // error
        }
    );
};
