/**
 * AlgoHub Daily Reminder System — Vercel Serverless Function / Cron Target
 * Route: GET /api/reminders or POST /api/reminders
 *
 * Purpose:
 *   1. Identifies today's Problem of the Day (matches dashboard logic).
 *   2. Fetches registered users and their streak/XP stats from Supabase.
 *   3. Excludes users who have already solved today's PoD.
 *   4. Generates rich, personalized Email & Push notification payloads.
 *   5. Dispatches via configured email provider (e.g., Resend) or outputs
 *      the prepared payloads for preview/dry-run.
 *
 * Security:
 *   - Verifies Bearer token against CRON_SECRET if set (Vercel Cron automatically
 *     sends `Authorization: Bearer <CRON_SECRET>`).
 *   - Uses SUPABASE_SERVICE_ROLE_KEY server-side only to access user stats.
 *
 * Query Parameters:
 *   ?dry_run=true    (default: true) Returns prepared payloads without sending emails.
 *   ?mock=true       Uses simulated user data for local testing if DB keys are not yet configured.
 *   ?secret=...      Alternative to Authorization header for manual testing.
 */

const { getProblemOfTheDay, datePartsInZone } = require('./_lib/problems');
const { listAllUsers, select } = require('./_lib/supabase-admin');

// ---------------------------------------------------------------------------
// Helpers & Templates
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

function getHoursUntilReset(timeZone = 'UTC') {
  const now = new Date();
  const tomorrow = new Date(now);
  tomorrow.setUTCDate(tomorrow.getUTCDate() + 1);
  tomorrow.setUTCHours(0, 0, 0, 0);
  return Math.max(1, Math.ceil((tomorrow - now) / (1000 * 60 * 60)));
}

function getDifficultyColor(diff) {
  switch (diff?.toLowerCase()) {
    case 'easy':
      return { bg: '#e8f8f1', text: '#1ea672', border: '#a7f3d0' };
    case 'medium':
      return { bg: '#fdf1e0', text: '#c2780a', border: '#fde68a' };
    case 'hard':
      return { bg: '#fde9ec', text: '#d23c4f', border: '#fecdd3' };
    default:
      return { bg: '#eef1ff', text: '#4f6df5', border: '#c7d2fe' };
  }
}

/**
 * Builds a modern, responsive HTML email matching AlgoHub's theme.
 */
