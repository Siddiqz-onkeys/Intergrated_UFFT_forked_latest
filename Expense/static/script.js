var id=0;
var amount=0;
var major;
function showEditMenu(expense_id,expense_amount){
    document.getElementById('edit_menu').style.display='block';

    // expense id is globalized to share it to other functions as well

    id=expense_id;
    amount=expense_amount;
    document.getElementById("exp_id_edit").textContent=id;
    document.getElementById('return_amount').textContent=amount;
}

// function edit_expense(){
    
//     document.getElementById('edit_expense').style.display="block";
//     document.getElementById('add_amount_form').style.display="none";
//     const form = document.getElementById('edit_expense');
//     form.action = `/edit_expense/${id}`;
  
    
// }

function edit_expense() {
  // Show the edit expense form
  const editForm = document.getElementById("edit_expense");
  editForm.style.display = "block";

  // Hide the add amount form
  const addAmountForm = document.getElementById("add_amount_form");
  if (addAmountForm) {
    addAmountForm.style.display = "none";
  }

  // Dynamically update the form action URL
  if (editForm) {
    const blueprintPrefix = "/expense"; // Adjust if your blueprint URL prefix is different
    editForm.action = `${blueprintPrefix}/edit_expense/${id}`;
  }
}


function add_amount(){
    document.getElementById('add_amount_form').style.display="block";
    document.getElementById('edit_expense').style.display="none";
    const form = document.getElementById('add_amount_form');
    //form.action = `/add_amount/${id}`;
    form.action = `/expense/add_amount/${id}`;
    
}

function close_menu(){
    document.getElementById('add_amount_form').style.display='none';
    document.getElementById('edit_menu').style.display='none';
    
}

let originalOrder = []; // Stores the default order of rows.

function sortTable(columnIndex, header) {
    const table = document.querySelector("table tbody");
    const rows = Array.from(table.rows);

    // Save original order only once
    if (originalOrder.length === 0) {
        originalOrder = rows.map(row => row.cloneNode(true));
    }

    // Get current sort order from the header
    const currentOrder = header.getAttribute("data-sort-order");
    let newOrder;

    if (currentOrder === "none" || currentOrder === "desc") {
        // Sort in ascending order
        newOrder = rows.sort((rowA, rowB) => {
            const cellA = rowA.cells[columnIndex].innerText.trim();
            const cellB = rowB.cells[columnIndex].innerText.trim();
            return isNaN(cellA) ? cellA.localeCompare(cellB) : parseFloat(cellA) - parseFloat(cellB);
        });
        header.setAttribute("data-sort-order", "asc");
    } else if (currentOrder === "asc") {
        // Sort in descending order
        newOrder = rows.sort((rowA, rowB) => {
            const cellA = rowA.cells[columnIndex].innerText.trim();
            const cellB = rowB.cells[columnIndex].innerText.trim();
            return isNaN(cellA) ? cellB.localeCompare(cellA) : parseFloat(cellB) - parseFloat(cellA);
        });
        header.setAttribute("data-sort-order", "desc");
    } else {
        // Restore to default order
        newOrder = originalOrder;
        header.setAttribute("data-sort-order", "none");
    }

    // Clear the table and append the sorted rows
    table.innerHTML = "";
    newOrder.forEach(row => table.appendChild(row));

    // Reset other headers' sort order
    document.querySelectorAll("thead th").forEach(th => {
        if (th !== header) {
            th.setAttribute("data-sort-order", "none");
        }
    });
}
let del_id = 0;

function verify_age(user_id, expense_id) {
  fetch(`/expense/verify_major/${user_id}`) // Adjusted URL with /expense prefix
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json(); // Parse the JSON response
    })
    .then((data) => {
      const ageMessage = document.getElementById("ageMessage");
      const deleteConfirmationSection = document.getElementById(
        "deleteConfirmationSection"
      );
      if (data.is_major) {
        deleteConfirmationSection.style.display = "block"; // Show confirmation dialog
        del_id = expense_id; // Set global variable
      } else {
        ageMessage.style.display = "block";
        ageMessage.style.animation = "none"; // Reset animation
        void ageMessage.offsetWidth; // Trigger reflow
        ageMessage.style.animation = "showHide 1.5s ease-in-out";
      }
    })
    .catch((error) => console.error("Error:", error));
}

function deletion(event) {
  event.preventDefault(); // Prevent default form submission

  const form = document.getElementById("deleteConfirmationSection");
  form.action = `/expense/delete_expense/${del_id}`; // Adjusted URL with /expense prefix

  const deleteMessage = document.getElementById("deleteMessage");
  deleteMessage.style.display = "block";
  deleteMessage.style.animation = "none"; // Reset animation
  void deleteMessage.offsetWidth; // Trigger reflow
  deleteMessage.style.animation = "showHide 1.5s ease-in-out";

  // Optionally, delay the actual submission to allow the animation to play
  setTimeout(() => {
    form.submit(); // Submit the form after the animation
  }, -3500); // Adjust delay to match animation duration
}


function close_delete(){
    document.getElementById('deleteConfirmationSection').style.display='none';
}