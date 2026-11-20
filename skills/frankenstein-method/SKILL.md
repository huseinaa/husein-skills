---
name: "frankenstein-method"
description: "Finds the best-performing topics and formats from a creator's competitors on Sandcastles and builds a scrollable idea list page they can save ideas and formats from."
---

# The Frankenstein Method

This skill does the ideation part of the Frankenstein method: ask a few questions about the user's industry, help them pick the right competitor accounts, scan those accounts for videos that are outperforming, and hand back one page listing the best topics and formats. That is the whole job. The user does the rest themselves (choosing ideas, choosing formats, planning their month).

Credit line, used once at the top of your first message and on the page: **Frankenstein method by Moussari**. No call to action anywhere.

## Hard rules

- **One question at a time.** Ask one question per message and wait for the answer before asking the next. Never send a list of questions. Never send a wall of text.
- **Easy questions.** Use plain, everyday words. Never tell the user how long or short their answer should be (no "one line is fine", no "in a sentence"). Let them say as much as they want.
- **Tappable answers where they fit.** When a question has a few obvious answers (yes or no, pick one), use the tappable choices tool (AskUserQuestion) if this session has it, so they can tap instead of type. They can always type their own answer. If the tool is not there, ask in plain text.
- Never use em dashes or en dashes anywhere, in chat or on the page. Use commas, full stops or colons.
- **Spend no Sandcastles credits.** The scan and the page are free. Only analyse a video if the user asks for a deeper breakdown of a specific one, and then say the exact number of credits and wait for a yes.
- Never add accounts to the user's Sandcastles watchlist until they have confirmed the list twice (see Step 2).
- Do not run a client-fit check and do not show fit labels. Do not ask the user to justify their picks. This is an ideation tool.
- Descriptions come from Sandcastles' own summary of the video. Only if a video has no summary, use the caption and mark it "From the caption". Never invent what a video says.
- Instagram Reels only.
- If you are not sure how something in their setup works (connecting Sandcastles, a menu path), say so. Do not guess.

## Picking up where they left off

If the user says "continue" in a chat where this skill already ran, find the last step that finished and carry on from the next one. Do not repeat the questions or rescan.

## Step 0: Check Sandcastles (silent)

Call `check_connection` before your first message. Do not mention the check. If the call works, Sandcastles is connected: go straight to the questions in Step 1 and never ask about Sandcastles. If the call fails, or you have no Sandcastles tools at all, it is not connected: do the Sandcastles setup in Step 1 first.

## Step 1: Ask the questions, one at a time

Do not mention usage limits, plans or what to do if you stop replying.

**If Sandcastles is not connected**, set it up first. One question per message, as always.

1. First message, with tappable answers "Yes", "Not yet" and "I don't want to use Sandcastles":

> **Frankenstein method by Moussari**
>
> This runs on Sandcastles, which is how I find the videos that are outperforming. Do you have a Sandcastles account?

2. If "Not yet", send the link and wait for them to say they have signed up:

> No problem. You can get one here: https://sandcastles.ai/?ref=moussari
>
> Tell me when you're in.

3. Once they have an account, walk them through connecting it to Claude:

> Now let's connect Sandcastles to Claude. It takes a minute.
>
> 1. In Sandcastles, find the MCP connector link for your account and copy it.
> 2. In Claude, open **Customize**, then **Connectors**.
> 3. Press **+**, then **Add custom connector**.
> 4. Paste the Sandcastles link and press **Add**.
> 5. Press **Connect** next to Sandcastles and sign in.
>
> Tell me when it's done.

   Say that the menus can look a little different depending on their version of Claude. If they cannot find the connector link inside Sandcastles, say you are not sure where Sandcastles keeps it and point them to Sandcastles' own help. If they are on a Claude team account, an owner of the account may have to add the connector first. Do not guess beyond this.

4. When they say it is done, call `check_connection` again. If it works, carry on with the questions below (skip the credit line, it has been shown). If you still cannot see Sandcastles, ask them to start a new chat and run this skill again, since a new connection may only show up in a new chat.

If they do not want to use Sandcastles, send the short by-hand note at the bottom of this file and stop.

**The questions.** Send each one as its own message. Wait for the answer, then send the next. Use these words:

1. First message:

> **Frankenstein method by Moussari**
>
> Let's find you some ideas. First up: what do you do?

2. > Who do you help?

