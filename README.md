# Full A-to-Z: Free AI Instagram auto-post — test account

This is a **working starter**, not a ready-connected service. It has not been connected to your Instagram account or tested against live Meta/Gemini credentials. Use a **throwaway test Instagram account** first. It publishes a **single square JPEG** with gradient and AI quote per run, at **10 AM, 3 PM, 9 PM America/Toronto**. After setup, PC/phone can be OFF.

## The system

Google Gemini text API (free tier when eligible) → Python Pillow draws 1080×1080 original gradient JPG → GitHub Actions uploads to GitHub Pages public hosting → official Instagram API creates media → waits for processing → publishes.

NO Make.com, Canva subscription or paid image model needed. **Gemini Premium is different from Gemini API billing.** Free tier can be limited and is not a guaranteed ongoing $0 service. All generated images on Pages will be public.

## A. Accounts you need

- Your test Instagram **public professional Creator or Business** profile. **Personal cannot publish via official API.** Make a brand new test account or convert an existing one in Instagram Settings → Account type and tools → Switch to professional account (labels vary).
- Free GitHub account: https://github.com/signup
- A Google account for Gemini API: https://aistudio.google.com/apikey ; select free-tier project (do NOT activate paid billing unless you want to).
- Facebook/Meta login for Meta for Developers: https://developers.facebook.com/apps/

## B. Set up Gemini API

1. Open https://aistudio.google.com/apikey and sign in.
2. Make an API key for a **free-tier** project. Copy the key privately.
3. In AI Studio confirm your chosen model is eligible for your project. Default model here is `gemini-2.5-flash-lite`, which may be changed later in the code or set as a GitHub environment variable. A model can be unavailable to new accounts — if so, use an available free text model from https://ai.google.dev/gemini-api/docs/pricing .
4. Do NOT paste the key into GitHub code or a chat message.

## C. Make GitHub repository and upload everything

1. Sign in to https://github.com/ . Select **+ → New repository**.
2. Name it `instagram-ai-test` (any repository name is fine), **Public**, add README optional, Create repository.
3. Extract this ZIP on PC. Open the unzipped folder. Upload all **files and folders inside** it to repository root using **Add file → Upload files**. GitHub's upload interface may skip hidden `.github` folders. If `.github/workflows/autopost.yml` did not upload, add it separately: **Add file → Create new file** and type `.github/workflows/autopost.yml` as the path, then paste the file's text and commit.
4. Check the **Code** tab shows `generate.py`, `publish.py`, `requirements.txt`, `README.md` and `.github/workflows/autopost.yml` in their correct locations. Do NOT upload `__pycache__` or API keys.
5. Go to **Settings → Pages → Build and deployment → Source: GitHub Actions**. DO NOT use 'Deploy from a branch' with this script.
6. Under **Settings → Actions → General**, ensure Actions are allowed. Default GITHUB_TOKEN must be able to deploy Pages; workflow already requests Pages write access.

## D. Meta for Developers: Instagram Login (MOST IMPORTANT)

1. Open https://developers.facebook.com/apps/ . Register/verify your Meta developer account if prompted.
2. Click **Create App**. Choose a use case involving Instagram API/content management. If asked for app type, select **Business**. Give app a name (`IG AI Test`) and contact email. Interface wording varies by Meta dashboard.
3. Add the **Instagram** product/use case. Find **API setup with Instagram Login** (sometimes called Instagram business login). **Do not choose 'Instagram API with Facebook Login'** for this package, because that is a different token + endpoint workflow and often requires a linked Facebook Page.
4. If account authorization fails in development mode, go to **App roles → Roles → Instagram Testers / Add people**, add the **test Instagram handle**, then go to that Instagram account's **Settings → Website permissions → Apps and websites → Tester invites** and accept. Refresh Meta dashboard; the account should be active. You may need to add your Meta developer Facebook user to the app too.
5. Back in **Instagram → API setup with Instagram login → Generate access tokens → Add account** (wording changes), sign into **the test Instagram account** and click **Allow** for the necessary permissions. Required scopes for images: `instagram_business_basic`, `instagram_business_content_publish`.
6. Generate an **Instagram User Access Token** for that account. Keep it SECRET. Depending on flow it can initially be short-lived; see next section. **Do not use your Instagram password as an API token.**
7. Get the **numeric Instagram Professional Account ID** shown in dashboard, or call the profile endpoint with the token. In browser you can open `https://graph.instagram.com/me?fields=id,username&access_token=YOUR_TOKEN` privately on your OWN PC, but this puts your token into browser URL history. Safer: use a local command or API client with token in header. Numeric `id`, not the `@username`, goes in GitHub Secret `INSTAGRAM_USER_ID`.
8. Meta app in **development mode** is generally enough for testing with Instagram accounts assigned appropriate roles. For other public accounts, production app review / permissions / business verification may be required. Do not change to Live prematurely.

### IMPORTANT: Long-lived token

