document.addEventListener('DOMContentLoaded', function() {
    const socket = io();
    let currentRoomCode = null; 

    function rejoinRooms() {
        socket.emit('rejoin_rooms', {});
    }

    socket.on('connect', () => {
        rejoinRooms();
    });

    function createRoomDiv(data) {
        const newDiv = document.createElement('div');
        newDiv.setAttribute('data-music', data.music_path);
        newDiv.setAttribute('data-room-code', data.code);
        newDiv.classList.add('roomItem');

        const roomText = document.createElement('span');
        roomText.textContent = data.code;
        newDiv.appendChild(roomText);

        newDiv.style.display = 'flex';
        newDiv.style.alignItems = 'center';
        newDiv.style.justifyContent = 'center';
        newDiv.style.border = '1px solid black';
        newDiv.style.margin = '5px';
        newDiv.style.height = '8%';
        newDiv.style.width = '95%';
        newDiv.style.backgroundColor = '#444';
        newDiv.style.color = '#fff';
        newDiv.style.cursor = 'pointer';
        newDiv.style.borderRadius = '15px'

        document.getElementById('room_list').appendChild(newDiv);
    
        newDiv.addEventListener('click', () => {
            joinRoom(data.code);
        });

    }

    function joinRoom(roomCode) {

        const validCodePattern = /^[a-z]-[a-z]-[a-z]-[a-z]-[a-z]-[a-z]-[a-z]-[a-z]-[a-z]$/;
    
        if (!validCodePattern.test(roomCode)) {
            alert("Invalid room code format. Please enter a valid code like 'x-x-x-x-x-x-x-x-x'.");
            return;
        }

        const roomForm = document.querySelector('.mediaPlayer form');
        roomForm.innerHTML = '';
    
        socket.emit('join', { 'room': roomCode });
        currentRoomCode = roomCode; 
    
        fetch(`/room_details/${roomCode}`)
            .then(response => response.json())
            .then(data => {
                roomForm.innerHTML = `
                    <h2>Room: ${data.code}</h2>
                `;
    
                document.getElementById('music').src = data.music_path;
                document.getElementById('music').play();

                if (!document.querySelector(`.room_list div[data-room-code="${data.code}"]`)) {
                    createRoomDiv(data);
                }
            })
            .catch(error => console.error('Error:', error));
    }

    document.getElementById('EnterBTN').addEventListener('click', function() {
        const roomCodeInput = document.getElementById('code');
        const roomCode = roomCodeInput.value.trim();
        joinRoom(roomCode);
        roomCodeInput.value = ''; 
    });

    document.getElementById('addBTN').addEventListener('click', function(event) {
        fetch('/add_room')
            .then(response => response.json())
            .then(data => createRoomDiv(data))
            .catch(error => console.error('Error:', error));

        event.preventDefault();
    });

    document.getElementById('settingsBTN').addEventListener('click', function(event) {
        document.getElementById('settings').classList.add('active');
        event.preventDefault();
    });

    document.getElementById('closeBTN').addEventListener('click', function() {
        document.getElementById('settings').classList.remove('active');
    });

    document.querySelectorAll('.roomClass').forEach(room => {
        room.addEventListener('click', () => {
            const player = document.getElementById('music');
            player.src = room.dataset.music;
            player.play();
        });
    });

    document.getElementById('voteYesBtn').addEventListener('click', function() {
        alert("You voted YES to skip the song.");
        socket.emit('vote_to_skip', { room: currentRoomCode, vote: 'yes' });
    });

    document.getElementById('voteNoBtn').addEventListener('click', function() {
        alert("You voted NO to keep the song.");
        socket.emit('vote_to_skip', { room: currentRoomCode, vote: 'no' });
    });

    socket.on('skip_song', (data) => {
        const player = document.getElementById('music');
        player.src = data.music_path;
        player.play();
    });

    socket.on('no_skip', () => {
        alert("The song will continue playing.");
    });

    socket.on('vote_received', (data) => {
        if (data.status === 'success') {
            alert(`Your vote for "${data.vote}" has been recorded.`);
        } else if (data.status === 'already_voted') {
            alert("You have already voted.");
        } else if (data.status === 'pending') {
            alert(data.message);
        }
    });

    socket.on('vote_count_update', (data) => {
        alert(`Current Votes:\nYES: ${data.yes}\nNO: ${data.no}`);
    });

});
