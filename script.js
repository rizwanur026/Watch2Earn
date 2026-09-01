// ============================================================
// Watch2Earn Frontend - Fixed
// ============================================================

"use strict";

const API_URL = "https://watch2earn-lp3w.onrender.com";

let balance = 0;
let adsWatched = 0;
let referrals = 0;

const tg = window.Telegram && window.Telegram.WebApp
    ? window.Telegram.WebApp
    : null;

const PAGES = [
    "home",
    "tasks",
    "games",
    "leaderboard",
    "wallet",
    "profile",
    "referral"
];

// ============================================================
// TELEGRAM INITIALIZATION
// ============================================================

function initTelegram() {
    if (!tg) {
        console.warn("Telegram WebApp not detected.");
        return;
    }

    try {
        tg.ready();
        tg.expand();
        if (typeof tg.enableClosingConfirmation === "function") {
            tg.enableClosingConfirmation();
        }
    } catch (error) {
        console.warn("Telegram initialization warning:", error);
    }
}

// ============================================================
// UI
// ============================================================

function updateUI() {
    const values = {
        balance: balance,
        adsWatched: adsWatched,
        refCount: referrals,
        referralCount: referrals,
        profileCoins: balance,
        profileAds: adsWatched,
        profileRefs: referrals
    };

    Object.entries(values).forEach(([id, value]) => {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    });
}

function showMessage(message) {
    window.alert(String(message));
}

// ============================================================
// API
// ============================================================

async function apiRequest(endpoint, options = {}) {
    const headers = {
        Accept: "application/json",
        ...(options.headers || {})
    };

    let response;

    try {
        response = await fetch(`${API_URL}${endpoint}`, {
            ...options,
            headers
        });
    } catch (error) {
        console.error("Network/API connection error:", error);
        throw new Error(
            "Cannot connect to Watch2Earn server. Please check the Render service."
        );
    }

    const contentType = response.headers.get("content-type") || "";
    let data = null;

    if (contentType.includes("application/json")) {
        try {
            data = await response.json();
        } catch (error) {
            data = null;
        }
    } else {
        const text = await response.text();
        data = text ? { message: text } : null;
    }

    if (!response.ok) {
        throw new Error(
            data?.detail ||
            data?.message ||
            `Server error (${response.status})`
        );
    }

    return data;
}

// ============================================================
// AUTH
// ============================================================

async function authenticateUser() {
    if (!tg || !tg.initData) {
        console.warn("No Telegram initData. Guest mode.");
        setGuestProfile();
        return false;
    }

    try {
        const data = await apiRequest("/auth", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                init_data: tg.initData
            })
        });

        if (!data || !data.user) {
            throw new Error("Authentication response is invalid.");
        }

        balance = Number(data.user.balance || 0);
        adsWatched = Number(data.user.ads_watched || 0);
        referrals = Number(data.user.referrals || 0);

        updateUI();
        setTelegramProfile();

        return true;
    } catch (error) {
        console.error("Authentication error:", error);
        setGuestProfile();
        return false;
    }
}

function setTelegramProfile() {
    const user = tg?.initDataUnsafe?.user;

    if (!user) {
        setGuestProfile();
        return;
    }

    const fullName = `${user.first_name || ""} ${user.last_name || ""}`.trim();

    const headerTitle = document.querySelector(".header h1");
    const profileName = document.querySelector(".profile-card h2");
    const profileInfo = document.querySelector(".profile-card p");
    const avatar = document.querySelector(".avatar");
    const profileAvatar = document.querySelector(".profile-avatar");

    if (headerTitle) {
        headerTitle.textContent = `Hi, ${user.first_name || "User"}!`;
    }

    if (profileName) {
        profileName.textContent = fullName || "User";
    }

    if (profileInfo) {
        profileInfo.textContent = `Telegram ID: ${user.id}`;
    }

    const initial = (user.first_name || "W").charAt(0).toUpperCase();

    if (avatar) avatar.textContent = initial;
    if (profileAvatar) profileAvatar.textContent = initial;
}

function setGuestProfile() {
    const headerTitle = document.querySelector(".header h1");
    const profileName = document.querySelector(".profile-card h2");
    const profileInfo = document.querySelector(".profile-card p");

    if (headerTitle) headerTitle.textContent = "Watch2Earn";
    if (profileName) profileName.textContent = "Guest";
    if (profileInfo) profileInfo.textContent = "Open this app from Telegram";
}

// ============================================================
// TASKS
// ============================================================

