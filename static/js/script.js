document.addEventListener('DOMContentLoaded', () => {

    const chatWindow = document.getElementById("chat-window");
    let currentPersona = 'business';

    const scrollToBottom = () => {
        chatWindow.scrollTop = chatWindow.scrollHeight;
    };

    const handleCommand = (command) => {
        let chatWindow = document.getElementById("chat-window");

        if (command === '/file') {
            let fileUploadElem = document.createElement("div");
            fileUploadElem.className = "p-2 mb-2 bg-light rounded";

            // Create an 'a' element that you can later change the text of
            let fileLink = document.createElement("a");
            fileLink.href = "#";
            fileLink.textContent = "Upload a file";
            fileLink.onclick = () => document.getElementById('file-upload').click();
            fileUploadElem.appendChild(fileLink);
            fileLink.scrollIntoView({ behavior: 'smooth' });

            // Create a loader element
            let loaderElem = document.createElement("div");
            loaderElem.id = "loader";
            loaderElem.style.display = "none";
            loaderElem.innerHTML = "Uploading...";
            loaderElem.scrollIntoView({ behavior: 'smooth' });

            // Create a container for the loader
            let loaderContainerElem = document.createElement("div");
            loaderContainerElem.className = "d-flex justify-content-end align-items-center";
            loaderContainerElem.style.marginLeft = "auto";
            loaderContainerElem.style.marginRight = "5px";
            loaderContainerElem.appendChild(loaderElem);

            fileUploadElem.appendChild(loaderContainerElem);

            chatWindow.appendChild(fileUploadElem);

            let fileInputElem = document.createElement("input");
            fileInputElem.type = "file";
            fileInputElem.id = "file-upload";
            fileInputElem.style.display = "none";
            fileInputElem.onchange = (e) => {
                let formData = new FormData();
                let file = e.target.files[0];
                formData.append('file', file);

                // Show the loader
                loaderElem.style.display = "block";

                // Fetch and wait for it to finish
                fetch('/upload_file', {method: 'POST', body: formData}).then(() => {
                    // Change the text of the link after the upload is complete
                    fileLink.textContent = `DONE! ${file.name} successfully uploaded.`;
                    // Hide the loader
                    loaderElem.style.display = "none";
                    // Remove the file input element so that a new one can be created next time
                    fileInputElem.remove();
                    scrollToBottom();
                });
            };
            chatWindow.appendChild(fileInputElem);
            scrollToBottom();
        }

        if (command === '/folder') {
            let folderUploadElem = document.createElement("div");
            folderUploadElem.className = "p-2 mb-2 bg-light rounded";

            // Create an 'a' element to trigger folder selection
            let folderLink = document.createElement("a");
            folderLink.href = "#";
            folderLink.textContent = "Upload a folder";
            folderLink.onclick = () => document.getElementById('folder-upload').click();
            folderUploadElem.appendChild(folderLink);

            chatWindow.appendChild(folderUploadElem);

            let folderInputElem = document.createElement("input");
            folderInputElem.type = "file";
            folderInputElem.id = "folder-upload";
            folderInputElem.style.display = "none";
            folderInputElem.setAttribute("webkitdirectory", "");
            folderInputElem.onchange = (e) => {
                let files = e.target.files;
                for (let i = 0; i < files.length; i++) {
                    let formData = new FormData();
                    formData.append('file', files[i]);

                    fetch('/upload_folder', {method: 'POST', body: formData}).then(() => {
                        let statusMessage = document.createElement("div");
                        statusMessage.className = "p-2 mb-2 bg-light rounded";
                        statusMessage.textContent = `DONE! ${files[i].name} successfully uploaded.`;
                        chatWindow.appendChild(statusMessage);
                    });
                }
            };
            chatWindow.appendChild(folderInputElem);
        }
        if (command === '/plan') {
            let planElem = document.createElement("div");
            planElem.className = "p-2 mb-2 bg-light rounded";

            // Add the desired content to the div
            planElem.textContent = "Loading Strategic planning and decision-making\n\nFormulate long-term strategies.\n" +
                "Assess market conditions.\n" +
                "Make informed decisions aligned with organizational goals.\n";

            chatWindow.appendChild(planElem);

            // Now call get_persona() with 'business' as an argument
            fetch('/get_persona', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({'persona_type': 'business'})
            })
                .then(response => response.json())
                .then(data => {
                    // Here you would handle the returned persona. For now I'll just log it.
                    currentPersona = data;
                    console.log(data);
                });

            scrollToBottom();
        }


    };

    const sendMessage = () => {
        let chatInput = document.getElementById("chat-input");
        let chatWindow = document.getElementById("chat-window");

        if (chatInput.value.trim() !== '') {
            const message = chatInput.value;

            if (message.startsWith('/')) {
                handleCommand(message);
                chatInput.value = '';
                return;
            }

            let userMessageElem = document.createElement("div");
            userMessageElem.className = "p-2 mb-2 rounded";
            userMessageElem.innerHTML = `<span class="bg-light px-1 p-1 rounded-pill">${message}</span>`;
            chatWindow.appendChild(userMessageElem);
            userMessageElem.scrollIntoView({ behavior: 'smooth' });

            chatInput.value = '';

            // Append skeleton loader
            let skeletonLoader = document.createElement("div");
            skeletonLoader.className = "p-2 mb-2 bg-primary text-white rounded skeleton-loader";
            chatWindow.appendChild(skeletonLoader);
            skeletonLoader.scrollIntoView({ behavior: 'smooth' });

            fetch('/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({'message': message, 'persona_template': currentPersona.template})
            })

                .then(response => response.json())
                .then(data => {
                    // Remove skeleton loader
                    chatWindow.removeChild(skeletonLoader);

                    // Append model message
                    let modelMessageElem = document.createElement("div");
                    modelMessageElem.className = "p-2 mb-2 rounded d-flex justify-content-end";
                    modelMessageElem.innerHTML = `<span class="bg-primary text-white px-3 p-1 rounded-pill">${data.response}</span>`;
                    chatWindow.appendChild(modelMessageElem);

                    // Scroll to the bottom using scrollIntoView
                    modelMessageElem.scrollIntoView({ behavior: 'smooth' });
                });
        }
    };




    document.querySelector('#send-button').onclick = sendMessage;

    // Listening for Enter key
    document.querySelector('#chat-input').addEventListener("keydown", function(e) {
        if (e.keyCode === 13) {
            sendMessage();
        }
    });
});




    document.getElementById('send-button').addEventListener('click', function() {
    var messageInput = document.getElementById('chat-input');
    var message = messageInput.value;
    messageInput.value = '';

    // Send the message to the server
    fetch('/send_message', {
    method: 'POST',
    headers: {
    'Content-Type': 'application/json'
},
    body: JSON.stringify({message: message, persona_template: '{{ persona }}'})
})
    .then(response => response.json())
    .then(data => {
    // Add the message and response to the chat window
    var chatWindow = document.getElementById('chat-window');
    chatWindow.innerHTML += '<p>You: ' + message + '</p>';
    chatWindow.innerHTML += '<p>NPC: ' + data.response + '</p>';
});
});

//     window.onload = function() {
//     var introMessage = "Hello, I am {{ bot_name }}. How can I help you?";
//     var chatWindow = document.getElementById('chat-window');
//     var messageNode = document.createElement("p");
//     messageNode.textContent = introMessage;
//     chatWindow.appendChild(messageNode);
// }

