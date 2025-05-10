document.getElementById('restart-btn').addEventListener('click', function() {
    fetch('/control/restart', {method: 'POST'})
        .then(resp => resp.json())
        .then(data => {
            document.getElementById('control-status').innerText = data.message;
        });
});
document.getElementById('stop-btn').addEventListener('click', function() {
    fetch('/control/stop', {method: 'POST'})
        .then(resp => resp.json())
        .then(data => {
            document.getElementById('control-status').innerText = data.message;
        });
});
