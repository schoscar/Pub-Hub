# Pub Hub Ask

The free-text search box. You type a sentence about your night; this Worker asks a
model on Cloudflare's free allowance to turn it into Pub Hub's own filters, and the
page applies them to its own checked data.

Until the Worker is deployed and its address is set in `index.html`, the search box
still works using keyword matching in the page. The same matching takes over if the
Worker is slow, offline, or out of free allowance.

## What it costs

Nothing on Cloudflare's free plan. Workers AI gives 10,000 neurons a day; at roughly
65 neurons a search on Llama 3.3 70B that is about 150 searches a day. When the
allowance runs out, the free plan returns an error instead of a bill, and the page
falls back to keyword matching until midnight UTC.

## Deploy it (dashboard, no installs)

1. Sign in or sign up at https://dash.cloudflare.com. The free plan is enough.
2. Go to **Workers & Pages** and choose **Create application**. On the "Make something
   new" screen, pick **Start with Hello World!**. Name it `pub-hub-ask` and **Deploy**.
3. On the Worker's page choose **Edit code**, delete everything in the editor, paste in
   the whole of `worker/pub-hub-ask.js`, and **Deploy**.
4. Open the Worker's **Settings**, find **Bindings**, **Add** a **Workers AI** binding,
   and set the variable name to `AI`. Deploy again if asked.
5. Copy the Worker's address. It looks like `https://pub-hub-ask.<your-name>.workers.dev`.

Then set `ASK_URL` in `index.html` to that address, or send it over and it will be done
for you.

## Deploy it (command line, if you have Node.js)

    cd worker
    npx wrangler login
    npx wrangler deploy

`wrangler.toml` in this folder already declares the AI binding.

## Keeping it in step with the app

The Worker carries its own copy of the teams, features and cuisines the app can filter
on, so the model is never offered anything else. After those change in the app:

    python3 worker/build.py

then paste or deploy the file again.

## Who can call it

Only pages served from `https://schoscar.github.io` or a local copy on port 8766. That
stops other websites using up the daily allowance; it is not a security boundary, and
nothing secret sits behind it.
