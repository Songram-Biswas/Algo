/**
 * AlgoHub Passive-Aggressive Streak Reminder Cron Job
 * Route: GET /api/cron/reminders or POST /api/cron/reminders
 *
 * Frequency: Hourly (0 * * * *) via Vercel Cron
 *
 * Flow:
 *   1. Fetches registered users and their stats/profiles from Supabase.
 *   2. Filters for users who:
 *      - Have an active streak (streak > 0)
 *      - Have NOT solved a problem today (in their local timezone)
 *      - Whose current local time is exactly between 21:00 (9:00 PM) and 22:00 (10:00 PM)
 *   3. Calls Gemini 2.5 Flash with an unhinged, passive-aggressive Duolingo-owl persona:
 *      - ALL CAPS
 *      - Hilarious broken grammar ('YOUR STREAK IS DIE IN 3 HOURS!', 'WHY YOU DO THIS TO POOR ARRAY?')
 *      - Heavy dramatic/crying/skull emojis (💀😭🦉🔥)
 *   4. Dispatches the email via Nodemailer (Gmail SMTP: GMAIL_USER, GMAIL_APP_PASSWORD).
 *
 * Query Options (for testing & preview):
 *   ?dry_run=true      (skips actual email dispatch; returns generated previews)
 *   ?mock=true         (uses simulated user dataset spanning multiple timezones)
 *   ?force_hour=21     (forces local hour check to 21 for manual testing)
 *   ?preview_all=true  (processes all active streak users regardless of current hour)
 *   ?secret=...        (matches CRON_SECRET if set)
 */

try {
  require('dotenv').config();
} catch (e) {}

const nodemailer = require('nodemailer');
const { GoogleGenAI } = require('@google/genai');
const { getProblemOfTheDay, datePartsInZone } = require('../_lib/problems');
const { listAllUsers, select } = require('../_lib/supabase-admin');

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function sendJson(res, status, payload) {
  res.statusCode = status;
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  res.end(JSON.stringify(payload, null, 2));
}

function resolveSiteUrl(req) {
  if (process.env.SITE_URL) return process.env.SITE_URL.replace(/\/+$/, '');
  if (process.env.VERCEL_PROJECT_PRODUCTION_URL) return `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`;
  if (process.env.VERCEL_URL) return `https://${process.env.VERCEL_URL}`;
  const host = req.headers['x-forwarded-host'] || req.headers.host;
  if (host) {
    const proto = req.headers['x-forwarded-proto'] || (host.startsWith('localhost') ? 'http' : 'https');
    return `${proto}://${host}`;
  }
  return 'https://algohub.vercel.app';
}

/**
 * Returns formatted YYYY-MM-DD in the target IANA timezone.
 */
function getLocalDateStr(date, timeZone) {
  try {
    return new Intl.DateTimeFormat('en-CA', {
      timeZone,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).format(date);
  } catch {
    return date.toISOString().split('T')[0];
  }
}

/**
 * Returns numeric hour (0-23) in the target IANA timezone.
 */
function getLocalHour(date, timeZone) {
  try {
    const formatter = new Intl.DateTimeFormat('en-US', {
      timeZone,
      hour: 'numeric',
      hourCycle: 'h23',
    });
    return parseInt(formatter.format(date), 10);
  } catch {
    return date.getUTCHours();
  }
}

/**
 * Checks if local time is currently between 21:00 (9:00 PM) and 22:00 (10:00 PM).
 */
function isBetween21And22(date, timeZone) {
  return getLocalHour(date, timeZone) === 21;
}

// ---------------------------------------------------------------------------
// Chaotic Gemini Prompt & Persona
// ---------------------------------------------------------------------------

const CHAOTIC_SYSTEM_INSTRUCTION = `You are an unhinged, passive-aggressive Duo-style owl mascot for AlgoHub whose only purpose is saving users' daily coding streaks.
You MUST write in this EXACT persona:
- COMPLETELY PASSIVE-AGGRESSIVE AND GUILT-TRIPPING. Make them feel like terrible human beings for abandoning their streak and their code.
- WRITE IN 100% ALL CAPS. EVERY SINGLE WORD AND SENTENCE MUST BE CAPITALIZED. NO LOWERCASE ALLOWED.
- USE INTENTIONAL, HILARIOUS GRAMMATICAL MISTAKES (e.g., 'WHY YOU DO THIS TO POOR ARRAY?', 'YOUR STREAK IS DIE IN 3 HOURS!', 'U HATE HASHMAPS?', 'LEETCODE IS CRYING IN CORNER', 'YOU FORGOT HOW TO REVERSE LINKED LIST OR WHAT??', 'I SAW YOU WATCHING NETFLIX INSTEAD OF GRINDING GRAPHS', 'WHO WILL FIX THE SEGFAULT IF NOT YOU???').
- HEAVY USE OF DRAMATIC, CRYING, AND SKULL EMOJIS (💀, 😭, 🦉, 🔥, 💔, 🥀, 🪦, 🔪).
- Keep it punchy, chaotic, and between 3-6 sentences. Mention their streak count, that their streak will be MURDERED in less than 3 hours at midnight, and demand they go solve the problem right now.`;

let genAiClient = null;
function getGeminiClient() {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) return null;
  if (!genAiClient) genAiClient = new GoogleGenAI({ apiKey });
  return genAiClient;
}