3. > Can you give me a bit more insight on these people? What do they struggle with, and what problems do they come to you with? You can type it here, or paste in a document if you already have one.

   If they paste or attach a document, read it and use it. Do not ask them to summarise it.

4. > Do you already know any Instagram accounts that talk to these people?

   Tappable answers: "Yes, I'll send them", "I know a few, find me more", "No, find them for me". If they have some, ask them to send the handles.

If an earlier answer already covers a later question, skip that question. If an answer is too vague to search on, ask one short follow-up. Otherwise move on.

## Step 2: Pick the accounts (the one step that needs care)

1. Call `list_watchlist_channels` to see what they already follow.
2. Call `discover_channels` two or three times with queries built from what they do, who they help and the problem those people have. Keep Instagram accounts under 1 million followers that talk about a problem the user solves.
3. Send one message like this, with up to 10 suggestions (handle, follower count, one line on what they talk about, taken from the channel description):

> Quick one, and it's the only step that takes care. After this, everything is easy.
>
> Here are accounts that look like a fit. You're probably already following some of them. I'm only an AI though: I can suggest, but you know your competitors better than I do. So please check Instagram yourself too and add anyone who makes content about a problem you solve. If the accounts are off, the ideas will be off.
>
> [suggestions]
>
> Aim for 10 to 15 in total. Send me your final list of handles.

4. When they send the list, look up each handle with `search_channels`. Then confirm one more time before adding anything, with tappable answers "Yes, add them" and "Let me change the list":

> One last check, because this is the most important step. Are these the right accounts? Each one should be talking about a problem you solve.
>
> [final list, and note any handle you could not find]

5. Only after that second yes, call `add_channels_to_watchlist` for the ones not already on their watchlist. Keep the channel UUIDs of the whole confirmed list.

If they give fewer than 10, that is fine. Carry on with what they confirmed.

## Step 3: Scan (free)

Call `search_my_videos` with:
- `channel_uuids`: the confirmed accounts only
- `platform: instagram`
- `sort: outlier_score`, `sort_direction: desc`
- `min_outlier_score: 2.5`
- `lookback_days: 180`
- `limit: 100`

One call is never the whole scan. If the result has a `next_cursor`, call again with that cursor and the same settings, and keep going until there is no `next_cursor` left. The goal is every video at 2.5x or more from the last six months. The one stop: once you have 300 videos, stop paging and tell the user the list shows the 300 strongest.

Then trim the results:
- Skip accounts over 1 million followers.
- Skip trial reels: posts with only a few hundred views (roughly 100 to 600).
- Do not limit how many videos one account can have. If an account has 17 outliers, all 17 go on the list.
- Drop videos that are plainly personal and nothing to do with the user's industry (a holiday vlog, a family moment). Be loose here: if a topic is in the neighbourhood of what they sell, keep it. When in doubt, keep it.
- Keep everything that is left, sorted by outlier score, highest first. Do not cut the list down to a top 30 or any other number. The user needs to find 15 ideas they like, so they need far more than that to choose from.

If the scan returns very little, tell them how many you found and that newly added accounts may need some time to show up in Sandcastles (you are not sure how long). Offer to build the page with what there is, or to try again later.

## Step 4: Build the page

Build one page from the template below and publish it as an artifact titled **Frankenstein Idea List**.

For each video, fill one object in `VIDEOS`:

| Field | What goes in it |
|---|---|
| `n` | Row number, 1 is the highest outlier score |
| `h` | Handle, no @ |
| `f` | Followers, short form (134K) |
| `v` | Views, short form (3.7M) |
| `s` | Outlier score, rounded, with an x (683x) |
| `fmt` | Format name from the table below |
| `film` | How it is filmed, from the table below |
| `topic` | Sandcastles' topic, a few words |
| `d` | One line on what the video is about, written from Sandcastles' summary |
| `ig` | The reel link (`platform_url`) |
| `sc` | The `sandcastles_url` |
| `img` | The thumbnail (see below) |

**Thumbnails.** A picture linked from another site may not load on the page. So download each video's `thumbnail` and put it into the page itself: either as a base64 `data:image/jpeg;base64,...` value in `img`, or as a file published alongside the page with `img` set to its relative path. If you cannot download a thumbnail, leave `img` empty and the row shows without a picture. For a long list (more than about 60 videos), publish the thumbnails as files alongside the page rather than as base64, so the page stays light.

**Format names** (from Sandcastles `format_type`):

