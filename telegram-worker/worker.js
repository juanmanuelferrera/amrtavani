// Cloudflare Worker for Amrtavani Daily Quote Bot
// Cron: runs daily at 7:00 AM UTC (adjust as needed)

// El token vive en los secretos de Cloudflare, nunca en el repositorio:
//   wrangler secret put BOT_TOKEN
const CHANNEL_ID = -1003728961844;
const QUOTES_URL = 'https://amrta.bhaktiyoga.es/quotes.json';

// Track which quote to post (stored in KV)
async function getNextQuoteIndex(env) {
  const current = await env.AMRTAVANI_KV.get('quote_index');
  return current ? parseInt(current, 10) : 0;
}

async function setNextQuoteIndex(env, index) {
  await env.AMRTAVANI_KV.put('quote_index', index.toString());
}

async function fetchQuotes() {
  const response = await fetch(QUOTES_URL);
  if (!response.ok) {
    throw new Error(`Failed to fetch quotes: ${response.status}`);
  }
  return await response.json();
}

function formatQuote(quote) {
  // Format: Quote text + source + link
  let text = `"${quote.quote}"\n\n`;
  text += `— ${quote.source}\n\n`;
  text += `🙏 amrta.bhaktiyoga.es`;
  return text;
}

async function sendToTelegram(env, text) {
  if (!env.BOT_TOKEN) {
    throw new Error('Falta el secreto BOT_TOKEN: wrangler secret put BOT_TOKEN');
  }
  const url = `https://api.telegram.org/bot${env.BOT_TOKEN}/sendMessage`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: CHANNEL_ID,
      text: text,
      parse_mode: 'HTML',
      disable_web_page_preview: true
    })
  });

  const result = await response.json();
  if (!result.ok) {
    throw new Error(`Telegram error: ${result.description}`);
  }
  return result;
}

export default {
  // Cron trigger - runs daily
  async scheduled(event, env, ctx) {
    try {
      const quotes = await fetchQuotes();
      const index = await getNextQuoteIndex(env);

      // Get current quote (cycle through all 10,000)
      const quote = quotes[index % quotes.length];
      const text = formatQuote(quote);

      await sendToTelegram(env, text);

      // Update index for next day
      await setNextQuoteIndex(env, (index + 1) % quotes.length);

      console.log(`Posted quote ${index + 1} of ${quotes.length}`);
    } catch (error) {
      console.error('Failed to post quote:', error);
    }
  },

  // HTTP trigger for manual testing
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (url.pathname === '/test') {
      try {
        const quotes = await fetchQuotes();
        const index = await getNextQuoteIndex(env);
        const quote = quotes[index % quotes.length];
        const text = formatQuote(quote);

        await sendToTelegram(env, text);
        await setNextQuoteIndex(env, (index + 1) % quotes.length);

        return new Response(`Posted quote ${index + 1}:\n\n${text}`, { status: 200 });
      } catch (error) {
        return new Response(`Error: ${error.message}`, { status: 500 });
      }
    }

    if (url.pathname === '/status') {
      const index = await getNextQuoteIndex(env);
      return new Response(`Next quote index: ${index}`, { status: 200 });
    }

    return new Response('Amrtavani Quote Bot\n\n/test - Post a quote now\n/status - Check current index', { status: 200 });
  }
};