async function loadTasks() {
    const container = document.getElementById("tasksContainer");
    if (!container) return;

    container.innerHTML = `
        <div class="task">
            <div class="task-info">
                <h3>Loading Tasks...</h3>
                <p>Please wait...</p>
            </div>
        </div>
    `;

    try {
        const data = await apiRequest("/tasks");

        if (!data || !Array.isArray(data.tasks) || data.tasks.length === 0) {
            container.innerHTML = `
                <div class="task">
                    <div class="task-info">
                        <h3>No tasks available</h3>
                        <p>New tasks will appear here.</p>
                    </div>
                </div>
            `;
            return;
        }

        container.innerHTML = "";

        data.tasks.forEach(task => {
            renderTask(container, task);
        });
    } catch (error) {
        console.error("Task loading error:", error);

        container.innerHTML = `
            <div class="task">
                <div class="task-info">
                    <h3>Unable to load tasks</h3>
                    <p>${escapeHTML(error.message)}</p>
                    <button type="button" onclick="loadTasks()">Retry</button>
                </div>
            </div>
        `;
    }
}

function renderTask(container, task) {
    const taskElement = document.createElement("div");
    taskElement.className = "task";

    const taskId = Number(task.id);
    const title = escapeHTML(task.title || "Untitled Task");
    const description = escapeHTML(task.description || "Complete this task");
    const reward = Number(task.reward || 0);
    const taskType = escapeHTML(task.task_type || "website");
    const link = String(task.link || "").trim();

    taskElement.innerHTML = `
        <div class="task-icon">${getTaskIcon(taskType)}</div>

        <div class="task-info">
            <h3>${title}</h3>
            <p>${description}</p>
            <p>+${reward} W2E</p>
        </div>

        <button type="button" class="task-start-btn">Start</button>
    `;

    const button = taskElement.querySelector(".task-start-btn");

    if (button) {
        button.addEventListener("click", () => {
            startTask(taskId, link, button);
        });
    }

    container.appendChild(taskElement);
}

function getTaskIcon(type) {
    switch (String(type).toLowerCase()) {
        case "telegram": return "📢";
        case "website": return "🌐";
        case "social": return "⭐";
        case "video": return "🎬";
        default: return "🎯";
    }
}

function escapeHTML(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

async function startTask(taskId, link, button) {
    if (!tg || !tg.initData) {
        showMessage("Please open Watch2Earn from Telegram.");
        return;
    }

    if (!link) {
        showMessage("This task does not have a link.");
        return;
    }

    if (button?.dataset.completed === "true") return;

    if (button) {
        button.disabled = true;
        button.textContent = "Opening...";
    }

    try {
        if (typeof tg.openLink === "function") {
            tg.openLink(link);
        } else {
            window.open(link, "_blank", "noopener,noreferrer");
        }

        // Telegram Mini Apps may not reliably support window.confirm
        // after opening another page, so use a normal browser confirm only
        // when available. The task can still be completed through the API.
        const completed = window.confirm("Did you complete this task?");

        if (!completed) {
            if (button) {
                button.disabled = false;
                button.textContent = "Start";
            }
            return;
        }

        await completeTask(taskId, button);
    } catch (error) {
        console.error("Task error:", error);

        if (button) {
            button.disabled = false;
            button.textContent = "Start";
        }

        showMessage(error.message || "Unable to complete task.");
    }
}

async function completeTask(taskId, button) {
    if (!tg || !tg.initData) {
        showMessage("Please open Watch2Earn from Telegram.");
        return;
    }

    if (button?.dataset.completing === "true") return;

    if (button) {
        button.dataset.completing = "true";
        button.disabled = true;
        button.textContent = "Checking...";
    }

    try {
        const data = await apiRequest(`/tasks/${taskId}/complete`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                init_data: tg.initData
            })
        });

        if (!data.success) {
            if (button) {
                button.textContent = "Completed ✓";
                button.dataset.completed = "true";
                button.dataset.completing = "false";
            }

            showMessage(data.message || "Task already completed.");
            return;
        }

        balance = Number(data.balance || 0);
        updateUI();

        if (button) {
            button.textContent = "Completed ✓";
            button.disabled = true;
            button.dataset.completed = "true";
            button.dataset.completing = "false";
        }

        showMessage(`+${Number(data.reward || 0)} W2E earned!`);
    } catch (error) {
        console.error("Task completion error:", error);

        if (button) {
            button.disabled = false;
            button.dataset.completing = "false";
            button.textContent = "Start";
        }

        showMessage(error.message || "Unable to complete task.");
    }
}

// ============================================================
// WATCH AD
// ============================================================

