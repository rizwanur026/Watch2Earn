```javascript
// ============================================================
// Watch2Earn Frontend
// ============================================================

const API_URL =
    "https://watch2earn-lp3w.onrender.com";

let balance = 0;
let adsWatched = 0;
let referrals = 0;

const tg = window.Telegram?.WebApp;


// ============================================================
// TELEGRAM INITIALIZATION
// ============================================================

if (tg) {
    tg.ready();
    tg.expand();

    try {
        tg.enableClosingConfirmation?.();
    } catch (error) {
        console.log("Telegram closing confirmation unavailable");
    }
}


// ============================================================
// UI UPDATE
// ============================================================

function updateUI() {

    const elements = {
        balance: balance,
        adsWatched: adsWatched,
        refCount: referrals,
        referralCount: referrals,
        profileCoins: balance,
        profileAds: adsWatched,
        profileRefs: referrals
    };

    Object.entries(elements).forEach(
        ([id, value]) => {

            const element =
                document.getElementById(id);

            if (element) {
                element.textContent = value;
            }
        }
    );
}


// ============================================================
// API REQUEST
// ============================================================

async function apiRequest(
    endpoint,
    options = {}
) {

    const response = await fetch(
        `${API_URL}${endpoint}`,
        {
            ...options,
            headers: {
                ...(options.headers || {})
            }
        }
    );

    let data = null;

    try {
        data = await response.json();
    } catch {
        data = null;
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
// TELEGRAM AUTHENTICATION
// ============================================================

async function authenticateUser() {

    if (!tg || !tg.initData) {

        console.log(
            "Telegram WebApp not detected."
        );

        setGuestProfile();

        return false;
    }

    try {

        const data =
            await apiRequest(
                "/auth",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        init_data:
                            tg.initData
                    })
                }
            );

        if (
            data &&
            data.user
        ) {

            balance =
                Number(
                    data.user.balance || 0
                );

            adsWatched =
                Number(
                    data.user.ads_watched || 0
                );

            referrals =
                Number(
                    data.user.referrals || 0
                );

            updateUI();

            setTelegramProfile();

            return true;
        }

    } catch (error) {

        console.error(
            "Authentication error:",
            error
        );

        setGuestProfile();

        return false;
    }

    return false;
}


// ============================================================
// TELEGRAM PROFILE
// ============================================================

function setTelegramProfile() {

    const user =
        tg?.initDataUnsafe?.user;

    if (!user) {

        setGuestProfile();

        return;
    }

    const fullName =
        `${user.first_name || ""} ${
            user.last_name || ""
        }`.trim();

    const headerTitle =
        document.querySelector(
            ".header h1"
        );

    const profileName =
        document.querySelector(
            ".profile-card h2"
        );

    const profileInfo =
        document.querySelector(
            ".profile-card p"
        );

    const avatar =
        document.querySelector(
            ".avatar"
        );

    const profileAvatar =
        document.querySelector(
            ".profile-avatar"
        );

    if (headerTitle) {

        headerTitle.textContent =
            `Hi, ${user.first_name || "User"}!`;
    }

    if (profileName) {

        profileName.textContent =
            fullName || "User";
    }

    if (profileInfo) {

        profileInfo.textContent =
            `Telegram ID: ${user.id}`;
    }

    const initial =
        (
            user.first_name ||
            "W"
        )
            .charAt(0)
            .toUpperCase();

    if (avatar) {
        avatar.textContent = initial;
    }

    if (profileAvatar) {
        profileAvatar.textContent = initial;
    }
}


// ============================================================
// GUEST PROFILE
// ============================================================

function setGuestProfile() {

    const headerTitle =
        document.querySelector(
            ".header h1"
        );

    const profileName =
        document.querySelector(
            ".profile-card h2"
        );

    const profileInfo =
        document.querySelector(
            ".profile-card p"
        );

    if (headerTitle) {
        headerTitle.textContent =
            "Hi, Guest!";
    }

    if (profileName) {
        profileName.textContent =
            "Guest";
    }

    if (profileInfo) {
        profileInfo.textContent =
            "Open this app from Telegram";
    }
}


// ============================================================
// LOAD TASKS
// ============================================================

async function loadTasks() {

    const container =
        document.getElementById(
            "tasksContainer"
        );

    if (!container) {
        return;
    }

    container.innerHTML = `
        <div class="task">
            <div class="task-info">
                <h3>Loading Tasks...</h3>
                <p>Please wait...</p>
            </div>
        </div>
    `;

    try {

        const data =
            await apiRequest(
                "/tasks"
            );

        if (
            !data ||
            !data.success ||
            !Array.isArray(data.tasks) ||
            data.tasks.length === 0
        ) {

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

        data.tasks.forEach(
            task => {
                renderTask(
                    container,
                    task
                );
            }
        );

    } catch (error) {

        console.error(
            "Task loading error:",
            error
        );

        container.innerHTML = `
            <div class="task">
                <div class="task-info">
                    <h3>Unable to load tasks</h3>
                    <p>Please try again later.</p>

                    <button
                        type="button"
                        onclick="loadTasks()"
                    >
                        Retry
                    </button>
                </div>
            </div>
        `;
    }
}


// ============================================================
// RENDER TASK
// ============================================================

function renderTask(
    container,
    task
) {

    const taskElement =
        document.createElement(
            "div"
        );

    taskElement.className =
        "task";

    const taskId =
        Number(task.id);

    const title =
        escapeHTML(
            task.title ||
            "Untitled Task"
        );

    const description =
        escapeHTML(
            task.description ||
            "Complete this task"
        );

    const reward =
        Number(task.reward || 0);

    const taskType =
        escapeHTML(
            task.task_type ||
            "website"
        );

    const link =
        String(
            task.link || ""
        ).trim();

    taskElement.innerHTML = `
        <div class="task-icon">
            ${getTaskIcon(taskType)}
        </div>

        <div class="task-info">

            <h3>${title}</h3>

            <p>${description}</p>

            <p>+${reward} W2E</p>

        </div>

        <button
            type="button"
            class="task-start-btn"
        >
            Start
        </button>
    `;

    const button =
        taskElement.querySelector(
            ".task-start-btn"
        );

    if (button) {

        button.addEventListener(
            "click",
            () => {

                startTask(
                    taskId,
                    link,
                    button
                );

            }
        );
    }

    container.appendChild(
        taskElement
    );
}


// ============================================================
// TASK ICON
// ============================================================

function getTaskIcon(type) {

    switch (
        String(type).toLowerCase()
    ) {

        case "telegram":
            return "📢";

        case "website":
            return "🌐";

        case "social":
            return "⭐";

        case "video":
            return "🎬";

        default:
            return "🎯";
    }
}


// ============================================================
// HTML SECURITY
// ============================================================

function escapeHTML(value) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


// ============================================================
// START TASK
// ============================================================

async function startTask(
    taskId,
    link,
    button
) {

    if (!tg || !tg.initData) {

        alert(
            "Please open Watch2Earn from Telegram."
        );

        return;
    }

    if (!link) {

        alert(
            "This task does not have a link."
        );

        return;
    }

    if (
        button?.dataset.completed ===
        "true"
    ) {
        return;
    }

    if (button) {

        button.disabled = true;

        button.textContent =
            "Opening...";
    }

    try {

        if (
            typeof tg.openLink ===
            "function"
        ) {

            tg.openLink(link);

        } else {

            window.open(
                link,
                "_blank"
            );
        }

        const completed =
            window.confirm(
                "Did you complete this task?"
            );

        if (!completed) {

            if (button) {

                button.disabled = false;

                button.textContent =
                    "Start";
            }

            return;
        }

        await completeTask(
            taskId,
            button
        );

    } catch (error) {

        console.error(
            "Task error:",
            error
        );

        if (button) {

            button.disabled = false;

            button.textContent =
                "Start";
        }

        alert(
            error.message ||
            "Unable to complete task."
        );
    }
}


// ============================================================
// COMPLETE TASK
// ============================================================

async function completeTask(
    taskId,
    button
) {

    if (!tg || !tg.initData) {

        alert(
            "Please open Watch2Earn from Telegram."
        );

        return;
    }

    if (
        button?.dataset.completing ===
        "true"
    ) {
        return;
    }

    if (button) {

        button.dataset.completing =
            "true";

        button.disabled = true;

        button.textContent =
            "Checking...";
    }

    try {

        const data =
            await apiRequest(
                `/tasks/${taskId}/complete`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        init_data:
                            tg.initData
                    })
                }
            );

        if (!data.success) {

            if (button) {

                button.textContent =
                    "Completed ✓";

                button.dataset.completed =
                    "true";

                button.dataset.completing =
                    "false";
            }

            alert(
                data.message ||
                "Task already completed."
            );

            return;
        }

        balance =
            Number(
                data.balance || 0
            );

        updateUI();

        if (button) {

            button.textContent =
                "Completed ✓";

            button.disabled = true;

            button.dataset.completed =
                "true";

            button.dataset.completing =
                "false";
        }

        alert(
            `+${data.reward} W2E earned!`
        );

    } catch (error) {

        console.error(
            "Task completion error:",
            error
        );

        if (button) {

            button.disabled = false;

            button.dataset.completing =
                "false";

            button.textContent =
                "Start";
        }

        alert(
            error.message ||
            "Unable to complete task."
        );
    }
}


// ============================================================
// WATCH AD
// ============================================================

async function watchAd() {

    if (!tg || !tg.initData) {

        alert(
            "Please open Watch2Earn from Telegram."
        );

        return;
    }

    try {

        const data =
            await apiRequest(
                "/watch-ad",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        init_data:
                            tg.initData
                    })
                }
            );

        if (!data.success) {

            if (
                data.remaining_seconds
            ) {

                alert(
                    `Please wait ${data.remaining_seconds} seconds.`
                );

            } else {

                alert(
                    data.message ||
                    "Ad reward failed."
                );
            }

            return;
        }

        balance =
            Number(
                data.balance || 0
            );

        adsWatched =
            Number(
                data.ads_watched || 0
            );

        updateUI();

        alert(
            `+${data.reward} W2E earned!`
        );

    } catch (error) {

        console.error(
            "Watch ad error:",
            error
        );

        alert(
            error.message ||
            "Unable to give ad reward."
        );
    }
}


// ============================================================
// DAILY BONUS
// ============================================================

async function dailyBonus() {

    if (!tg || !tg.initData) {

        alert(
            "Please open Watch2Earn from Telegram."
        );

        return;
    }

    const button =
        document.getElementById(
            "bonusBtn"
        );

    if (
        button &&
        button.dataset.loading === "true"
    ) {
        return;
    }

    if (button) {

        button.dataset.loading =
            "true";

        button.disabled = true;

        button.textContent =
            "Checking...";
    }

    try {

        const data =
            await apiRequest(
                "/daily-bonus",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        init_data:
                            tg.initData
                    })
                }
            );

        if (!data.success) {

            alert(
                `Daily bonus already claimed.\n\n` +
                `Try again in ` +
                `${data.remaining_hours || 0}h ` +
                `${data.remaining_minutes || 0}m.`
            );

            if (button) {

                button.textContent =
                    "Claimed";

                button.disabled = true;

                button.dataset.loading =
                    "false";
            }

            return;
        }

        balance =
            Number(
                data.balance || 0
            );

        updateUI();

        if (button) {

            button.textContent =
                "Claimed ✓";

            button.disabled = true;

            button.dataset.loading =
                "false";
        }

        const dailyStatus =
            document.getElementById(
                "dailyStatus"
            );

        if (dailyStatus) {
            dailyStatus.textContent =
                "Claimed";
        }

        alert(
            `+${data.reward} W2E earned!`
        );

    } catch (error) {

        console.error(
            "Daily bonus error:",
            error
        );

        if (button) {

            button.disabled = false;

            button.textContent =
                "Claim";

            button.dataset.loading =
                "false";
        }

        alert(
            error.message ||
            "Unable to claim bonus."
        );
    }
}


// ============================================================
// REFERRAL LINK
// ============================================================

function getReferralLink() {

    const user =
        tg?.initDataUnsafe?.user;

    if (!user) {

        alert(
            "Open the app from Telegram."
        );

        return null;
    }

    return (
        `https://t.me/Watch2EarnBot?start=${user.id}`
    );
}