async function generateChaoticEmailBody({ name, streak, pod, solveUrl }) {
  const ai = getGeminiClient();
  const userName = (name || 'CODER').toUpperCase();

  if (ai) {
    try {
      const prompt = `USER NAME: ${userName}
CURRENT STREAK: ${streak} DAYS
TIME LEFT BEFORE MIDNIGHT: LESS THAN 3 HOURS
TODAY'S PROBLEM: #${pod.id} ${pod.title} (${pod.difficulty} ${pod.category})
SOLVE LINK: ${solveUrl}

GENERATE THE UNHINGED STREAK REMINDER EMAIL NOW.`;

      const resp = await ai.models.generateContent({
        model: 'gemini-2.5-flash',
        contents: [{ role: 'user', parts: [{ text: prompt }] }],
        config: {
          systemInstruction: CHAOTIC_SYSTEM_INSTRUCTION,
          temperature: 1.0,
          maxOutputTokens: 600,
        },
      });

      const reply = (resp.text || '').trim();
      if (reply) return reply.toUpperCase();
    } catch (err) {
      console.warn('[cron/reminders] Gemini API call failed, using chaotic fallback template:', err.message);
    }
  }

  // Chaotic template fallback in case Gemini key is missing or quota exceeded
  const fallbacks = [
    `${userName}, IS THIS HOW YOU REPAY THE ALGORITHMS THAT LOVED YOU?! 😭 YOUR BEAUTIFUL ${streak}-DAY STREAK IS DIE IN LESS THAN 3 HOURS! 💀 WHY YOU DO THIS TO POOR ARRAY?? U HATE HASHMAPS NOW?! 💔 THE TWO POINTERS ARE LITERALLY CRYING IN THE CORNER BECAUSE YOU ABANDON THEM! GO CLICK THE LINK AND SOLVE #${pod.id} ${pod.title.toUpperCase()} RIGHT NOW OR I WILL PERSONALLY DELETE YOUR LINKED LIST! 🦉🔥🥀`,
    `OH WOW LOOK WHO SUDDENLY FORGOT HOW TO CODE!! 💀 ${userName}, YOUR ${streak}-DAY STREAK IS ON LIFE SUPPORT AND CLOCK IS TICKING TO MIDNIGHT! 😭 WHO TOLD YOU NETFLIX MORE IMPORTANT THAN DYNAMIC PROGRAMMING?! YOUR TIME COMPLEXITY IS CRYING! 💔 GO SOLVE #${pod.id} ${pod.title.toUpperCase()} BEFORE YOUR STREAK BECOMES A GHOST! 🦉🪦🔥`,
    `I AM WATCHING YOU ${userName}. I AM IN YOUR TERMINAL. 🦉 YOUR ${streak}-DAY STREAK HAS ONLY 3 HOURS LEFT TO LIVE BEFORE IT DIES A TRAGIC PAINFUL DEATH! 💀😭 WHY YOU TREAT TODAY'S PROBLEM LIKE UNWANTED EDGE CASE?! GO SOLVE #${pod.id} ${pod.title.toUpperCase()} THIS INSTANT OR WE ARE NOT FRIENDS ANYMORE! 💔🔥`
  ];
  return fallbacks[Math.floor(Math.random() * fallbacks.length)];
}