Some developer tools generate a **short-lived token** (around 1 hour). A durable schedule needs a **long-lived Instagram User Access Token**, typically valid around 60 days, and periodic renewal. For the Instagram Login flow, token exchange is documented at `https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/business-login` and https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api . Long-lived exchange commonly uses `GET https://graph.instagram.com/access_token?grant_type=ig_exchange_token&client_secret=YOUR_INSTAGRAM_APP_SECRET&access_token=SHORT_LIVED_TOKEN` ; **do not paste tokens or secrets into public URLs/chats/screenshots**. If Meta's dashboard already provides a long-lived token, use it. The starter DOES NOT implement auto-refresh. Replace secret when token expires or implement secure renewal separately. Your Instagram App Secret is a sensitive secret as well.

## E. Add GitHub Secrets

Repository → **Settings → Secrets and variables → Actions → New repository secret**. Add three separately:

- `GEMINI_API_KEY` = Google Gemini API key
- `INSTAGRAM_USER_ID` = test account NUMERIC professional ID
- `INSTAGRAM_ACCESS_TOKEN` = long-lived **Instagram User** token for the SAME account

No quotes. Do NOT use repository Variables for these secret values. No need to add Facebook password.

## F. Run the first post (REAL PUBLIC POST)

1. Check the test account is the one that the token authorizes, and it is public professional account.
2. GitHub repo → **Actions** → **Wistful Forever AI autopost** → **Run workflow** → Run workflow.
3. Click the new workflow run. Watch jobs: `Install Python dependencies` → `Generate quote and design` → `Configure GitHub Pages` → `Deploy Pages site` → `Publish image to Instagram`.
4. A green workflow means the API responded with a published media ID. Check the Instagram test account for the post. Your first run **posts for real**; there is no approval step.
5. Check **Settings → Pages** for published site address. The rendered image URL should look like `https://YOURGITHUBNAME.github.io/instagram-ai-test/post-2026....jpg` . You need not manually copy this URL; code uses it automatically.

## G. Let it run automatically

Workflow: `.github/workflows/autopost.yml` : `0 10,15,21 * * *` with `timezone: 'America/Toronto'` . That means 10:00 AM, 3:00 PM and 9:00 PM Toronto local time including daylight savings. Scheduled GitHub Actions can be delayed; no exact-to-the-minute guarantee. Phone/PC off is fine.

**To change frequency:** for one daily post use `0 15 * * *`. To change times, edit hours `10,15,21`. To pause automatic posting, remove the `schedule` block and commit, or disable the workflow in Actions. To publish manually, leave `workflow_dispatch` and Run workflow.

## H. How to change target Instagram account later

1. Convert new profile to public professional (Creator/Business).
2. Add/authorize new account in Meta app and roles (if needed).
3. Generate new valid Instagram User token for NEW profile; get its numeric ID.
4. Replace BOTH GitHub Secrets `INSTAGRAM_USER_ID` and `INSTAGRAM_ACCESS_TOKEN`.
5. Manually run on new test account once. Previous Instagram media stay on prior account.

Simply renaming the SAME Instagram account usually leaves the numeric ID unchanged.

## I. Limitations, safety, and zero-cost caveats

- This posts **images only**, not Stories/Reels or DMs, and DOES NOT auto-reply to comments.
- Gemini generates the line+caption; Pillow renders the background/text. It is NOT a paid AI image model.
- Quotes may repeat occasionally. No permanent history/deduplication.
- **The code requires publicly reachable JPEGs**; GitHub Pages provides temporary hosted images. Each deployment replaces previous hosted images, but Instagram posts already published remain.
- Github Actions schedules can fail/delay and public repository schedules can be automatically disabled after **60 days with no repository activity**. Check your Actions page sometimes.
- **Meta access tokens expire**; this package does not auto-refresh. This is not literally 365 days of no human intervention.
- Free Gemini API usage and GitHub free tiers may change. Never enable paid billing if you want a hard $0 limit.
- Public GitHub code/images are visible; **never commit tokens**.
- The Instagram API may require completing Meta developer verification, permissions or app review depending on app configuration. No guarantee you'll get publish access immediately.

## J. Troubleshooting

| What you see | Probable cause / solution |
|---|---|
| Workflow not listed under Actions | `.github/workflows/autopost.yml` missing or wrong directory; check file on `main` branch |
| Gemini 400 / 404 model not found | Default model unavailable; set `GEMINI_MODEL` in workflow env to a currently free model for your account |
| Gemini 429 | Free rate/quota reached; try again later, reduce posting frequency |
| Instagram OAuth login fails | Add test IG user as app tester and ACCEPT invite; same account in Meta role and login |
| Instagram 401 / 190 | Token invalid/expired or wrong type; use correct Instagram User token and renew/replace it |
| Instagram 403 / permission | Missing `instagram_business_content_publish`, wrong app role, professional account, or app permission status |
| `Image not publicly available` | GitHub Pages disabled, URL not deployed, or site not public |
| Instagram media ERROR | Image hosting invalid/not public, media not accepted, or publishing restrictions |
| Manual run works; schedule does not | Workflow disabled/inactive, default branch problem, scheduling delay, or GitHub outage |
| No exact timestamp | Scheduled workflows can be delayed; time zone affects intended run local time |

Official reference links:
- Instagram API: https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api
- Instagram Login publishing: https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/content-publishing
- GitHub Actions scheduling: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- GitHub Pages workflow: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
- Gemini pricing/free tier: https://ai.google.dev/gemini-api/docs/pricing