// ============================================================
// COPY REFERRAL
// ============================================================

async function copyReferral() {

    const link =
        getReferralLink();

    if (!link) {
        return;
    }

    try {

        if (
            navigator.clipboard &&
            navigator.clipboard.writeText
        ) {

            await navigator.clipboard.writeText(
                link
            );

            alert(
                "Referral link copied!"
            );

        } else {

            window.prompt(
                "Copy your referral link:",
                link
            );
        }

    } catch (error) {

        console.error(
            "Clipboard error:",
            error
        );

        window.prompt(
            "Copy your referral link:",
            link
        );
    }
}


// ============================================================
// SHARE REFERRAL
// ============================================================

function shareReferral() {

    const link =
        getReferralLink();

    if (!link) {
        return;
    }

    const text =
        "Join Watch2Earn and start earning W2E!";

    const shareUrl =
        "https://t.me/share/url?" +
        "url=" +
        encodeURIComponent(link) +
        "&text=" +
        encodeURIComponent(text);

    if (
        tg &&
        typeof tg.openTelegramLink ===
        "function"
    ) {

        tg.openTelegramLink(
            shareUrl
        );

    } else {

        window.open(
            shareUrl,
            "_blank"
        );
    }
}


// ============================================================
// LOAD REFERRAL STATS
// ============================================================

