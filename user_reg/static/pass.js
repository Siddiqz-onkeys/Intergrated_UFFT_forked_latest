const passwordInput = document.getElementById("password");
const passwordForm = document.getElementById("passwordForm");
const togglePassword=document.getElementById("togglePassword")
const requirementsList = document.getElementById("requirements");

togglePassword.addEventListener('click',()=>{
    const isPassword=passwordInput.type ==='password';
    passwordInput.type=isPassword ? 'text' : 'password';
    togglePassword.innerHTML = `<i class="far fa-eye${isPassword ?'' : '-slash'}"></i>`;
})

// Show the requirements list when the password field is focused
passwordInput.addEventListener("focus", () => {
    requirementsList.classList.add("show");
});

// Hide the requirements list when clicking outside or switching to another field
document.addEventListener("click", (event) => {
    const isPasswordField = passwordInput.contains(event.target);
    const isRequirementsList = requirementsList.contains(event.target);

    // Hide if the click is outside both the password field and requirements list
    if (!isPasswordField && !isRequirementsList) {
        requirementsList.classList.remove("show");
    }
});

// Optional: Remove the list on blur for smoother transitions
passwordInput.addEventListener("blur", () => {
    setTimeout(() => requirementsList.classList.remove("show"), 100); // Small delay to prevent abrupt hiding
});


const updateValidation = (reqElement, isValid) => {
    if (!reqElement) {
        console.error("Missing element:", reqElement);
        return;
    }
    const iconElement = reqElement.querySelector("i");
    if (!iconElement) {
        console.error("Icon not found in", reqElement);
        return;
    }
    
    if (isValid) {
        iconElement.classList.remove("fa-xmark");
        iconElement.classList.add("fa-check");
        reqElement.style.color = "#16423C";
    } else {
        iconElement.classList.remove("fa-check");
        iconElement.classList.add("fa-xmark");
        reqElement.style.color = "";
    }
};

passwordForm.addEventListener("input", () => {
    console.log("Password input changed:", passwordInput.value);

    const password = passwordInput.value;
    
    updateValidation(document.getElementById("length"), password.length >= 8);
    updateValidation(document.getElementById("uppercase"), /[A-Z]/.test(password));
    updateValidation(document.getElementById("lowercase"), /[a-z]/.test(password));
    updateValidation(document.getElementById("number"), /\d/.test(password));
    updateValidation(document.getElementById("special"), /[!@#$%&*]/.test(password));

})


document.getElementById('d').addEventListener('focus', function() {
    this.type = 'date';
});





