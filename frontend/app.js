const toneList = document.querySelector('#tone-list');
const form = document.querySelector('#chat-form');
const input = document.querySelector('#message-input');
const conversation = document.querySelector('#conversation');
const welcome = document.querySelector('#welcome');
const providerLabel = document.querySelector('#provider-label');
const statusLabel = document.querySelector('#status-label');
const clearButton = document.querySelector('#clear-button');

let selectedTone = 'professional';
let history = [];

const toneIcons = { happy: '*', sad: '~', angry: '!', professional: '+', sarcastic: '/' };

async function loadTones() {
  const response = await fetch('/api/personalities');
  const data = await response.json();
  toneList.innerHTML = data.personalities.map((tone) => `
    <button class="tone ${tone.id === selectedTone ? 'active' : ''} ${tone.id}" data-tone="${tone.id}" type="button">
      <span class="tone-icon">${toneIcons[tone.id]}</span>
      <span class="tone-copy"><strong>${tone.label}</strong><small>${tone.description}</small></span>
    </button>`).join('');
  toneList.querySelectorAll('.tone').forEach((button) => button.addEventListener('click', () => {
    selectedTone = button.dataset.tone;
    toneList.querySelectorAll('.tone').forEach((item) => item.classList.toggle('active', item === button));
  }));
}

function addMessage(role, content) {
  welcome?.remove();
  const message = document.createElement('div');
  message.className = `message ${role}`;
  message.innerHTML = `<div class="avatar">${role === 'user' ? 'You' : 'M'}</div><div class="bubble"></div>`;
  message.querySelector('.bubble').textContent = content;
  conversation.appendChild(message);
  conversation.scrollTop = conversation.scrollHeight;
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) return;
  input.value = '';
  input.style.height = 'auto';
  addMessage('user', message);
  const sendButton = form.querySelector('.send-button');
  sendButton.disabled = true;
  sendButton.querySelector('span').textContent = 'Thinking';
  try {
    const response = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message, personality: selectedTone, history }) });
    if (!response.ok) throw new Error('Request failed');
    const data = await response.json();
    addMessage('assistant', data.reply);
    history.push({ role: 'user', content: message }, { role: 'assistant', content: data.reply });
    providerLabel.textContent = data.provider;
  } catch (error) {
    addMessage('assistant', 'I could not reach the conversation service. Please check that the API is running.');
    statusLabel.textContent = 'Service unavailable';
  } finally {
    sendButton.disabled = false;
    sendButton.querySelector('span').textContent = 'Send';
  }
});

input.addEventListener('input', () => { input.style.height = 'auto'; input.style.height = `${Math.min(input.scrollHeight, 120)}px`; });
input.addEventListener('keydown', (event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); form.requestSubmit(); } });
clearButton.addEventListener('click', () => { history = []; conversation.innerHTML = '<div class="welcome" id="welcome"><div class="welcome-orb">M</div><h3>A little room to think.</h3><p>Pick a personality below and start anywhere. There is no perfect way to begin.</p></div>'; providerLabel.textContent = 'Local demo mode'; });

loadTones().catch(() => { statusLabel.textContent = 'Service unavailable'; });