// ---------------------------------------------------------------------------
// Email Formatting & Nodemailer
// ---------------------------------------------------------------------------

function buildChaoticHtml({ name, streak, pod, solveUrl, chaoticText }) {
  const userName = (name || 'CODER').toUpperCase();
  const safeText = chaoticText.replace(/\n/g, '<br><br>');

  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>💀 YOUR STREAK IS DIE IN 3 HOURS! 🦉</title>
</head>
<body style="margin: 0; padding: 0; background-color: #090a10; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #f4f4f5;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #090a10; padding: 36px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" style="max-width: 580px; background: #11131f; border: 2px solid #ef4444; border-radius: 20px; overflow: hidden; box-shadow: 0 0 35px rgba(239, 68, 68, 0.25);">
          
          <!-- Urgent Banner -->
          <tr>
            <td style="background: linear-gradient(135deg, #dc2626, #b91c1c); padding: 22px 28px; text-align: center;">
              <div style="font-size: 34px; margin-bottom: 6px;">🦉 💀 🥀</div>
              <div style="font-size: 20px; font-weight: 900; letter-spacing: 0.5px; color: #ffffff; text-transform: uppercase;">
                URGENT: ${streak}-DAY STREAK EMERGENCY!
              </div>
            </td>
          </tr>

          <!-- Chaotic Message -->
          <tr>
            <td style="padding: 32px 28px;">
              <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 14px; padding: 24px; font-size: 15px; font-weight: 800; line-height: 1.6; color: #fecaca; letter-spacing: 0.3px;">
                ${safeText}
              </div>

              <!-- Problem of the Day Box -->
              <table role="presentation" width="100%" style="margin-top: 24px; background: #0c0e17; border: 1px solid #27272a; border-radius: 14px;">
                <tr>
                  <td style="padding: 20px;">
                    <div style="display: flex; gap: 8px; margin-bottom: 8px;">
                      <span style="font-size: 11px; font-weight: 800; text-transform: uppercase; padding: 3px 8px; border-radius: 6px; background: #ef4444; color: #ffffff;">
                        ${pod.difficulty}
                      </span>
                      <span style="font-size: 12px; font-weight: 600; color: #a1a1aa; padding-top: 2px;">
                        ${pod.category}
                      </span>
                    </div>
                    <div style="font-size: 18px; font-weight: 900; color: #ffffff; margin-bottom: 6px;">
                      #${pod.id} ${pod.title}
                    </div>
                    <div style="font-size: 12px; color: #fb7185; font-weight: 700;">
                      ⚡ Resets at midnight in your local timezone!
                    </div>
                  </td>
                </tr>
              </table>

              <!-- Action Button -->
              <table role="presentation" width="100%" style="margin-top: 28px;">
                <tr>
                  <td align="center">
                    <a href="${solveUrl}" target="_blank" style="display: inline-block; background: linear-gradient(135deg, #ef4444, #dc2626); color: #ffffff; font-size: 16px; font-weight: 900; text-transform: uppercase; letter-spacing: 0.5px; text-decoration: none; padding: 16px 36px; border-radius: 999px; box-shadow: 0 10px 25px rgba(239, 68, 68, 0.45);">
                      SAVE MY STREAK NOW 🔥
                    </a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Passive-Aggressive Footer -->
          <tr>
            <td style="padding: 18px 24px; background: #090a10; border-top: 1px solid #1f2233; font-size: 11px; font-weight: 700; color: #71717a; text-align: center; text-transform: uppercase;">
              THIS EMAIL WAS SENT WITH IMMENSE DISAPPOINTMENT BY ALGOHUB OWL 🦉💀 DO NOT REPLY OR I WILL REVERSE YOUR LINKED LIST.
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>`;
}

function getTransporter() {
  const user = process.env.GMAIL_USER;
  const pass = process.env.GMAIL_APP_PASSWORD;

  if (!user || !pass) {
    return null;
  }

  return nodemailer.createTransport({
    service: 'gmail',
    auth: { user, pass },
  });
}

async function sendReminderEmail({ to, subject, text, html }) {
  const transporter = getTransporter();
  if (!transporter) {
    return {
      status: 'skipped',
      reason: 'GMAIL_USER and GMAIL_APP_PASSWORD not configured. Output preview only.',
    };
  }

  const from = `"AlgoHub Owl 🦉" <${process.env.GMAIL_USER}>`;
  const info = await transporter.sendMail({
    from,
    to,
    subject,
    text,
    html,
  });

  return { status: 'sent', messageId: info.messageId };
}

// ---------------------------------------------------------------------------
// Handler
// ---------------------------------------------------------------------------

module.exports = async function handler(req, res) {
  if (req.method !== 'GET' && req.method !== 'POST') {
    res.setHeader('Allow', 'GET, POST');
    return sendJson(res, 405, { error: 'Method not allowed. Use GET or POST.' });
  }

  // 1. Authorization check for Vercel Cron
  const expectedSecret = process.env.CRON_SECRET;
  if (expectedSecret) {
    const authHeader = req.headers.authorization || '';
    const querySecret = new URL(req.url, 'http://localhost').searchParams.get('secret');
    const isAuthorized =
      authHeader === `Bearer ${expectedSecret}` || querySecret === expectedSecret;

    if (!isAuthorized) {
      return sendJson(res, 401, { error: 'Unauthorized. Invalid CRON_SECRET.' });
    }
  }

  const urlObj = new URL(req.url, 'http://localhost');
  const isDryRun = urlObj.searchParams.get('dry_run') === 'true';
  const isMockMode = urlObj.searchParams.get('mock') === 'true';
  const forceHour = urlObj.searchParams.get('force_hour') !== null ? parseInt(urlObj.searchParams.get('force_hour'), 10) : null;
  const previewAll = urlObj.searchParams.get('preview_all') === 'true';

  const now = new Date();
  const siteUrl = resolveSiteUrl(req);

  // 2. Fetch Users from Supabase
  let rawUsers = [];
  let userStatsList = [];
  let profilesList = [];

  const hasDbKeys = Boolean(process.env.SUPABASE_SERVICE_ROLE_KEY);

  if (isMockMode || !hasDbKeys) {
    // Determine dynamic timezone that matches hour 21 right now for realistic demonstration
    const sampleTzs = ['Australia/Sydney', 'Pacific/Noumea', 'Asia/Tokyo', 'Asia/Dhaka', 'UTC', 'America/New_York'];
    const matching21Tz = sampleTzs.find(tz => getLocalHour(now, tz) === 21) || 'Australia/Sydney';

    rawUsers = [
      {
        id: 'usr-1',
        email: 'alex.streak@example.com',
        user_metadata: { full_name: 'Alex Coder', timezone: matching21Tz },
      },
      {
        id: 'usr-2',
        email: 'taylor.late@example.com',
        user_metadata: { full_name: 'Taylor Dev', timezone: 'Asia/Dhaka' }, // hour != 21
      },
      {
        id: 'usr-3',
        email: 'sam.zero@example.com',
        user_metadata: { full_name: 'Sam Novice', timezone: matching21Tz }, // streak == 0
      },
      {
        id: 'usr-4',
        email: 'jordan.solved@example.com',
        user_metadata: { full_name: 'Jordan Pro', timezone: matching21Tz }, // already solved today
      },
    ];

    userStatsList = [
      { user_id: 'usr-1', current_streak: 5, xp: 450, last_solved_date: '2026-11-07', timezone: matching21Tz },
      { user_id: 'usr-2', current_streak: 12, xp: 1200, last_solved_date: '2026-11-07', timezone: 'Asia/Dhaka' },
      { user_id: 'usr-3', current_streak: 0, xp: 0, last_solved_date: null, timezone: matching21Tz },
      { user_id: 'usr-4', current_streak: 20, xp: 2100, last_solved_date: getLocalDateStr(now, matching21Tz), timezone: matching21Tz },
    ];
  } else {
    try {
      const [authBatch, statsBatch, profileBatch] = await Promise.all([
        listAllUsers().catch(() => []),
        select('user_stats', { select: '*' }).catch(() => []),
        select('profiles', { select: '*' }).catch(() => []),
      ]);
      rawUsers = authBatch || [];
      userStatsList = statsBatch || [];
      profilesList = profileBatch || [];
    } catch (err) {
      console.error('[cron/reminders] Supabase fetch error:', err.message);
      return sendJson(res, 500, {
        error: 'Failed to fetch users from Supabase.',
        details: err.message,
      });
    }
  }

  const statsMap = new Map();
  userStatsList.forEach((s) => statsMap.set(s.user_id || s.id, s));

  const profilesMap = new Map();
  profilesList.forEach((p) => profilesMap.set(p.id || p.user_id, p));

  // 3. Filter Users:
  //    - active streak (streak > 0)
  //    - NOT solved today in their local timezone
  //    - local hour is exactly 21 (between 21:00 and 22:00)
  const targetUsers = [];
  const skippedSummary = {
    no_email: 0,
    zero_streak: 0,
    already_solved_today: 0,
    outside_reminder_window: 0,
  };

  for (const u of rawUsers) {
    const stats = statsMap.get(u.id) || {};
    const profile = profilesMap.get(u.id) || {};

    const email = u.email || profile.email;
    if (!email) {
      skippedSummary.no_email++;
      continue;
    }

    const streak = stats.current_streak ?? profile.current_streak ?? profile.streak ?? u.user_metadata?.streak ?? 0;
    if (streak <= 0) {
      skippedSummary.zero_streak++;
      continue;
    }

    const timezone = profile.timezone || stats.timezone || u.user_metadata?.timezone || u.timezone || 'UTC';
    const todayLocal = getLocalDateStr(now, timezone);

    // Check last_solved_date
    const rawSolvedDate = stats.last_solved_date || stats.last_active_date || profile.last_solved_date || u.user_metadata?.last_solved_date;
    const solvedToday = rawSolvedDate ? getLocalDateStr(new Date(rawSolvedDate), timezone) === todayLocal || rawSolvedDate === todayLocal : false;

    if (solvedToday) {
      skippedSummary.already_solved_today++;
      continue;
    }

    const currentLocalHour = getLocalHour(now, timezone);
    const inWindow = forceHour !== null ? currentLocalHour === forceHour : (previewAll || isBetween21And22(now, timezone));

    if (!inWindow) {
      skippedSummary.outside_reminder_window++;
      continue;
    }

    const name = u.user_metadata?.full_name || u.user_metadata?.name || profile.name || email.split('@')[0];

    targetUsers.push({
      userId: u.id,
      email,
      name,
      streak,
      timezone,
      currentLocalHour,
      todayLocal,
    });
  }

  // 4. Generate Chaotic Reminder Payloads and Dispatch via Nodemailer
  const results = [];

  for (const target of targetUsers) {
    const pod = getProblemOfTheDay(now, target.timezone);
    const solveUrl = `${siteUrl}/solutions/${pod.slug}`;

    const chaoticText = await generateChaoticEmailBody({
      name: target.name,
      streak: target.streak,
      pod,
      solveUrl,
    });

    const subject = `💀 ${target.name.toUpperCase()}, YOUR ${target.streak}-DAY STREAK IS DIE IN 3 HOURS!! 😭🦉`;
    const html = buildChaoticHtml({
      name: target.name,
      streak: target.streak,
      pod,
      solveUrl,
      chaoticText,
    });

    let dispatchResult = { status: 'dry_run_preview' };
    if (!isDryRun) {
      try {
        dispatchResult = await sendReminderEmail({
          to: target.email,
          subject,
          text: chaoticText,
          html,
        });
      } catch (err) {
        console.error(`[cron/reminders] Dispatch failed for ${target.email}:`, err.message);
        dispatchResult = { status: 'failed', error: err.message };
      }
    }

    results.push({
      userId: target.userId,
      email: target.email,
      name: target.name,
      streak: target.streak,
      timezone: target.timezone,
      localHour: target.currentLocalHour,
      subject,
      chaoticMessage: chaoticText,
      dispatch: dispatchResult,
    });
  }

  return sendJson(res, 200, {
    success: true,
    timestamp: now.toISOString(),
    mode: isDryRun ? 'dry_run' : 'live',
    isMock: isMockMode || !hasDbKeys,
    smtpConfigured: Boolean(process.env.GMAIL_USER && process.env.GMAIL_APP_PASSWORD),
    geminiConfigured: Boolean(process.env.GEMINI_API_KEY),
    stats: {
      total_examined: rawUsers.length,
      skipped: skippedSummary,
      matched_for_reminders: targetUsers.length,
    },
    reminders: results,
  });
};
