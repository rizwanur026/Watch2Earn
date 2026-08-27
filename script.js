// ===============================
// Watch2Earn Backend
// ===============================

const API_URL = "https://watch2earn-lp3w.onrender.com/";

async function authenticateUser() {

    if (!window.Telegram?.WebApp) {
        console.log("Telegram WebApp not detected");
        return;
    }

    const tg = window.Telegram.WebApp;

    tg.ready();
    tg.expand();

    const initData = tg.initData;

    if (!initData) {
        console.log("Telegram initData not available");
        return;
    }

    try {

        const response = await fetch(`${API_URL}/auth`, {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                init_data: initData
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Authentication failed");
        }

        console.log("Authenticated:", data);

        if (data.user) {

            balance = data.user.balance || 0;
            adsWatched = data.user.ads_watched || 0;
            referrals = data.user.referrals || 0;

            updateUI();

            const user = tg.initDataUnsafe?.user;

            if (user) {

                const fullName =
                    `${user.first_name || ""} ${user.last_name || ""}`.trim();

                document.querySelector(".header h1").textContent =
                    `Hi, ${user.first_name || "User"}!`;

                document.querySelector(".profile-card h2").textContent =
                    fullName || "User";

                document.querySelector(".profile-card p").textContent =
                    `Telegram ID: ${user.id}`;
            }
        }

    } catch (error) {

        console.error("Authentication error:", error);

    }
}

const tg = window.Telegram.WebApp;

tg.ready();
tg.expand();

const user = tg.initDataUnsafe?.user;

if (user) {
    document.querySelector(".header h1").textContent =
        "Hi, " + (user.first_name || "User") + "!";

    document.querySelector(".profile-card h2").textContent =
        (user.first_name || "") + " " + (user.last_name || "");

    document.querySelector(".profile-card p").textContent =
        "Telegram ID: " + user.id;

    console.log("Telegram User:", user);
} else {
    document.querySelector(".header h1").textContent =
        "Hi, Guest!";

    document.querySelector(".profile-card h2").textContent =
        "Guest";

    document.querySelector(".profile-card p").textContent =
        "Open this app from Telegram";
}

let balance = Number(localStorage.getItem("balance")) || 0;
let adsWatched = Number(localStorage.getItem("adsWatched")) || 0;
let referrals = Number(localStorage.getItem("referrals")) || 0;

function saveData() {
    localStorage.setItem("balance", balance);
    localStorage.setItem("adsWatched", adsWatched);
    localStorage.setItem("referrals", referrals);
}

function updateUI() {

    document.getElementById("balance").textContent = balance;

    document.getElementById("adsWatched").textContent = adsWatched;

    document.getElementById("refCount").textContent = referrals;

    document.getElementById("leaderBalance").textContent = balance;

    document.getElementById("profileCoins").textContent = balance;

    document.getElementById("profileAds").textContent = adsWatched;

    document.getElementById("profileRefs").textContent = referrals;
}


function watchAd() {

    const reward = 50;

    alert("Demo Ad\n\nIn the real version an advertisement will appear here.");

    balance += reward;

    adsWatched++;

    saveData();

    updateUI();

    alert("+" + reward + " W2E earned!");
}


function dailyBonus() {

    const lastClaim = localStorage.getItem("dailyBonus");

    const today = new Date().toDateString();

    if (lastClaim === today) {

        alert("Daily bonus already claimed.");

        return;
    }

    const reward = 250;

    balance += reward;

    localStorage.setItem("dailyBonus", today);

    saveData();

    updateUI();

    document.getElementById("bonusBtn").textContent = "Claimed";

    document.getElementById("dailyStatus").textContent = "Claimed";

    alert("Daily Bonus +" + reward + " W2E");
}


function completeTask(button, reward) {

    if (button.dataset.completed === "true") {

        alert("Task already completed.");

        return;
    }

    button.textContent = "Done";

    button.dataset.completed = "true";

    balance += reward;

    saveData();

    updateUI();

    alert("Task completed!\n+" + reward + " W2E");
}


function startGame() {

    let taps = 0;

    const game = confirm(
        "Tap Challenge\n\nPress OK to start!"
    );

    if (!game) return;

    for (let i = 0; i < 10; i++) {

        taps++;

    }

    const reward = 100;

    balance += reward;

    saveData();

    updateUI();

    alert(
        "Game completed!\n\n" +
        "Score: " + taps +
        "\nReward: +" + reward + " W2E"
    );
}


function luckyBox() {

    const rewards = [10, 25, 50, 100, 200];

    const reward =
        rewards[Math.floor(Math.random() * rewards.length)];

    balance += reward;

    saveData();

    updateUI();

    alert("Lucky Box!\n\nYou won +" + reward + " W2E");
}


function copyReferral() {

    const link =
        "https://t.me/Watch2EarnBot?start=USER000001";

    navigator.clipboard.writeText(link);

    alert("Referral link copied!");
}


function connectWallet() {

    document.getElementById("walletStatus").textContent =
        "Wallet connection will be added in the next version.";

    alert(
        "TON Wallet integration coming next!"
    );
}


function showPage(pageId) {

    document.querySelectorAll(".page").forEach(page => {

        page.classList.remove("active");

    });

    document.getElementById(pageId).classList.add("active");


    document.querySelectorAll(".nav-btn").forEach(btn => {

        btn.classList.remove("active");

    });


    const buttons = document.querySelectorAll(".nav-btn");

    const pages = [
        "home",
        "tasks",
        "games",
        "leaderboard",
        "wallet"
    ];

    const index = pages.indexOf(pageId);

    if (index !== -1) {

        buttons[index].classList.add("active");

    }

}


updateUI();