async function loadReferralStats() {

    const user =
        tg?.initDataUnsafe?.user;

    if (!user) {
        return;
    }

    try {

        const data =
            await apiRequest(
                `/referrals/${user.id}`
            );

        referrals =
            Number(
                data.referrals || 0
            );

        updateUI();

    } catch (error) {

        console.error(
            "Referral loading error:",
            error
        );
    }
}


// ============================================================
// REFERRAL UI
// ============================================================

function loadReferralUI() {

    const link =
        getReferralLink();

    const linkElement =
        document.getElementById(
            "referralLink"
        );

    if (
        linkElement &&
        link
    ) {

        linkElement.value =
            link;
    }
}


// ============================================================
// TON WALLET
// ============================================================

function connectWallet() {

    const walletInput =
        document.getElementById(
            "walletAddress"
        );

    if (walletInput) {

        walletInput.focus();

    } else {

        alert(
            "Wallet input not found."
        );
    }
}


// ============================================================
// GAMES
// ============================================================

function startGame() {

    alert(
        "Tap Challenge\n\n" +
        "Mini game integration will be added next."
    );
}


function luckyBox() {

    alert(
        "Lucky Box\n\n" +
        "Game reward system will be added next."
    );
}


// ============================================================
// LEADERBOARD
// ============================================================