function buildReminderEmailHtml({ user, pod, solveUrl, streak, xp, hoursLeft }) {
  const diff = getDifficultyColor(pod.difficulty);
  const streakText = streak > 0 ? `${streak} Day Streak 🔥` : 'Start Your Streak ⚡';
  const streakMessage = streak > 0
    ? `You are on a <strong>${streak}-day streak</strong>! Solve today's challenge within ${hoursLeft} hours to keep your momentum going and lock in a <strong>2x XP bonus</strong>.`
    : `Kickstart a new daily streak today! Complete this challenge within ${hoursLeft} hours to earn a <strong>2x XP bonus</strong>.`;

  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AlgoHub Daily Challenge</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0c0e16; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #eceef6;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #0c0e16; padding: 40px 15px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" style="max-width: 560px; background: #131623; border: 1px solid #1f2333; border-radius: 16px; overflow: hidden; box-shadow: 0 16px 36px rgba(0,0,0,0.4);">
          
          <!-- Header -->
          <tr>
            <td style="background: linear-gradient(135deg, #4f6df5, #8b5cf6); padding: 28px 32px; text-align: left;">
              <table role="presentation" width="100%">
                <tr>
                  <td>
                    <span style="display: inline-block; font-size: 22px; font-weight: 900; letter-spacing: -0.5px; color: #ffffff;">algoHub</span>
                    <span style="margin-left: 8px; font-size: 11px; font-weight: 700; text-transform: uppercase; background: rgba(255,255,255,0.25); color: #ffffff; padding: 2px 8px; border-radius: 999px;">Daily Challenge</span>
                  </td>
                  <td align="right">
                    <span style="font-size: 13px; font-weight: 700; background: rgba(0,0,0,0.2); color: #ffffff; padding: 6px 12px; border-radius: 8px;">${streakText}</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding: 32px;">
              <h2 style="margin: 0 0 12px; font-size: 20px; font-weight: 700; color: #ffffff;">Hey ${user.name}, ready for today's challenge?</h2>
              <p style="margin: 0 0 24px; font-size: 14px; line-height: 1.6; color: #8e93a8;">
                ${streakMessage}
              </p>

              <!-- Problem Card -->
              <table role="presentation" width="100%" style="background: #0c0e16; border: 1px solid #1f2333; border-radius: 12px; margin-bottom: 24px;">
                <tr>
                  <td style="padding: 20px;">
                    <div style="margin-bottom: 8px;">
                      <span style="display: inline-block; font-size: 11px; font-weight: 800; text-transform: uppercase; padding: 3px 8px; border-radius: 6px; background: ${diff.bg}; color: ${diff.text};">
                        ${pod.difficulty}
                      </span>
                      <span style="margin-left: 6px; font-size: 12px; font-weight: 600; color: #8e93a8;">
                        ${pod.category}
                      </span>
                    </div>
                    <div style="font-size: 18px; font-weight: 800; color: #ffffff; margin-bottom: 6px;">
                      #${pod.id} ${pod.title}
                    </div>
                    <div style="font-size: 12px; color: #7c93ff; font-weight: 600;">
                      ⚡ 2x XP Multiplier Active · Resets in ~${hoursLeft}h
                    </div>
                  </td>
                </tr>
              </table>

              <!-- Call to Action -->
              <table role="presentation" width="100%">
                <tr>
                  <td align="center" style="padding-bottom: 12px;">
                    <a href="${solveUrl}" target="_blank" style="display: inline-block; background: linear-gradient(135deg, #4f6df5, #6366f1); color: #ffffff; font-size: 15px; font-weight: 700; text-decoration: none; padding: 14px 32px; border-radius: 10px; box-shadow: 0 8px 20px rgba(79, 109, 245, 0.4);">
                      Solve Today's Problem →
                    </a>
                  </td>
                </tr>
              </table>

              <p style="margin: 16px 0 0; font-size: 12px; text-align: center; color: #6b7080;">
                Stuck while solving? Open the built-in <strong>AI Tutor</strong> for instant hints and code reviews.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding: 20px 32px; background: #0e1018; border-top: 1px solid #1f2333; font-size: 12px; color: #6b7080; text-align: center;">
              You received this because you are an active member of AlgoHub. Current XP: <strong>${xp}</strong>.
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>`;
}

function buildReminderText({ user, pod, solveUrl, streak, hoursLeft }) {
  return [
    `Hey ${user.name}!`,
    '',
    streak > 0
      ? `Keep your ${streak}-day streak alive on AlgoHub!`
      : `Ready to start a new daily streak on AlgoHub?`,
    '',
    `Today's Problem of the Day: #${pod.id} ${pod.title}`,
    `Difficulty: ${pod.difficulty} | Category: ${pod.category}`,
    `Bonus: 2x XP Multiplier (resets in ~${hoursLeft} hours)`,
    '',
    `Solve it now: ${solveUrl}`,
    '',
    'Need a hint? Open the built-in AI Tutor right inside the problem page.',
    '',
    '— The AlgoHub Team',
  ].join('\n');
}

/**
 * Optional email dispatcher (e.g., via Resend).
 * Pluggable: easily activated by adding RESEND_API_KEY to environment variables.
 */
async function dispatchEmail(payload) {
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) return { status: 'skipped', reason: 'RESEND_API_KEY not configured' };

  const from = process.env.EMAIL_FROM || 'AlgoHub <reminders@algohub.dev>';
  const res = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      from,
      to: payload.to,
      subject: payload.subject,
      html: payload.html,
      text: payload.text,
    }),
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.message || 'Email dispatch failed');
  return { status: 'sent', id: data.id };
}

// ---------------------------------------------------------------------------
// Main Handler
// ---------------------------------------------------------------------------

