const socket = io();

document.getElementById('sendBtn').addEventListener('click', function(){
    document.getElementById('sendBtn').disabled = true;
    let msg = document.getElementById('msg').value;
    document.getElementById('msg').value = "";
    socket.emit('sendMsg', msg);
});

socket.on('chat', function(data){
    let sessionUID = document.getElementById('sessionUID').value;
    let msgStr = 
    `<li class="list-group-item list-group-item-dark themsg"><span style="color: blue; font-weight: bolder;">${data['msgUsername']}:</span> <span class="themsg">${data['msg']}</span><span style="float: right;">${data['msgTimestamp']}</span>
    <input type="hidden" class="msgids" name="msgid" id="msgID" value="${data['msgID']}">`
    
    if (data['msgUID']==sessionUID || sessionUID==data['adminUID']){
        msgStr +=
        `<div><button type="button" class="btn btn-danger" style="float: right;" id="deleteMsg" onclick="deleteBtn.call(this)">Delete</button></div>`
    }
    msgStr += '</li>';
    document.getElementById('chat_box').innerHTML = msgStr + document.getElementById('chat_box').innerHTML;
});

function deleteBtn(){
    let msgID = this.parentElement.parentElement.children;
    msgID = msgID[3].value
    // console.log(msgID)
    socket.emit('deleteMsg', msgID);
}

socket.on('deleteChat', function(data){
    let allMsgs = document.getElementsByClassName('msgids');
    for(let i=0; i<allMsgs.length; i++){
        if(data['msgID']==allMsgs[i].value){
            allMsgs[i].parentElement.remove();
        }
    }
    // location.reload();
});

function clearAllBtn(){
    socket.emit('clearchat');
}

socket.on('clearAllChat', function(data){
    let chat_box = document.getElementById('chat_box');
    chat_box.innerHTML = "";
});