async function loadLeaderboard() {

    const container =
        document.getElementById(
            "leaderboardContainer"
        );

    if (!container) {
        return;
    }

    container.innerHTML =
        "<p>Loading leaderboard...</p>";

    try {

        const data =
            await apiRequest(
                "/leaderboard?limit=20"
            );

        if (
            !data ||
            !data.success ||
            !Array.isArray(
                data.leaderboard
            )
        ) {

            container.innerHTML =
                "<p>No leaderboard data.</p>";

            return;
        }

        if (
            data.leaderboard.length === 0
        ) {

            container.innerHTML =
                "<p>No users yet.</p>";

            return;
        }

        container.innerHTML = "";

        data.leaderboard.forEach(
            user => {

                const row =
                    document.createElement(
                        "div"
                    );

                row.className =
                    "leaderboard-row";

                const displayName =
                    user.username
                        ? `@${user.username}`
                        : (
                            user.first_name ||
                            "User"
                        );

                const name =
                    escapeHTML(
                        displayName
                    );

                row.innerHTML = `
                    <div class="leader-rank">
                        #${Number(user.rank || 0)}
                    </div>

                    <div class="leader-user">
                        ${name}
                    </div>

                    <div class="leader-balance">
                        ${Number(
                            user.balance || 0
                        )} W2E
                    </div>
                `;

                container.appendChild(
                    row
                );
            }
        );

    } catch (error) {

        console.error(
            "Leaderboard error:",
            error
        );

        container.innerHTML =
            "<p>Unable to load leaderboard.</p>";
    }
}


// ============================================================
// LOAD WALLET
// ============================================================

