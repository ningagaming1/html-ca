/**
 * auth-guard.js
 * ─────────────────────────────────────────────────────────────────
 * Handles two things:
 *
 *  1. After login  → saves the user (name, role) to sessionStorage
 *     so every page knows who is logged in.
 *
 *  2. On dashboards → checks if the logged-in user's role is allowed
 *     on the current page. If not, redirects them to the right place.
 *
 * ROLE ACCESS RULES
 * ─────────────────
 *  member  → /member-dashboard.html only
 *  trainer → /member-dashboard.html + /trainer-dashboard.html
 *  admin   → all dashboards
 *  owner   → all dashboards (same as admin)
 */

// ── Pages each role is ALLOWED to visit ──────────────────────────
const ROLE_ACCESS = {
    member:  ["member-dashboard.html"],
    trainer: ["member-dashboard.html", "trainer-dashboard.html"],
    admin:   ["member-dashboard.html", "trainer-dashboard.html", "admin-dashboard.html"],
    owner:   ["member-dashboard.html", "trainer-dashboard.html", "admin-dashboard.html"],
};

// ── Where each role goes after login (their home dashboard) ──────
const ROLE_HOME = {
    member:  "/member-dashboard.html",
    trainer: "/trainer-dashboard.html",
    admin:   "/admin-dashboard.html",
    owner:   "/admin-dashboard.html",
};


/**
 * Call this right after a successful /api/login response.
 * Saves the user to sessionStorage so other pages can read it.
 *
 * @param {object} user - The user object from the API response
 *                        { username, role, full_name, ... }
 */
function saveSession(user) {
    sessionStorage.setItem("titans_user", JSON.stringify(user));
}


/**
 * Returns the saved user object, or null if no one is logged in.
 */
function getSession() {
    const raw = sessionStorage.getItem("titans_user");
    return raw ? JSON.parse(raw) : null;
}


/**
 * Clears the session and sends the user back to the login page.
 * Call this when the user clicks "Log Out".
 */
function logout() {
    sessionStorage.removeItem("titans_user");
    window.location.href = "/login.html";
}


/**
 * Call this at the top of every dashboard page.
 *
 * It checks:
 *  - Is the user logged in at all?       → if not, redirect to /login.html
 *  - Is the user allowed on this page?   → if not, redirect to their home dashboard
 *
 * @param {string} requiredPage - e.g. "member-dashboard.html"
 */
function guardPage(requiredPage) {
    const user = getSession();

    // Not logged in at all → go to login
    if (!user) {
        window.location.href = "/login.html";
        return null;
    }

    const role = user.role.toLowerCase();
    const allowed = ROLE_ACCESS[role] || [];

    // Logged in but not allowed on this page → go to their own dashboard
    if (!allowed.includes(requiredPage)) {
        window.location.href = ROLE_HOME[role] || "/login.html";
        return null;
    }

    // All good — return the user so the page can use their name/role
    return user;
}
