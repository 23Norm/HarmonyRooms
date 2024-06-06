document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('addBTN').addEventListener('click', function(event) {
        const roomName = 'New Room';  // You can customize this as needed
        
        // Create a new div element
        const newDiv = document.createElement('div');
        
        // Optionally, add some content or styling to the new div
        newDiv.textContent = roomName;
        newDiv.style.display = 'flex';
        newDiv.style.alignItems = 'center';
        newDiv.style.border = '1px solid black';
        newDiv.style.margin = '15px';
        newDiv.style.height = '8%';
        newDiv.style.backgroundColor = '#444';
        newDiv.style.color = '#fff';
        newDiv.style.cursor = 
        
        // Append the new div to the right panel
        document.getElementById('room_list').appendChild(newDiv);
        
        // Send data to Flask route
        fetch('/add_room', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ room_name: roomName })
        })
        .then(response => response.json())
        .then(data => console.log(data))  // Handle response as needed
        .catch(error => console.error('Error:', error));
        
        event.preventDefault();
    });
});

document.getElementById('settingsBTN').addEventListener('click', function(){
    document.getElementById('settings').classList.add('active')
    event.preventDefault();
})

document.getElementById('closeBTN').addEventListener('click', function(){
    document.getElementById('settings').classList.remove('active')
})

