document.addEventListener('DOMContentLoaded', () => {
  const widget = document.getElementById('supportWidget');
  if (!widget) return;

  const launcher = document.getElementById('supportLauncher');
  const closeButton = document.getElementById('supportClose');
  const clearButton = document.getElementById('supportClear');
  const panel = document.getElementById('supportPanel');
  const messages = document.getElementById('supportMessages');
  const form = document.getElementById('supportForm');
  const input = document.getElementById('supportInput');
  const unread = document.getElementById('supportUnread');
  const suggestions = document.getElementById('supportSuggestions');
  const storageKey = 'bookstore-support-chat';

  const getCookie = name => {
    const cookie = document.cookie.split('; ').find(item => item.startsWith(`${name}=`));
    return cookie ? decodeURIComponent(cookie.split('=').slice(1).join('=')) : '';
  };

  const escapeHtml = value => value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');

  const renderMarkdown = text => {
    let html = escapeHtml(text);
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, label, url) => {
      if (!url.startsWith('/') && !url.startsWith('mailto:')) return label;
      return `<a href="${url}">${label}</a>`;
    });
    const lines = html.split('\n');
    const output = [];
    let inList = false;
    lines.forEach(line => {
      if (line.startsWith('- ')) {
        if (!inList) {
          output.push('<ul>');
          inList = true;
        }
        output.push(`<li>${line.slice(2)}</li>`);
      } else {
        if (inList) {
          output.push('</ul>');
          inList = false;
        }
        if (line.trim()) output.push(`<p>${line}</p>`);
      }
    });
    if (inList) output.push('</ul>');
    return output.join('');
  };

  const defaultHistory = [{
    role: 'bot',
    text: 'Hi, I am your BookStore AI support assistant. I can help with book recommendations, order tracking, subscriptions, discounts, cancellations, and store support.',
  }];

  const readHistory = () => {
    try {
      const stored = JSON.parse(localStorage.getItem(storageKey) || '[]');
      return Array.isArray(stored) && stored.length ? stored : defaultHistory;
    } catch (error) {
      return defaultHistory;
    }
  };

  const writeHistory = history => {
    localStorage.setItem(storageKey, JSON.stringify(history.slice(-24)));
  };

  const scrollToEnd = () => {
    messages.scrollTop = messages.scrollHeight;
  };

  const setSuggestions = items => {
    if (!suggestions || !Array.isArray(items) || !items.length) return;

    suggestions.innerHTML = '';
    items.slice(0, 6).forEach(label => {
      const button = document.createElement('button');
      button.type = 'button';
      button.dataset.supportPrompt = label;
      button.textContent = label;
      button.title = label;
      suggestions.appendChild(button);
    });
  };

  const addMessage = (role, text, persist = true, source = '') => {
    const bubble = document.createElement('div');
    bubble.className = `support-message ${role}`;
    bubble.innerHTML = role === 'bot' ? renderMarkdown(text) : escapeHtml(text);
    if (role === 'bot' && source) {
      const badge = document.createElement('span');
      badge.className = 'support-source';
      badge.textContent = source === 'gemini' ? 'AI answer' : 'Store answer';
      bubble.appendChild(badge);
    }
    messages.appendChild(bubble);
    scrollToEnd();

    if (persist) {
      const history = readHistory();
      history.push({ role, text });
      writeHistory(history);
    }
  };

  const renderHistory = () => {
    messages.innerHTML = '';
    readHistory().forEach(item => addMessage(item.role, item.text, false));
  };

  const setOpen = isOpen => {
    widget.classList.toggle('is-open', isOpen);
    panel.setAttribute('aria-hidden', String(!isOpen));
    if (unread) unread.hidden = isOpen;
    if (isOpen) {
      renderHistory();
      window.setTimeout(() => input.focus(), 80);
    }
  };

  const showTyping = () => {
    const typing = document.createElement('div');
    typing.className = 'support-typing';
    typing.dataset.supportTyping = 'true';
    typing.innerHTML = '<span></span><span></span><span></span>';
    messages.appendChild(typing);
    scrollToEnd();
  };

  const hideTyping = () => {
    messages.querySelector('[data-support-typing="true"]')?.remove();
  };

  const sendMessage = async text => {
    const message = text.trim();
    if (!message) return;

    addMessage('user', message);
    input.value = '';
    showTyping();

    try {
      const response = await fetch(widget.dataset.chatUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
          'X-Requested-With': 'XMLHttpRequest',
        },
        credentials: 'same-origin',
        body: JSON.stringify({ message }),
      });
      const data = await response.json();
      hideTyping();
      addMessage('bot', data.reply || data.error || 'I could not answer that just now. Please try again.', true, data.source);
      setSuggestions(data.suggestions);
    } catch (error) {
      hideTyping();
      addMessage('bot', 'I could not reach support right now. Please try again in a moment.');
    }
  };

  launcher?.addEventListener('click', () => setOpen(true));
  closeButton?.addEventListener('click', () => setOpen(false));
  clearButton?.addEventListener('click', () => {
    localStorage.removeItem(storageKey);
    renderHistory();
    input.focus();
  });

  form?.addEventListener('submit', event => {
    event.preventDefault();
    sendMessage(input.value);
  });

  suggestions?.addEventListener('click', event => {
    const button = event.target.closest('[data-support-prompt]');
    if (!button) return;
    sendMessage(button.dataset.supportPrompt);
  });

  renderHistory();
});