module.exports = async function handler(req, res) {
  if (req.method !== 'GET' && req.method !== 'POST') {
    res.setHeader('Allow', 'GET, POST');
    return sendJson(res, 405, { error: 'Method not allowed. Use GET or POST.' });
  }

  // 1. Authorization check for Cron / Admin triggers
  const expectedSecret = process.env.CRON_SECRET;
  if (expectedSecret) {
    const authHeader = req.headers.authorization || '';
    const querySecret = new URL(req.url, 'http://localhost').searchParams.get('secret');
    const isAuthorized =
      authHeader === `Bearer ${expectedSecret}` || querySecret === expectedSecret;

    if (!isAuthorized) {
      return sendJson(res, 401, { error: 'Unauthorized. Provide valid CRON_SECRET.' });
    }
  }

  const urlObj = new URL(req.url, 'http://localhost');
  const isDryRun = urlObj.searchParams.get('dry_run') !== 'false';
  const isMockMode = urlObj.searchParams.get('mock') === 'true';

  // 2. Determine Today's Problem of the Day
  const timeZone = process.env.TIMEZONE || 'UTC';
  const now = new Date();
  const { isoDate } = datePartsInZone(now, timeZone);
  const pod = getProblemOfTheDay(now, timeZone);
  const hoursLeft = getHoursUntilReset(timeZone);
  const siteUrl = resolveSiteUrl(req);
  const solveUrl = `${siteUrl}/solutions/${pod.slug}`;

  // 3. Retrieve Users & Progress from Supabase
  let authUsers = [];
  let userStatsMap = new Map();
  let solvedTodaySet = new Set();

  if (isMockMode || !process.env.SUPABASE_SERVICE_ROLE_KEY) {
    // If service role key is not yet set in environment, provide mock data so the endpoint can be inspected immediately
    authUsers = [
      { id: 'usr-1', email: 'alex@example.com', user_metadata: { full_name: 'Alex Developer' } },
      { id: 'usr-2', email: 'taylor@example.com', user_metadata: { name: 'Taylor Coder' } },
      { id: 'usr-3', email: 'sam@example.com', user_metadata: {} },
    ];
    userStatsMap.set('usr-1', { current_streak: 5, xp: 420 });
    userStatsMap.set('usr-2', { current_streak: 0, xp: 80 });
    solvedTodaySet.add('usr-3'); // user 3 already solved today
  } else {
    try {
      const [users, stats, attempts] = await Promise.all([
        listAllUsers(),
        select('user_stats', { select: 'user_id,xp,current_streak,last_active_date' }).catch(() => []),
        select('daily_pod_attempts', { pod_date: `eq.${isoDate}` }).catch(() => []),
      ]);

      authUsers = users || [];
      if (Array.isArray(stats)) {
        stats.forEach((s) => userStatsMap.set(s.user_id, s));
      }
      if (Array.isArray(attempts)) {
        attempts.filter((a) => a.solved_at).forEach((a) => solvedTodaySet.add(a.user_id));
      }
    } catch (err) {
      console.error('[reminders] Supabase fetch error:', err.message);
      return sendJson(res, 500, {
        error: 'Failed to fetch user data from Supabase.',
        details: err.message,
        hint: 'Ensure SUPABASE_SERVICE_ROLE_KEY is set in your Vercel / .env configuration.',
      });
    }
  }

  // 4. Filter & Prepare Payloads
  const preparedReminders = [];
  const dispatchResults = [];

  for (const u of authUsers) {
    if (!u.email) continue;
    if (solvedTodaySet.has(u.id)) continue; // skip users who already solved today's PoD

    const stats = userStatsMap.get(u.id) || { current_streak: 0, xp: 0 };
    const streak = stats.current_streak || 0;
    const xp = stats.xp || 0;
    const name = u.user_metadata?.full_name || u.user_metadata?.name || u.email.split('@')[0];

    const emailPayload = {
      to: u.email,
      subject: streak > 0
        ? `🔥 Keep your ${streak}-day streak alive! Today: #${pod.id} ${pod.title}`
        : `⚡ Daily Challenge: #${pod.id} ${pod.title} (2x XP Bonus)`,
      html: buildReminderEmailHtml({ user: { name }, pod, solveUrl, streak, xp, hoursLeft }),
      text: buildReminderText({ user: { name }, pod, solveUrl, streak, hoursLeft }),
    };

    const pushPayload = {
      title: `⚡ Daily Challenge: #${pod.id} ${pod.title}`,
      body: streak > 0
        ? `Keep your ${streak}-day streak alive! Solve within ${hoursLeft}h for double XP.`
        : `Today's problem: ${pod.difficulty} • ${pod.category}. Earn 2x XP before midnight!`,
      url: solveUrl,
      tag: `pod-${isoDate}`,
    };

    preparedReminders.push({
      userId: u.id,
      email: u.email,
      streak,
      xp,
      emailPayload,
      pushPayload,
    });

    // 5. If not dry_run and email provider configured, dispatch
    if (!isDryRun) {
      try {
        const result = await dispatchEmail(emailPayload);
        dispatchResults.push({ userId: u.id, email: u.email, ...result });
      } catch (err) {
        dispatchResults.push({ userId: u.id, email: u.email, status: 'failed', error: err.message });
      }
    }
  }

  return sendJson(res, 200, {
    success: true,
    timestamp: now.toISOString(),
    date: isoDate,
    mode: isDryRun ? 'dry_run' : 'live_dispatch',
    isMock: isMockMode || !process.env.SUPABASE_SERVICE_ROLE_KEY,
    pod: {
      id: pod.id,
      title: pod.title,
      difficulty: pod.difficulty,
      category: pod.category,
      slug: pod.slug,
      solveUrl,
      hoursLeft,
    },
    summary: {
      total_users_examined: authUsers.length,
      already_solved_today: solvedTodaySet.size,
      reminders_prepared: preparedReminders.length,
      dispatched: dispatchResults.length,
    },
    // Include full payloads for preview/testing
    reminders: preparedReminders.map((r) => ({
      userId: r.userId,
      email: r.email,
      streak: r.streak,
      xp: r.xp,
      subject: r.emailPayload.subject,
      push: r.pushPayload,
      emailPreviewText: r.emailPayload.text,
      // Keep payload preview clean; html is verified by template
      hasHtml: Boolean(r.emailPayload.html),
    })),
    dispatchResults: dispatchResults.length > 0 ? dispatchResults : undefined,
  });
};
