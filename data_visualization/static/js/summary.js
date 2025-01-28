// Utility function for smooth showing of results
function displayResult(elementId, content, alertClass = "alert-info") {
  const element = document.getElementById(elementId);
  element.className = `mt-4 alert ${alertClass}`;
  element.innerHTML = content;
  element.style.display = "block";
}

// Generate Summary button logic
document
  .getElementById("generate-summary-btn")
  .addEventListener("click", function () {
    fetch("/data_visualization/generate_summary", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.summary) {
          displayResult(
            "summary-result",
            `<strong>Summary:</strong><br>${data.summary.replace(
              /\n/g,
              "<br>"
            )}`
          );

          // Show the Brief Summary button
          document
            .getElementById("brief-summary-section")
            .classList.remove("d-none");
        } else {
          displayResult(
            "summary-result",
            `<strong>Error:</strong> ${data.error}`,
            "alert-danger"
          );
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        displayResult(
          "summary-result",
          `<strong>Error generating summary.</strong>`,
          "alert-danger"
        );
      });
  });

// Generate Brief Summary button logic
document
  .getElementById("generate-brief-summary-btn")
  .addEventListener("click", function () {
    fetch("/data_visualization/generate_brief_summary", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.brief_summary) {
          displayResult(
            "brief-summary-result",
            `<strong>Brief Summary:</strong><br>${data.brief_summary.replace(
              /\n/g,
              "<br>"
            )}`,
            "alert-secondary"
          );
        } else {
          displayResult(
            "brief-summary-result",
            `<strong>Error:</strong> ${data.error}`,
            "alert-danger"
          );
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        displayResult(
          "brief-summary-result",
          `<strong>Error generating brief summary.</strong>`,
          "alert-danger"
        );
      });
  });
