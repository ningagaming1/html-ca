document.addEventListener('DOMContentLoaded', () => {
  // 1. Initialize Feedback Cards (Only runs on pages with #feedback-track)
  loadFeedbackCards();

  // 2. Initialize Login Form (Only runs on pages with #login-form)
  initLoginForm();

  // 3. Initialize Signup Form (Only runs on pages with #signup-form)
  // initSignupForm();
});


async function loadFeedbackCards() {
  const track = document.querySelector('#feedback-track');

  if (!track) return; // Guard clause in case element isn't on page

  try {
    // Fetch data from FastAPI backend
    const response = await fetch('/api/feedback');

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const feedbackList = await response.json();

    // Clear the "Loading member feedback..." text
    track.innerHTML = '';

    // Function to construct individual card HTML
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

    // Build card HTML and duplicate once for continuous CSS loop
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

async function initLoginForm() {
  //alert("initLoginForm is running");
  const loginform = document.querySelector("#login-form")
  if (!loginform) return;

  loginform.addEventListener("submit",async (e)=>{
    e.preventDefault();

    const username = document.querySelector("#username").value;
    const password = document.querySelector("#password").value;

    console.log(username)
    try {
      const response = await fetch("/api/login",{
        method : "POST",
        headers : {"Content-Type": "application/json"},
        body : JSON.stringify({username,password})
      });

      const result = await response.json();
      if (response.ok) {
        alert(result.message || "Login Successful!")
      }
      else {
        alert(result.message || "Wrong")
      }
    }
    catch (err) {
      console.error("login request failed",err);
      alert("unable to conect to server")
    }
  })
}