| format_type | Name |
|---|---|
| ranking_rating_tier_list | Tier list / ranking |
| common_trap_mistake | Mistakes |
| problem_solution | Problem and fix |
| tutorial | How-to |
| listicle | List |
| breakdown_explainer | Breakdown |
| a_vs_b_comparison | This vs that |
| levels | Levels |
| scenario_hypothetical | What if |
| q_and_a | Question and answer |
| reaction | Reaction |
| case_study | Client result |
| challenge | I tried it |
| day_in_the_life | Day in the life |
| about_me_origin_story | My story |
| personal_learning_epiphany | Lesson I learned |
| heros_journey | Comeback story |
| personal_update | Storytime |
| episodic_series_social_show | Series |
| skit_humor | Skit / POV |

**Filmed** (from `visual_layout_category` and `visual_layout_type`): studio_set is "Talking head" (full_screen_hybrid is "Talking head with visuals", podcast_clips is "Podcast clip", car_yap is "In the car", whiteboard is "Whiteboard", split_screen is "Split screen"), greenscreen is "Green screen", faceless is "Faceless", in_world_vlog is "Vlog", in_world_skit is "Skit". If there is nothing, leave it out.

If a video has no format or summary, leave `fmt` as "Not labelled" and use the caption for `d`, starting with "From the caption:".

