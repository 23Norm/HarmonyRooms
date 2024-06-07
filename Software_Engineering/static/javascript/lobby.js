document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('addBTN').addEventListener('click', function(event) {

        function createRoomItem(data){

            const newDiv = document.createElement('div');
            newDiv.setAttribute('data-music', data.music_path);

            newDiv.textContent = data.code;
            newDiv.style.display = 'flex';
            newDiv.style.alignItems = 'center';
            newDiv.style.border = '1px solid black';
            newDiv.style.margin = '15px';
            newDiv.style.height = '8%';
            newDiv.style.backgroundColor = '#444';
            newDiv.style.color = '#fff';
            newDiv.style.cursor = 
           
            document.getElementById('room_list').appendChild(newDiv);
            
            newDiv.addEventListener('click', () => {
                const player = document.getElementById('music')
                player.src = data.music_path
                player.play()
            })
        }

        fetch('/add_room')
        .then(response => response.json())
        .then(data => createRoomItem(data)) 
        .catch(error => console.error('Error:', error));
        
        event.preventDefault();
    });
});

document.getElementById('settingsBTN').addEventListener('click', () => {
    document.getElementById('settings').classList.add('active')
})  

document.getElementById('closeBTN').addEventListener('click', function(){
    document.getElementById('settings').classList.remove('active')
})

document.querySelectorAll('.roomClass').forEach(room => {
    room.addEventListener('click', () => {
        const player = document.getElementById('music')
        player.src = room.dataset.music
        player.play()
    })  
})