async function watchAd() {
    if (!tg || !tg.initData) {
        showMessage("Please open Watch2Earn from Telegram.");
        return;
    }

    try {
        const data = await apiRequest("/watch-ad", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                init_data: tg.initData
            })
        });

        if (!data.success) {
            if (data.remaining_seconds) {
                showMessage(`Please wait ${data.remaining_seconds} seconds.`);
            } else {
                showMessage(data.message || "Ad reward failed.");
            }
            return;
        }

        balance = Number(data.balance || 0);
        adsWatched = Number(data.ads_watched || 0);

        updateUI();
        showMessage(`+${Number(data.reward || 0)} W2E earned!`);
    } catch (error) {
        console.error("Watch ad error:", error);
        showMessage(error.message || "Unable to give ad reward.");
    }
}

// ============================================================
// DAILY BONUS
// ============================================================

async function dailyBonus() {
    if (!tg || !tg.initData) {
        showMessage("Please open Watch2Earn from Telegram.");
        return;
    }

    const button = document.getElementById("bonusBtn");

    if (button?.dataset.loading === "true") return;

    if (button) {
        button.dataset.loading = "true";
        button.disabled = true;
        button.textContent = "Checking...";
    }

    try {
        const data = await apiRequest("/daily-bonus", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                init_data: tg.initData
            })
        });

        if (!data.success) {
            showMessage(
                `Daily bonus already claimed.\n\n` +
                `Try again in ${data.remaining_hours || 0}h ` +
                `${data.remaining_minutes || 0}m.`
            );

            if (button) {
                button.textContent = "Claimed";
                button.disabled = true;
                button.dataset.loading = "false";
            }

            return;
        }

        balance = Number(data.balance || 0);
        updateUI();

        if (button) {
            button.textContent = "Claimed ✓";
            button.disabled = true;
            button.dataset.loading = "false";
        }

        const status = document.getElementById("dailyStatus");
        if (status) status.textContent = "Claimed";

        showMessage(`+${Number(data.reward || 0)} W2E earned!`);
    } catch (error) {
        console.error("Daily bonus error:", error);

        if (button) {
            button.disabled = false;
            button.textContent = "Claim";
            button.dataset.loading = "false";
        }

        showMessage(error.message || "Unable to claim bonus.");
    }
}

// ============================================================
// REFERRALS
// ============================================================

function getReferralLink() {
    const user = tg?.initDataUnsafe?.user;

    if (!user) {
        showMessage("Open the app from Telegram.");
        return null;
    }

    return `https://t.me/Watch2EarnBot?start=${encodeURIComponent(user.id)}`;
}

async function copyReferral() {
    const link = getReferralLink();
    if (!link) return;

    try {
        if (navigator.clipboard?.writeText) {
            await navigator.clipboard.writeText(link);
            showMessage("Referral link copied!");
        } else {
            window.prompt("Copy your referral link:", link);
        }
    } catch (error) {
        console.error("Clipboard error:", error);
        window.prompt("Copy your referral link:", link);
    }
}

function shareReferral() {
    const link = getReferralLink();
    if (!link) return;

    const text = "Join Watch2Earn and start earning W2E!";
    const shareUrl =
        "https://t.me/share/url?" +
        "url=" + encodeURIComponent(link) +
        "&text=" + encodeURIComponent(text);

    if (tg && typeof tg.openTelegramLink === "function") {
        tg.openTelegramLink(shareUrl);
    } else {
        window.open(shareUrl, "_blank", "noopener,noreferrer");
    }
}

async function loadReferralStats() {
    const user = tg?.initDataUnsafe?.user;
    if (!user) return;

    try {
        const data = await apiRequest(`/referrals/${encodeURIComponent(user.id)}`);
        referrals = Number(data.referrals || 0);
        updateUI();
    } catch (error) {
        console.error("Referral loading error:", error);
    }
}

function loadReferralUI() {
    const link = getReferralLink();
    const input = document.getElementById("referralLink");

    if (input && link) {
        input.value = link;
    }
}

// ============================================================
// WALLET
// ============================================================

function connectWallet() {
    const input = document.getElementById("walletAddress");
    if (input) input.focus();
}

async function loadWallet() {
    if (!tg || !tg.initData) return;

    try {
        const data = await apiRequest(
            `/wallet?init_data=${encodeURIComponent(tg.initData)}`
        );

        const input = document.getElementById("walletAddress");
        const status = document.getElementById("walletStatus");

        if (input) input.value = data.wallet_address || "";
        if (status) {
            status.textContent = data.wallet_address
                ? "Wallet connected"
                : "No wallet connected";
        }
    } catch (error) {
        console.error("Wallet loading error:", error);
    }
}