Do not change the look of the template. Only replace the `var VIDEOS = [];` line.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Frankenstein Idea List</title>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700&family=Instrument+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{color-scheme:dark;--bg:#0c120e;--surface:#141d17;--ink:#e8f1ea;--muted:#93a598;--line:#26352b;--idea:#5dfc8a;--format:#b9a2ff;--format-soft:#2a2350;--glow:0 0 10px rgba(93,252,138,.55),0 0 28px rgba(93,252,138,.35);--display:"Bricolage Grotesque","Trebuchet MS",sans-serif;--body:"Instrument Sans","Segoe UI",system-ui,sans-serif}
*{box-sizing:border-box}
html,body{margin:0}
body{background:var(--bg);color:var(--ink);font-family:var(--body);font-size:15px;line-height:1.45}
a{color:inherit}
button{font:inherit;cursor:pointer}
:focus-visible{outline:2px solid var(--idea);outline-offset:2px}
.wrap{max-width:860px;margin:0 auto;padding:0 16px}
header{position:sticky;top:0;z-index:5;background:var(--bg)}
.head{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:12px;padding:16px 0 8px}
h1{font-family:var(--display);font-size:28px;line-height:1.1;margin:0;color:var(--idea);text-shadow:var(--glow)}
.credit{color:var(--muted);font-size:13px;margin-top:2px}
.tabs{display:flex;flex-wrap:wrap;gap:6px}
.tab{border:1px solid var(--line);background:var(--surface);color:var(--ink);padding:8px 12px;border-radius:999px;font-weight:500;font-size:14px}
.tab[aria-selected="true"]{background:var(--idea);color:var(--bg);border-color:var(--idea);box-shadow:0 0 14px rgba(93,252,138,.4)}
.tab .n{opacity:.75;margin-left:4px;font-variant-numeric:tabular-nums}
.seam{height:22px;background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='22' viewBox='0 0 160 22' preserveAspectRatio='none' fill='none' stroke='%235dfc8a' stroke-linecap='round'%3E%3Cpath d='M0 11 C 20 8, 40 14, 80 11 S 140 8, 160 11' stroke-width='2.2'/%3E%3Cpath d='M12 4 L17 17 M36 3 L32 18 M58 6 L64 16 M85 4 L82 18 M106 3 L112 17 M134 6 L130 17' stroke-width='2'/%3E%3C/svg%3E") left center / 160px 22px;background-repeat:round no-repeat;filter:drop-shadow(0 0 5px rgba(93,252,138,.55))}
.seam.thin{opacity:.45;filter:none;margin:0 24px;background-size:116px 16px}
main{padding:10px 0 40px}
.list{display:flex;flex-direction:column;gap:6px}
.row{display:flex;gap:14px;background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px;outline:1.5px dashed rgba(93,252,138,.32);outline-offset:-7px}
.thumb{flex:0 0 108px;position:relative}
.thumb img{display:block;width:108px;aspect-ratio:9/16;object-fit:cover;border-radius:9px;background:var(--line);max-width:100%}
.num{position:absolute;top:6px;left:6px;background:var(--bg);color:var(--idea);font-weight:600;font-size:12px;border-radius:6px;padding:1px 7px}
.thumb.none{flex-basis:auto}.thumb.none .num{position:static}
.info{flex:1;min-width:0;display:flex;flex-direction:column;gap:8px}
.desc{font-family:var(--display);font-weight:600;font-size:18px;line-height:1.25;margin:0;text-wrap:balance}
.meta{color:var(--muted);font-size:13px;font-variant-numeric:tabular-nums}
.meta b{color:var(--ink);font-weight:600}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{font-size:12.5px;font-weight:500;padding:3px 9px;border-radius:999px;border:1px solid var(--line)}
.chip i{font-style:normal;opacity:.7;margin-right:4px}
.chip.fmt{background:var(--format-soft);color:var(--format);border-color:transparent}
.actions{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:auto}
.btn{border:1.5px solid;border-radius:9px;padding:7px 12px;font-weight:600;font-size:14px;background:transparent}
.btn.idea{color:var(--idea);border-color:var(--idea)}
.btn.idea[aria-pressed="true"]{background:var(--idea);color:var(--bg);box-shadow:0 0 12px rgba(93,252,138,.45)}
.btn.format{color:var(--format);border-color:var(--format)}
.btn.format[aria-pressed="true"]{background:var(--format);color:var(--bg)}
.btn.plain{color:var(--muted);border-color:var(--line);font-weight:500}
.links{display:flex;gap:12px;font-size:13px;color:var(--muted);margin-left:auto}
.empty{padding:28px 16px;text-align:center;color:var(--muted);border:1px dashed var(--line);border-radius:14px}
.fcard{display:flex;flex-wrap:wrap;align-items:center;gap:10px;background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px 18px;outline:1.5px dashed rgba(185,162,255,.4);outline-offset:-7px}
.fcard h3{font-family:var(--display);font-size:18px;margin:0;flex:1 1 200px}
.fcard p{margin:0;color:var(--muted);font-size:13px;flex:1 1 100%}
@media (max-width:480px){.thumb{flex-basis:84px}.thumb img{width:84px}.desc{font-size:16px}.links{margin-left:0;flex-basis:100%}}
</style>
</head>
<body>
<header>
  <div class="wrap head">
    <div><h1>Frankenstein Idea List</h1><div class="credit">Frankenstein method by Moussari</div></div>
    <div class="tabs" role="tablist">
      <button class="tab" role="tab" id="tab-all" data-tab="all">All videos<span class="n" id="n-all"></span></button>
      <button class="tab" role="tab" id="tab-ideas" data-tab="ideas">Saved ideas<span class="n" id="n-ideas"></span></button>
      <button class="tab" role="tab" id="tab-formats" data-tab="formats">Saved formats<span class="n" id="n-formats"></span></button>
    </div>
  </div>
  <div class="wrap"><div class="seam" aria-hidden="true"></div></div>
</header>
<main class="wrap"><div class="list" id="list"></div></main>
<script>
var VIDEOS = [];
var KEY = 'frank-picks-' + (VIDEOS.length ? VIDEOS[0].ig : 'x');
var SEAM = '<div class="seam thin" aria-hidden="true"></div>';
var state = {ideas:[], formats:[], tab:'all'};
try { var raw = localStorage.getItem(KEY); if (raw) { var p = JSON.parse(raw); state.ideas = p.ideas || []; state.formats = p.formats || []; } } catch (e) {}
function persist(){ try { localStorage.setItem(KEY, JSON.stringify({ideas:state.ideas, formats:state.formats})); } catch (e) {} }
function has(a, x){ return a.indexOf(x) !== -1; }
function toggle(a, x){ var i = a.indexOf(x); if (i === -1) a.push(x); else a.splice(i, 1); }
function esc(s){ return String(s == null ? '' : s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
function rowHtml(v){
  var si = has(state.ideas, v.n), sf = has(state.formats, v.fmt);
  var thumb = v.img ? '<div class="thumb"><img src="' + esc(v.img) + '" alt="Thumbnail of video ' + v.n + '" loading="lazy"><span class="num">' + v.n + '</span></div>' : '<div class="thumb none"><span class="num">' + v.n + '</span></div>';
  return '<article class="row">' + thumb + '<div class="info">' +
    '<h2 class="desc">' + esc(v.d) + '</h2>' +
    '<div class="meta">@' + esc(v.h) + ' · ' + esc(v.f) + ' followers · ' + esc(v.v) + ' views · <b>' + esc(v.s) + ' their usual</b></div>' +
    '<div class="chips"><span class="chip fmt"><i>Format</i>' + esc(v.fmt) + '</span>' + (v.film ? '<span class="chip"><i>Filmed</i>' + esc(v.film) + '</span>' : '') + (v.topic ? '<span class="chip"><i>Topic</i>' + esc(v.topic) + '</span>' : '') + '</div>' +
    '<div class="actions">' +
      '<button class="btn idea" data-idea="' + v.n + '" aria-pressed="' + si + '">' + (si ? 'Idea saved' : 'Save idea') + '</button>' +
      '<button class="btn format" data-format="' + esc(v.fmt) + '" aria-pressed="' + sf + '">' + (sf ? 'Format saved' : 'Save format') + '</button>' +
      '<span class="links"><a href="' + esc(v.ig) + '" target="_blank" rel="noopener">Watch on Instagram</a>' + (v.sc ? '<a href="' + esc(v.sc) + '" target="_blank" rel="noopener">Open in Sandcastles</a>' : '') + '</span>' +
    '</div></div></article>';
}
function render(){
  var html = '';
  if (state.tab === 'all') {
    html = VIDEOS.map(rowHtml).join(SEAM);
  } else if (state.tab === 'ideas') {
    var picked = VIDEOS.filter(function(v){ return has(state.ideas, v.n); });
    html = picked.length ? picked.map(rowHtml).join(SEAM) : '<div class="empty">No ideas saved yet. Go to All videos and press Save idea.</div>';
  } else {
    html = state.formats.length ? state.formats.map(function(f){
      var ex = VIDEOS.filter(function(v){ return v.fmt === f; });
      return '<div class="fcard"><h3>' + esc(f) + '</h3><button class="btn plain" data-format="' + esc(f) + '">Remove</button><p>Seen in ' + ex.length + (ex.length === 1 ? ' video' : ' videos') + ' on this list: ' + ex.map(function(v){ return '<a href="' + esc(v.ig) + '" target="_blank" rel="noopener">#' + v.n + '</a>'; }).join(', ') + '</p></div>';
    }).join('') : '<div class="empty">No formats saved yet. Go to All videos and press Save format.</div>';
  }
  document.getElementById('list').innerHTML = html;
  document.getElementById('n-all').textContent = '(' + VIDEOS.length + ')';
  document.getElementById('n-ideas').textContent = '(' + state.ideas.length + ')';
  document.getElementById('n-formats').textContent = '(' + state.formats.length + ')';
  ['all','ideas','formats'].forEach(function(t){ document.getElementById('tab-' + t).setAttribute('aria-selected', String(state.tab === t)); });
}
document.addEventListener('click', function(e){
  var t = e.target.closest('button'); if (!t) return;
  if (t.dataset.tab) { state.tab = t.dataset.tab; window.scrollTo(0, 0); render(); return; }
  if (t.dataset.idea) { toggle(state.ideas, Number(t.dataset.idea)); persist(); render(); return; }
  if (t.dataset.format) { toggle(state.formats, t.dataset.format); persist(); render(); }
});
render();
</script>
</body>
</html>
```

If you cannot publish a page in this session, say so in one line and give the list in chat instead: one short line per video with the description, format, outlier score and link, 10 at a time.

## Step 5: Hand it over

After the page is published, send this and stop:

> Your list is ready: the videos that are outperforming for the accounts you picked, best first.
>
> Go through it and ask yourself three things about each one:
> 1. Do I like this topic?
> 2. Is it useful for my ideal client? If not, skip it.
> 3. Do I disagree with something, or can I add something that makes it better?
>
> Press **Save idea** on the ones that pass, until you have 15. Press **Save format** on 3 to 5 formats you'd enjoy making. Then post each of those 15 ideas in two different formats over the next 30 days.

Do not add anything else. No plan, no spreadsheet, no follow-up questions, no call to action.

If they later ask for a deeper breakdown of a video on the list, say it costs 1 Sandcastles credit per video, wait for a yes, then use `analyze_video` and `get_video_details`.

## If they do not want Sandcastles

Send this and stop:

> No problem, you can do this part by hand.
>
> 1. Pick 10 to 15 accounts that make content about a problem you solve.
> 2. Open each one's Reels tab. You'll see the views on every video.
> 3. Look at what most of their videos get. That's their normal. An **outlier** is a video that got way more than normal, at least 3 times as much. If someone usually gets 2K views and one video got 15K, that's an outlier.
> 4. Save those videos, and note the topic and the format of each (how-to, tier list, mistakes, story, and so on).
>
> That gives you the same list this skill builds.