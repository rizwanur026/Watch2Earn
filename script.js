```javascript
// ===============================
// Watch2Earn Frontend
// ===============================

const API_URL = "https://watch2earn-lp3w.onrender.com";

let balance = 0;
let adsWatched = 0;
let referrals = 0;


// ===============================
// Telegram WebApp
// ===============================

const tg = window.Telegram?.WebApp;

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

    Object.entries(elements).forEach(([id, value]) => {

        const element = document.getElementById(id);

        if (element) {
            element.textContent = value;
        }

    });
}


// ===============================
// Telegram Authentication
// ===============================

async function authenticateUser() {

    if (!tg || !tg.initData) {

        console.log("Telegram WebApp not detected.");

        setGuestProfile();

        return;
    }

    try {

        const response = await fetch(`${API_URL}/auth`, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                init_data: tg.initData
            })

        });


        const data = await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail || "Authentication failed"
            );

        }


        console.log("Authenticated:", data);


        if (data.user) {

            balance = Number(
                data.user.balance || 0
            );

            adsWatched = Number(
                data.user.ads_watched || 0
            );

            referrals = Number(
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

    const user = tg?.initDataUnsafe?.user;


    if (!user) {

        setGuestProfile();

        return;

    }


    const fullName =
        `${user.first_name || ""} ${user.last_name || ""}`.trim();


    const headerTitle =
        document.querySelector(".header h1");


    const profileName =
        document.querySelector(".profile-card h2");


    const profileInfo =
        document.querySelector(".profile-card p");


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
        document.querySelector(".header h1");


    const profileName =
        document.querySelector(".profile-card h2");


    const profileInfo =
        document.querySelector(".profile-card p");


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
        document.getElementById("tasksContainer");


    if (!container) {

        console.warn(
            "tasksContainer not found."
        );

        return;

    }


    // Loading state

    container.innerHTML = `

        <div class="task">

            <div class="task-info">

                <h3>Loading Tasks...</h3>

                <p>Please wait...</p>

            </div>

        </div>

    `;


    try {

        const response =
            await fetch(`${API_URL}/tasks`, {

                method: "GET",

                headers: {
                    "Accept": "application/json"
                }

            });


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Failed to load tasks"
            );

        }


        console.log(
            "Tasks received:",
            data.tasks
        );


        // No tasks

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


        // Clear old tasks

        container.innerHTML = "";


        // Render every task from API

        data.tasks.forEach(task => {

            const taskElement =
                document.createElement("div");


            taskElement.className =
                "task";


            const taskId =
                Number(task.id);


            const title =
                escapeHTML(
                    task.title || "Untitled Task"
                );


            const description =
                escapeHTML(
                    task.description || "Complete this task"
                );


            const reward =
                Number(task.reward || 0);


            const taskType =
                escapeHTML(
                    task.task_type || "website"
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
                            link
                        );

                    }
                );

            }


            container.appendChild(
                taskElement
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


// ===============================
// Start Task
// ===============================

function startTask(taskId, link) {

    if (!link) {

        alert(
            "This task does not have a link."
        );

        return;

    }


    console.log(
        "Starting task:",
        taskId
    );


    if (tg && tg.openLink) {

        tg.openLink(link);

    } else {

        window.open(
            link,
            "_blank"
        );

    }

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

    if (!tg || !tg.initData) {

        alert(
            "Please open Watch2Earn from Telegram."
        );

        return;

    }


    const button =
        document.getElementById("bonusBtn");


    if (!button || button.disabled) {

        return;

    }


    button.disabled = true;

    button.textContent = "Checking...";


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
            Number(data.balance || 0);


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


        button.disabled = false;

        button.textContent = "Claim";

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
                    "Unable to copy referral link."
                );

            });

    } else {

        alert(link);

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
        pages.indexOf(pageId);


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
```