async function loadWallet() {

    if (!tg || !tg.initData) {
        return;
    }

    try {

        const url =
            `${API_URL}/wallet?init_data=${
                encodeURIComponent(
                    tg.initData
                )
            }`;

        const response =
            await fetch(
                url,
                {
                    method: "GET",

                    headers: {
                        "Accept":
                            "application/json"
                    }
                }
            );

        const data =
            await response.json();

        if (!response.ok) {

            console.error(
                "Wallet API error:",
                data
            );

            return;
        }

        const walletInput =
            document.getElementById(
                "walletAddress"
            );

        const walletStatus =
            document.getElementById(
                "walletStatus"
            );

        if (walletInput) {

            walletInput.value =
                data.wallet_address || "";
        }

        if (walletStatus) {

            walletStatus.textContent =
                data.wallet_address
                    ? "Wallet connected"
                    : "No wallet connected";
        }

    } catch (error) {

        console.error(
            "Wallet loading error:",
            error
        );
    }
}


// ============================================================
// SAVE WALLET
// ============================================================

async function saveWallet() {

    if (!tg || !tg.initData) {

        alert(
            "Please open Watch2Earn from Telegram."
        );

        return;
    }

    const input =
        document.getElementById(
            "walletAddress"
        );

    if (!input) {

        alert(
            "Wallet input not found."
        );

        return;
    }

    const walletAddress =
        input.value.trim();

    if (!walletAddress) {

        alert(
            "Enter your TON wallet address."
        );

        return;
    }

    try {

        const data =
            await apiRequest(
                "/wallet",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        init_data:
                            tg.initData,

                        wallet_address:
                            walletAddress
                    })
                }
            );

        const walletStatus =
            document.getElementById(
                "walletStatus"
            );

        if (walletStatus) {

            walletStatus.textContent =
                "Wallet connected ✓";
        }

        alert(
            "TON wallet saved successfully!"
        );

    } catch (error) {

        console.error(
            "Wallet error:",
            error
        );

        alert(
            error.message ||
            "Unable to save wallet."
        );
    }
}


// ============================================================
// REMOVE WALLET
// ============================================================

async function removeWallet() {

    if (!tg || !tg.initData) {

        alert(
            "Please open Watch2Earn from Telegram."
        );

        return;
    }

    try {

        await apiRequest(
            "/wallet",
            {
                method: "DELETE",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    init_data:
                        tg.initData
                })
            }
        );

        const input =
            document.getElementById(
                "walletAddress"
            );

        const status =
            document.getElementById(
                "walletStatus"
            );

        if (input) {
            input.value = "";
        }

        if (status) {

            status.textContent =
                "No wallet connected";
        }

        alert(
            "Wallet removed."
        );

    } catch (error) {

        console.error(
            "Wallet remove error:",
            error
        );

        alert(
            error.message ||
            "Unable to remove wallet."
        );
    }
}


// ============================================================
// PAGE NAVIGATION
// ============================================================

function showPage(pageId) {

    document
        .querySelectorAll(".page")
        .forEach(
            page => {

                page.classList.remove(
                    "active"
                );
            }
        );

    const selectedPage =
        document.getElementById(
            pageId
        );

    if (selectedPage) {

        selectedPage.classList.add(
            "active"
        );
    }

    document
        .querySelectorAll(".nav-btn")
        .forEach(
            btn => {

                btn.classList.remove(
                    "active"
                );
            }
        );

    const pages = [
        "home",
        "tasks",
        "games",
        "leaderboard",
        "wallet",
        "profile",
        "referral"
    ];

    const buttons =
        document.querySelectorAll(
            ".nav-btn"
        );

    const index =
        pages.indexOf(pageId);

    if (
        index !== -1 &&
        buttons[index]
    ) {

        buttons[index].classList.add(
            "active"
        );
    }

    if (pageId === "tasks") {
        loadTasks();
    }

    if (pageId === "leaderboard") {
        loadLeaderboard();
    }

    if (pageId === "wallet") {
        loadWallet();
    }

    if (pageId === "referral") {

        loadReferralStats();
        loadReferralUI();
    }
}


// ============================================================
// START APP
// ============================================================

async function startApp() {

    updateUI();

    const authenticated =
        await authenticateUser();

    if (authenticated) {

        await loadReferralStats();

        loadReferralUI();

        await loadTasks();

        await loadLeaderboard();

        await loadWallet();

    } else {

        await loadTasks();

        await loadLeaderboard();
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


// ============================================================
// RUN
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {
        startApp();
    }
);
```
