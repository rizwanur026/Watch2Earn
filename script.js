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
// UI Update
// ===============================

function updateUI() {

    document.getElementById("balance").textContent = balance;

    document.getElementById("adsWatched").textContent = adsWatched;

    document.getElementById("refCount").textContent = referrals;

    document.getElementById("leaderBalance").textContent = balance;

    document.getElementById("profileCoins").textContent = balance;

    document.getElementById("profileAds").textContent = adsWatched;

    document.getElementById("profileRefs").textContent = referrals;
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


    const initData = tg.initData;

    if (!initData) {

        console.log(
            "Telegram initData not available"
        );

        setGuestProfile();

        return;
    }


    try {

        const response = await fetch(
            `${API_URL}/auth`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    init_data: initData
                })
            }
        );


        const data = await response.json();


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

        alert(
            "Unable to connect to Watch2Earn server."
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


    console.log(
        "Telegram User:",
        user
    );
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
        document.getElementById(
            "bonusBtn"
        );


    if (!button) {
        return;
    }


    if (button.disabled) {
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


        // Already claimed
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


        // Server balance
        balance =
            Number(data.balance);


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
// Tasks
// ===============================

function completeTask(
    button,
    reward
) {

    alert(
        "Task system is being connected " +
        "to the server."
    );
}


// ===============================
// Tap Challenge
// ===============================

function startGame() {

    alert(
        "Tap Challenge\n\n" +
        "Mini game backend integration " +
        "will be added next."
    );
}


// ===============================
// Lucky Box
// ===============================

function luckyBox() {

    alert(
        "Lucky Box\n\n" +
        "Game reward system will be " +
        "connected to the server."
    );
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


    const telegramId =
        user.id;


    const link =
        `https://t.me/Watch2EarnBot?start=${telegramId}`;


    navigator.clipboard.writeText(link)
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
