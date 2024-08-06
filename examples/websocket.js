import WebSocket, { WebSocketServer } from 'ws';
import fs from 'fs';


const wss = new WebSocketServer({
    port: 8080,
});
wss.on("connection", (ws) => {
    console.log("WebSocket client connected");

    // Event listener for receiving messages from the client
    ws.on("message", (message) => {
        try {
            const parsed = JSON.parse(message)
            saveBase64Image(parsed.base64_img, parsed._requestId + '_image.webp');
        } catch (e) {
            console.log("Error occured when getting a message", e)
        }
    });

    // Event listener for the WebSocket connection closing
    ws.on("close", () => {
        console.log("WebSocket client disconnected");
    });
});

function saveBase64Image(base64String, filePath) {
    const binaryData = Buffer.from(base64String, 'base64');

    fs.writeFile(filePath, binaryData, 'binary', (err) => {
        if (err) {
            console.error('Error saving the image:', err);
        } else {
            console.log('Image saved successfully:', filePath);
        }
    });
}
console.log("Listening on 8080. Use ws://localhost:8080 as the websocket URL in the websocket serving node");

function sendMessage(message) {
    wss.clients.forEach((client) => {
        console.log("Sending the prompt - ", message.prompt)
        if (client.readyState === WebSocket.OPEN) {
            client.send(message);
        }
    });
}


let i = 0
setInterval(() => sendMessage(JSON.stringify({
    _requestId: ++i,
    prompt: "Robot saying 'it works!'",
})), 5000)