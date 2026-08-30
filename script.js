// ===============================
// Watch2Earn Frontend
// ===============================

const API_URL =
    "https://watch2earn-lp3w.onrender.com";


let balance = 0;
let adsWatched = 0;
let referrals = 0;


// ===============================
// Telegram WebApp
// ===============================

const tg =
    window.Telegram?.WebApp;


if (tg) {

    tg.ready();

    tg.expand();

}


// ===============================
// Update UI
// ===============================

function updateUI() {

    const elements = {

        balance: balance,

        adsWatched: adsWatched,

        refCount: referrals,

        leaderBalance: balance,

        profileCoins: balance,

        profileAds: adsWatched,

        profileRefs: referrals

    };


    Object.entries(elements)
        .forEach(([id, value]) => {

            const element =
                document.getElementById(id);

            if (element) {

                element.textContent = value;

            }

        });

}


// ===============================
// API Helper
// ===============================

async function apiRequest(
    endpoint,
    options = {}
) {

    const response =
        await fetch(
            `${API_URL}${endpoint}`,
            options
        );


    let data;

    try {

        data =
            await response.json();

    } catch {

        throw new Error(
            "Invalid server response"
        );

    }


    if (!response.ok) {

        throw new Error(
            data.detail ||
            "Request failed"
        );

    }


    return data;

}


// ===============================
// Telegram Authentication
// ===============================

async function authenticateUser() {

    if (!tg || !tg.initData) {

        console.log(
            "Telegram WebApp not detected."
        );

        setGuestProfile();

        return;

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


        console.log(
            "Authenticated:",
            data
        );


        if (data.user) {

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

        }


    } catch (error) {

        console.error(
            "Authentication error:",
            error
        );

        setGuestProfile();

    }

}


// ===============================
// Telegram Profile
// ===============================

function setTelegramProfile() {

    const user =
        tg?.initDataUnsafe?.user;


    if (!user) {

        setGuestProfile();

        return;

    }


    const fullName =
        `${user.first_name || ""} ${user.last_name || ""}`
            .trim();


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

}


// ===============================
// Guest Profile
// ===============================

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


// ===============================
// Load Tasks
// ===============================

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
            !data.success ||
            !Array.isArray(data.tasks) ||
            data.tasks.length === 0
        ) {

            container.innerHTML = `

                <div class="task">

                    <div class="task-info">

                        <h3>No tasks available</h3>

                        <p>
                            New tasks will appear here.
                        </p>

                    </div>

                </div>

            `;

            return;

        }


        container.innerHTML = "";


        data.tasks.forEach(task => {

            renderTask(
                container,
                task
            );

        });


    } catch (error) {

        console.error(
            "Task loading error:",
            error
        );


        container.innerHTML = `

            <div class="task">

                <div class="task-info">

                    <h3>
                        Unable to load tasks
                    </h3>

                    <p>
                        Please try again later.
                    </p>

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


// ===============================
// Render Task
// ===============================

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
        Number(
            task.reward || 0
        );


    const taskType =
        escapeHTML(
            task.task_type ||
            "website"
        );


    const link =
        String(
            task.link || ""
        );


    taskElement.innerHTML = `

        <div class="task-icon">
            ${getTaskIcon(taskType)}
        </div>

        <div class="task-info">

            <h3>
                ${title}
            </h3>

            <p>
                ${description}
            </p>

            <p>
                +${reward} W2E
            </p>

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


// ===============================
// Task Icon
// ===============================

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


// ===============================
// HTML Security
// ===============================

function escapeHTML(value) {

    return String(value)

        .replaceAll(
            "&",
            "&amp;"
        )

        .replaceAll(
            "<",
            "&lt;"
        )

        .replaceAll(
            ">",
            "&gt;"
        )

        .replaceAll(
            '"',
            "&quot;"
        )

        .replaceAll(
            "'",
            "&#039;"
        );

}


// ===============================
// Start Task
// ===============================

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
        button?.dataset.completed === "true"
    ) {

        return;

    }


    if (button) {

        button.disabled = true;

        button.textContent =
            "Opening...";

    }


    try {

        if (tg.openLink) {

            tg.openLink(link);

        } else {

            window.open(
                link,
                "_blank"
            );

        }


        const completed =
            confirm(
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


// ===============================
// Complete Task
// ===============================

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
        button?.dataset.completing === "true"
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

        }


        alert(
            `🎉 +${data.reward} W2E earned!`
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


// ===============================
// Watch Ad
// ===============================

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

            alert(
                data.message ||
                "Ad reward failed."
            );

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


// ===============================
// Daily Bonus
// ===============================

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
        button.disabled
    ) {

        return;

    }


    if (button) {

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
                `${data.remaining_hours}h ` +
                `${data.remaining_minutes}m.`
            );


            if (button) {

                button.textContent =
                    "Claimed";

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
                "Claimed";

        }


        alert(
            `🎁 +${data.reward} W2E earned!`
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

        }


        alert(
            error.message ||
            "Unable to claim bonus."
        );

    }

}


// ===============================
// Referral
// ===============================

function copyReferral() {

    const user =
        tg?.initDataUnsafe?.user;


    if (!user) {

        alert(
            "Open the app from Telegram."
        );

        return;

    }


    const link =
        `https://t.me/Watch2EarnBot?start=${user.id}`;


    if (
        navigator.clipboard &&
        navigator.clipboard.writeText
    ) {

        navigator.clipboard
            .writeText(link)
            .then(() => {

                alert(
                    "Referral link copied!"
                );

            })
            .catch(() => {

                alert(
                    link
                );

            });

    } else {

        alert(link);

    }

}