async function saveWallet() {
    if (!tg || !tg.initData) {
        showMessage("Please open Watch2Earn from Telegram.");
        return;
    }

    const input = document.getElementById("walletAddress");

    if (!input) {
        showMessage("Wallet input not found.");
        return;
    }

    const walletAddress = input.value.trim();

    if (!walletAddress) {
        showMessage("Enter your TON wallet address.");
        return;
    }

    try {
        const data = await apiRequest("/wallet", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                init_data: tg.initData,
                wallet_address: walletAddress
            })
        });

        const status = document.getElementById("walletStatus");
        if (status) status.textContent = "Wallet connected ✓";

        showMessage(data.message || "TON wallet saved successfully!");
    } catch (error) {
        console.error("Wallet save error:", error);
        showMessage(error.message || "Unable to save wallet.");
    }
}

async function removeWallet() {
    if (!tg || !tg.initData) {
        showMessage("Please open Watch2Earn from Telegram.");
        return;
    }

    try {
        await apiRequest("/wallet", {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                init_data: tg.initData
            })
        });

        const input = document.getElementById("walletAddress");
        const status = document.getElementById("walletStatus");

        if (input) input.value = "";
        if (status) status.textContent = "No wallet connected";

        showMessage("Wallet removed.");
    } catch (error) {
        console.error("Wallet remove error:", error);
        showMessage(error.message || "Unable to remove wallet.");
    }
}

// ============================================================
// GAMES
// ============================================================

function startGame() {
    showMessage(
        "Tap Challenge\n\nMini game integration will be added next."
    );
}

function luckyBox() {
    showMessage(
        "Lucky Box\n\nGame reward system will be added next."
    );
}

// ============================================================
// LEADERBOARD
// ============================================================

async function loadLeaderboard() {
    const container = document.getElementById("leaderboardContainer");
    if (!container) return;

    container.innerHTML = "<p>Loading leaderboard...</p>";

    try {
        const data = await apiRequest("/leaderboard?limit=20");

        if (!data || !Array.isArray(data.leaderboard)) {
            container.innerHTML = "<p>No leaderboard data.</p>";
            return;
        }

        if (data.leaderboard.length === 0) {
            container.innerHTML = "<p>No users yet.</p>";
            return;
        }

        container.innerHTML = "";

        data.leaderboard.forEach(user => {
            const row = document.createElement("div");
            row.className = "leaderboard-row";

            const displayName = user.username
                ? `@${user.username}`
                : (user.first_name || "User");

            row.innerHTML = `
                <div class="leader-rank">#${Number(user.rank || 0)}</div>
                <div class="leader-user">${escapeHTML(displayName)}</div>
                <div class="leader-balance">${Number(user.balance || 0)} W2E</div>
            `;

            container.appendChild(row);
        });
    } catch (error) {
        console.error("Leaderboard error:", error);
        container.innerHTML = `
            <p>Unable to load leaderboard.</p>
            <p class="error-text">${escapeHTML(error.message)}</p>
        `;
    }
}

// ============================================================
// NAVIGATION
// ============================================================

function showPage(pageId) {
    if (!PAGES.includes(pageId)) return;

    document.querySelectorAll(".page").forEach(page => {
        page.classList.toggle("active", page.id === pageId);
    });

    document.querySelectorAll(".nav-btn").forEach(button => {
        button.classList.remove("active");
    });

    const index = PAGES.indexOf(pageId);
    const buttons = document.querySelectorAll(".nav-btn");

    if (buttons[index]) {
        buttons[index].classList.add("active");
    }

    if (pageId === "tasks") loadTasks();
    if (pageId === "leaderboard") loadLeaderboard();
    if (pageId === "wallet") loadWallet();

    if (pageId === "referral") {
        loadReferralStats();
        loadReferralUI();
    }

    window.scrollTo({ top: 0, behavior: "smooth" });
}

// ============================================================
// START
// ============================================================

async function startApp() {
    initTelegram();
    updateUI();

    const authenticated = await authenticateUser();

    // Navigation remains usable even if an API/auth request fails.
    if (authenticated) {
        await Promise.allSettled([
            loadReferralStats(),
            loadTasks(),
            loadLeaderboard(),
            loadWallet()
        ]);
        loadReferralUI();
    } else {
        await Promise.allSettled([
            loadTasks(),
            loadLeaderboard()
        ]);
    }
}

// ============================================================
// GLOBAL FUNCTIONS
// ============================================================

window.showPage = showPage;
window.watchAd = watchAd;
window.dailyBonus = dailyBonus;
window.copyReferral = copyReferral;
window.shareReferral = shareReferral;
window.saveWallet = saveWallet;
window.removeWallet = removeWallet;
window.connectWallet = connectWallet;
window.startGame = startGame;
window.luckyBox = luckyBox;
window.loadTasks = loadTasks;
window.loadLeaderboard = loadLeaderboard;

// Start after DOM is ready.
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", startApp, { once: true });
} else {
    startApp();
}
