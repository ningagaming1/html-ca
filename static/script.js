document.addEventListener('DOMContentLoaded', () => {
  // 1. Initialize Feedback Cards (Only runs on pages with #feedback-track)
  loadFeedbackCards();

  // 2. Initialize Login Form (Runs on pages with #login-form or #auth-form)
  initLoginForm();
});

async function loadFeedbackCards() {
  const track = document.querySelector('#feedback-track');
  if (!track) return;

  try {
    const response = await fetch('/api/feedback');
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const feedbackList = await response.json();
    track.innerHTML = '';

    const createCardHTML = (item) => {
      const ratingClass = item.rating >= 4 ? 'rating-high' : 'rating-low';
      return `
        <div class="feedback-card">
            <div class="card-header">
                <div class="card-author">
                    <h4>${item.memberName}</h4>
                    <span>Trainer: ${item.trainer}</span>
                </div>
                <span class="rating ${ratingClass}">${item.rating} ★</span>
            </div>
            <p class="card-body">"${item.comments}"</p>
            <div class="card-footer">
                <span>Tag: ${item.category}</span>
                <span>${item.date}</span>
            </div>
        </div>
      `;
    };

    let cardsHTML = '';
    for (const item of feedbackList) {
      cardsHTML += createCardHTML(item);
    }

    track.innerHTML = cardsHTML + cardsHTML;
  } catch (err) {
    console.error('Failed to load feedback cards:', err);
    track.innerHTML = '<p style="color: red;">Unable to load feedback.</p>';
  }
}

async function validateForm(e) {
  if (e && e.preventDefault) e.preventDefault();

  const emailInput = document.querySelector("#email") || document.querySelector("#username");
  const passwordInput = document.querySelector("#password");

  if (!emailInput || !passwordInput) return false;

  const email = emailInput.value.trim();
  const password = passwordInput.value;

  try {
    const response = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: email, username: email, password: password })
    });

    const result = await response.json();
    if (response.ok) {
      const targetUrl = result.redirect_url || "/member-dashboard.html";
      window.location.href = targetUrl;
      return true;
    } else {
      alert(result.detail || result.message || "Invalid credentials.");
      return false;
    }
  } catch (err) {
    console.error("Login request failed", err);
    alert("Unable to connect to Titans server.");
    return false;
  }
}

function initLoginForm() {
  const loginform = document.querySelector("#login-form") || document.querySelector("#auth-form");
  if (!loginform) return;

  loginform.addEventListener("submit", validateForm);
}

// Global signup handler for signup.html
async function handleSignup(e) {
  if (e && e.preventDefault) e.preventDefault();

  const usernameEl = document.getElementById('username');
  const emailEl = document.getElementById('email');
  const passwordEl = document.getElementById('password');
  const confirmPasswordEl = document.getElementById('confirm-password');
  const termsEl = document.getElementById('terms');
  const errorMsg = document.getElementById('password-match-error');

  const username = usernameEl ? usernameEl.value.trim() : "";
  const email = emailEl ? emailEl.value.trim() : "";
  const password = passwordEl ? passwordEl.value : "";
  const confirmPassword = confirmPasswordEl ? confirmPasswordEl.value : "";
  const terms = termsEl ? termsEl.checked : true;

  if (password !== confirmPassword) {
    if (errorMsg) errorMsg.style.display = 'block';
    if (confirmPasswordEl) confirmPasswordEl.focus();
    return false;
  }

  if (!terms) {
    alert('Please accept the Terms and Conditions to proceed.');
    return false;
  }

  if (errorMsg) errorMsg.style.display = 'none';

  try {
    const res = await fetch("/api/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: username,
        email: email,
        password: password,
        role: "member"
      })
    });

    const data = await res.json();
    if (res.ok) {
      alert("Welcome to Titans Fitness Studio! Your account has been created.");
      window.location.href = data.redirect_url || "/login.html";
      return true;
    } else {
      alert(data.detail || "Signup failed. Please try a different username/email.");
      return false;
    }
  } catch (err) {
    console.error("Signup error:", err);
    alert("Network error creating account.");
    return false;
  }
}