// ===============================
// Load Referral Stats
// ===============================

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


// ===============================
// TON Wallet
// ===============================

function connectWallet() {

    const walletStatus =
        document.getElementById(
            "walletStatus"
        );


    if (walletStatus) {

        walletStatus.textContent =
            "TON Wallet integration coming next.";

    }


    alert(
        "TON Wallet integration coming next!"
    );

}


// ===============================
// Games
// ===============================

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


// ===============================
// Leaderboard
// ===============================

async function loadLeaderboard() {

    try {

        const data =
            await apiRequest(
                "/leaderboard"
            );


        if (
            !data.success ||
            !Array.isArray(
                data.leaderboard
            )
        ) {

            return;

        }


        const container =
            document.getElementById(
                "leaderboardContainer"
            );


        if (!container) {

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
                    "leaderboard-item";


                row.innerHTML = `

                    <span>
                        #${user.rank}
                    </span>

                    <span>
                        ${escapeHTML(
                            user.username
                        )}
                    </span>

                    <span>
                        ${Number(
                            user.balance || 0
                        )} W2E
                    </span>

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

    }

}


// ===============================
// Page Navigation
// ===============================

function showPage(pageId) {

    document
        .querySelectorAll(".page")
        .forEach(page => {

            page.classList.remove(
                "active"
            );

        });


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
        .forEach(btn => {

            btn.classList.remove(
                "active"
            );

        });


    const pages = [

        "home",
        "tasks",
        "games",
        "leaderboard",
        "wallet",
        "profile"

    ];


    const buttons =
        document.querySelectorAll(
            ".nav-btn"
        );


    const index =
        pages.indexOf(
            pageId
        );


    if (
        index !== -1 &&
        buttons[index]
    ) {

        buttons[index].classList.add(
            "active"
        );

    }


    if (
        pageId === "leaderboard"
    ) {

        loadLeaderboard();

    }

}


// ===============================
// Start App
// ===============================

async function startApp() {

    updateUI();

    await authenticateUser();

    await loadReferralStats();

    await loadTasks();

    await loadLeaderboard();

}


startApp();

// ===============================
// Referral Info
// ===============================

async function loadReferralInfo() {

    if (!tg || !tg.initDataUnsafe?.user) {
        return;
    }

    const telegramId =
        tg.initDataUnsafe.user.id;

    try {

        const response = await fetch(
            `${API_URL}/referrals/${telegramId}`
        );

        const data = await response.json();

        if (!response.ok) {
            return;
        }

        referrals =
            Number(data.referrals || 0);

        updateUI();

        const refElement =
            document.getElementById("referralCount");

        if (refElement) {
            refElement.textContent =
                referrals;
        }

    } catch (error) {

        console.error(
            "Referral loading error:",
            error
        );

    }

}


// ===============================
// Generate Referral Link
// ===============================

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


// ===============================
// Copy Referral Link
// ===============================

async function copyReferral() {

    const link =
        getReferralLink();

    if (!link) {
        return;
    }

    try {

        await navigator.clipboard.writeText(
            link
        );

        alert(
            "Referral link copied!"
        );

    } catch (error) {

        alert(link);

    }

}


// ===============================
// Share Referral
// ===============================

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

    if (tg?.openTelegramLink) {

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


// ===============================
// Leaderboard
// ===============================

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

        const response =
            await fetch(
                `${API_URL}/leaderboard?limit=20`
            );

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Leaderboard failed"
            );

        }

        if (
            !data.success ||
            !Array.isArray(data.leaderboard)
        ) {

            container.innerHTML =
                "<p>No leaderboard data.</p>";

            return;
        }

        if (data.leaderboard.length === 0) {

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

                const name =
                    escapeHTML(
                        user.username
                            ? `@${user.username}`
                            : (
                                user.first_name ||
                                "User"
                            )
                    );

                row.innerHTML = `
                    <div class="leader-rank">
                        #${user.rank}
                    </div>

                    <div class="leader-user">
                        ${name}
                    </div>

                    <div class="leader-balance">
                        ${Number(user.balance || 0)} W2E
                    </div>
                `;

                container.appendChild(row);

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


// ===============================
// Wallet
// ===============================

async function loadWallet() {

    if (!tg || !tg.initData) {
        return;
    }

    try {

        const response =
            await fetch(
                `${API_URL}/wallet`,
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

            if (data.wallet_address) {

                walletStatus.textContent =
                    "Wallet connected";

            } else {

                walletStatus.textContent =
                    "No wallet connected";

            }

        }

    } catch (error) {

        console.error(
            "Wallet loading error:",
            error
        );

    }

}


// ===============================
// Save TON Wallet
// ===============================

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

        const response =
            await fetch(
                `${API_URL}/wallet`,
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

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Unable to save wallet"
            );

        }

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


// ===============================
// Remove TON Wallet
// ===============================

async function removeWallet() {

    if (!tg || !tg.initData) {

        alert(
            "Please open Watch2Earn from Telegram."
        );

        return;

    }

    try {

        const response =
            await fetch(
                `${API_URL}/wallet`,
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

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Unable to remove wallet"
            );

        }

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


// ===============================
// Load New Features
// ===============================

loadReferralInfo();
loadLeaderboard();
loadWallet();
