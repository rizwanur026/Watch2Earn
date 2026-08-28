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

    document.getElementById(
        "balance"
    ).textContent = balance;


    document.getElementById(
        "adsWatched"
    ).textContent = adsWatched;


    document.getElementById(
        "refCount"
    ).textContent = referrals;


    document.getElementById(
        "leaderBalance"
    ).textContent = balance;


    document.getElementById(
        "profileCoins"
    ).textContent = balance;


    document.getElementById(
        "profileAds"
    ).textContent = adsWatched;


    document.getElementById(
        "profileRefs"
    ).textContent = referrals;

}


// ===============================
// Telegram Authentication
// ===============================

async function authenticateUser() {

    if (!tg) {

        console.log(
            "Telegram WebApp not detected"
        );

        setGuestProfile();

        return;

    }


    const initData =
        tg.initData;


    if (!initData) {

        console.log(
            "Telegram initData not available"
        );

        setGuestProfile();

        return;

    }


    try {

        const response =
            await fetch(
                `${API_URL}/auth`,
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body: JSON.stringify({

                        init_data:
                            initData

                    })

                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Authentication failed"
            );

        }


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

                <h3>
                    Loading Tasks...
                </h3>

                <p>
                    Please wait
                </p>

            </div>

        </div>

    `;


    try {

        const response =
            await fetch(
                `${API_URL}/tasks`
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Failed to load tasks"
            );

        }


        if (
            !data.tasks ||
            data.tasks.length === 0
        ) {

            container.innerHTML = `

                <div class="task">

                    <div class="task-info">

                        <h3>
                            No tasks available
                        </h3>

                        <p>
                            New tasks will appear here.
                        </p>

                    </div>

                </div>

            `;

            return;

        }


        container.innerHTML = "";


        data.tasks.forEach(
            task => {

                const taskElement =
                    document.createElement(
                        "div"
                    );


                taskElement.className =
                    "task";


                taskElement.innerHTML = `

                    <div class="task-icon">
                        ${getTaskIcon(task.task_type)}
                    </div>

                    <div class="task-info">

                        <h3>
                            ${escapeHTML(task.title)}
                        </h3>

                        <p>
                            ${escapeHTML(
                                task.description || ""
                            )}
                        </p>

                        <p>
                            +${task.reward} W2E
                        </p>

                    </div>

                    <button
                        onclick="startTask(
                            ${task.id},
                            '${escapeAttribute(task.link || "")}'
                        )"
                    >
                        Start
                    </button>

                `;


                container.appendChild(
                    taskElement
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

                    <h3>
                        Unable to load tasks
                    </h3>

                    <p>
                        Please try again later.
                    </p>

                </div>

            </div>

        `;

    }

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
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}


function escapeAttribute(value) {

    return String(value)
        .replaceAll("\\", "\\\\")
        .replaceAll("'", "\\'")
        .replaceAll("\n", "");

}


// ===============================
// Start Task
// ===============================

function startTask(
    taskId,
    link
) {

    if (!link) {

        alert(
            "This task does not have a link."
        );

        return;

    }


    if (
        tg &&
        tg.openLink
    ) {

        tg.openLink(link);

    } else {

        window.open(
            link,
            "_blank"
        );

    }


    console.log(
        "Started task:",
        taskId
    );

}


// ===============================
// Watch Ad
// ===============================

function watchAd() {

    alert(
        "Demo Ad\n\n" +
        "Real advertisement integration " +
        "will be added later."
    );

}


// ===============================
// Daily Bonus
// ===============================

async function dailyBonus() {

    if (
        !tg ||
        !tg.initData
    ) {

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
        !button ||
        button.disabled
    ) {

        return;

    }


    button.disabled = true;

    button.textContent =
        "Checking...";


    try {

        const response =
            await fetch(
                `${API_URL}/daily-bonus`,
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


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Something went wrong"
            );

        }


        if (!data.success) {

            alert(
                `Daily bonus already claimed.\n\n` +
                `Try again in ` +
                `${data.remaining_hours}h ` +
                `${data.remaining_minutes}m.`
            );


            button.textContent =
                "Claimed";


            return;

        }


        balance =
            Number(
                data.balance
            );


        updateUI();


        button.textContent =
            "Claimed";


        alert(
            `🎁 +${data.reward} W2E earned!`
        );


    } catch (error) {

        console.error(
            "Daily bonus error:",
            error
        );


        alert(
            "Unable to claim bonus. " +
            "Please try again."
        );


        button.disabled =
            false;


        button.textContent =
            "Claim";

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


    navigator.clipboard
        .writeText(link)
        .then(() => {

            alert(
                "Referral link copied!"
            );

        })
        .catch(() => {

            alert(
                "Unable to copy referral link."
            );

        });

}


// ===============================
// TON Wallet
// ===============================

function connectWallet() {

    document.getElementById(
        "walletStatus"
    ).textContent =
        "TON Wallet integration coming next.";


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
// Page Navigation
// ===============================

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

}


// ===============================
// Start App
// ===============================

updateUI();

authenticateUser();

loadTasks();
